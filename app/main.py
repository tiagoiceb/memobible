from datetime import datetime, timedelta
from collections import Counter
from io import BytesIO
from pathlib import Path
import os

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import Base, engine, get_db
from app.models import (
    Track,
    Verse,
    User,
    UserVerseProgress,
    CustomTrack,
    CustomTrackVerse,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="MemoBible-chave-secreta-mvp"
)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None


# --------------------------------------------------
# AUTENTICAÇÃO
# --------------------------------------------------

def get_current_user(request: Request, db: Session):
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def require_user(request: Request, db: Session):
    user = get_current_user(request, db)

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")

    return user


# --------------------------------------------------
# UTILIDADES
# --------------------------------------------------

def sort_tracks(tracks):
    desired_order = [
        "Seteceb 1º 2026",
        "Evangelho",
        "Vida Cristã",
        "Oração",
        "Fé",
        "Palavra de Deus",
        "Santidade",
        "Sabedoria",
        "Esperança",
        "Evangelismo",
        "Discipulado",
    ]

    order_map = {title: index for index, title in enumerate(desired_order)}

    return sorted(
        tracks,
        key=lambda t: order_map.get(t.title, 999)
    )


def get_next_review_date(review_stage: int):
    intervals = {
        1: 1,
        2: 3,
        3: 7,
        4: 14,
        5: 30,
        6: 90,
    }

    days = intervals.get(review_stage, 120)

    return datetime.utcnow() + timedelta(days=days)


def apply_correct_review(progress):
    stage = progress.review_stage or 0
    new_stage = stage + 1

    progress.memorized = True
    progress.review_stage = new_stage
    progress.last_reviewed_at = datetime.utcnow()
    progress.next_review_date = get_next_review_date(new_stage)


def apply_wrong_review(progress):
    stage = progress.review_stage or 1

    if stage <= 2:
        new_stage = 1
    else:
        new_stage = stage - 2

    progress.memorized = False if new_stage == 1 else True
    progress.review_stage = new_stage
    progress.last_reviewed_at = datetime.utcnow()
    progress.next_review_date = get_next_review_date(new_stage)


def build_heatmap_data(progresses, days=90):
    counts = Counter()

    for p in progresses:
        if p.last_reviewed_at:
            key = p.last_reviewed_at.date().isoformat()
            counts[key] += 1

    result = []
    today = datetime.utcnow().date()

    for i in range(days):
        day = today - timedelta(days=(days - 1 - i))
        key = day.isoformat()

        result.append({
            "date": key,
            "count": counts.get(key, 0),
        })

    return result


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    tracks = sort_tracks(db.query(Track).all())
    current_user = get_current_user(request, db)

    versiculo = "Escondi a tua palavra no meu coração, para eu não pecar contra ti. — Salmo 119:11"
    progresso = 0

    if current_user:
        progresses = db.query(UserVerseProgress).filter(
            UserVerseProgress.user_id == current_user.id
        ).all()

        progresso = sum(1 for p in progresses if p.memorized)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "titulo": "MemoBible",
            "versiculo": versiculo,
            "progresso": progresso,
            "tracks": tracks,
            "current_user": current_user,
        },
    )


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)

    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
            "titulo": "Criar Conta",
            "erro": None,
        },
    )


@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "titulo": "Criar Conta",
                "erro": "Já existe um usuário com esse e-mail.",
            },
        )

    hashed_password = pwd_context.hash(password)

    user = User(name=name, email=email, password_hash=hashed_password)

    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id

    return RedirectResponse(url="/dashboard", status_code=303)


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)

    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "titulo": "Entrar",
            "erro": None,
        },
    )


@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

    if not user or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "titulo": "Entrar",
                "erro": "E-mail ou senha inválidos.",
            },
        )

    request.session["user_id"] = user.id

    return RedirectResponse(url="/dashboard", status_code=303)


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    tracks = sort_tracks(db.query(Track).all())
    total_verses = db.query(Verse).count()

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()

    memorized_count = sum(1 for p in progresses if p.memorized)
    remaining_count = total_verses - memorized_count

    progress_map = {p.verse_id: p for p in progresses}

    now = datetime.utcnow()

    review_count = sum(
        1 for p in progresses
        if p.memorized and p.next_review_date and p.next_review_date <= now
    )

    today = datetime.utcnow().date()

    done_today = sum(
        1 for p in progresses
        if p.last_reviewed_at and p.last_reviewed_at.date() == today
    )

    heatmap_data = build_heatmap_data(progresses, 90)

    track_stats = []

    for track in tracks:
        total_track = len(track.verses)

        memorized_track = sum(
            1 for verse in track.verses
            if verse.id in progress_map and progress_map[verse.id].memorized
        )

        percentage = int((memorized_track / total_track) * 100) if total_track else 0

        track_stats.append({
            "track": track,
            "total": total_track,
            "memorized": memorized_track,
            "percentage": percentage,
        })

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "titulo": "Minha Jornada",
            "user": user,
            "current_user": user,
            "total_verses": total_verses,
            "memorized_count": memorized_count,
            "remaining_count": remaining_count,
            "review_count": review_count,
            "done_today": done_today,
            "heatmap_data": heatmap_data,
            "track_stats": track_stats,
        },
    )


# --------------------------------------------------
# REVISÃO
# --------------------------------------------------

@app.get("/revisao", response_class=HTMLResponse)
def revisao_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    now = datetime.utcnow()

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id,
        UserVerseProgress.memorized == True
    ).all()

    verses_to_review = [
        p for p in progresses
        if p.next_review_date is not None and p.next_review_date <= now
    ]

    return templates.TemplateResponse(
        "review.html",
        {
            "request": request,
            "titulo": "Revisão Diária",
            "current_user": user,
            "review_progresses": verses_to_review,
            "review_count": len(verses_to_review),
        },
    )


@app.post("/revisao/{progress_id}/acertou")
def acertou_revisao(
    progress_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    progress = db.query(UserVerseProgress).filter(
        UserVerseProgress.id == progress_id,
        UserVerseProgress.user_id == user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Progresso não encontrado")

    apply_correct_review(progress)
    db.commit()

    return RedirectResponse(url="/revisao", status_code=303)


@app.post("/revisao/{progress_id}/errou")
def errou_revisao(
    progress_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    progress = db.query(UserVerseProgress).filter(
        UserVerseProgress.id == progress_id,
        UserVerseProgress.user_id == user.id
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail="Progresso não encontrado")

    apply_wrong_review(progress)
    db.commit()

    return RedirectResponse(url="/revisao", status_code=303)


# --------------------------------------------------
# PÁGINAS NOVAS
# --------------------------------------------------

@app.get("/audio", response_class=HTMLResponse)
def audio_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    verses = db.query(Verse).all()

    return templates.TemplateResponse(
        "audio.html",
        {
            "request": request,
            "titulo": "Áudio e Repetição",
            "current_user": user,
            "verses": verses,
        },
    )


@app.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    return templates.TemplateResponse(
        "quiz.html",
        {
            "request": request,
            "titulo": "Quizzes e Testes",
            "current_user": user,
        },
    )


@app.get("/resumos", response_class=HTMLResponse)
def resumos_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    return templates.TemplateResponse(
        "resumos.html",
        {
            "request": request,
            "titulo": "Mapas e Resumos",
            "current_user": user,
        },
    )


@app.get("/aplicacao", response_class=HTMLResponse)
def aplicacao_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    return templates.TemplateResponse(
        "aplicacao.html",
        {
            "request": request,
            "titulo": "Aplicação Prática",
            "current_user": user,
        },
    )


# --------------------------------------------------
# API TRACKS
# --------------------------------------------------

@app.get("/tracks")
def list_tracks(db: Session = Depends(get_db)):
    tracks = sort_tracks(db.query(Track).all())

    data = [
        {
            "id": track.id,
            "title": track.title,
            "description": track.description,
            "verses": [
                {
                    "id": verse.id,
                    "reference": verse.reference,
                    "text": verse.text,
                }
                for verse in track.verses
            ],
        }
        for track in tracks
    ]

    return JSONResponse(content=data, media_type="application/json; charset=utf-8")

# --------------------------------------------------
# MINHAS TRILHAS
# --------------------------------------------------

@app.get("/minhas-trilhas", response_class=HTMLResponse)
def minhas_trilhas(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    custom_tracks = db.query(CustomTrack).filter(
        CustomTrack.user_id == user.id
    ).all()

    return templates.TemplateResponse(
        "custom_tracks.html",
        {
            "request": request,
            "titulo": "Minhas Trilhas",
            "current_user": user,
            "custom_tracks": custom_tracks,
        },
    )


@app.get("/minhas-trilhas/nova", response_class=HTMLResponse)
def nova_trilha_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    verses = db.query(Verse).all()

    return templates.TemplateResponse(
        "custom_track_new.html",
        {
            "request": request,
            "titulo": "Nova Trilha",
            "current_user": user,
            "verses": verses,
        },
    )


@app.post("/minhas-trilhas/nova")
def criar_trilha_personalizada(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    verse_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    nova_trilha = CustomTrack(
        user_id=user.id,
        title=title,
        description=description,
    )

    db.add(nova_trilha)
    db.commit()
    db.refresh(nova_trilha)

    for index, verse_id in enumerate(verse_ids):
        item = CustomTrackVerse(
            custom_track_id=nova_trilha.id,
            verse_id=verse_id,
            order_index=index,
        )
        db.add(item)

    db.commit()

    return RedirectResponse(url="/minhas-trilhas", status_code=303)


@app.get("/minhas-trilhas/{track_id}", response_class=HTMLResponse)
def detalhe_trilha_personalizada(track_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    custom_track = db.query(CustomTrack).filter(
        CustomTrack.id == track_id,
        CustomTrack.user_id == user.id
    ).first()

    if not custom_track:
        raise HTTPException(status_code=404, detail="Trilha personalizada não encontrada")

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()
    progress_map = {p.verse_id: p for p in progresses}

    ordered_items = sorted(custom_track.verses, key=lambda x: x.order_index)

    return templates.TemplateResponse(
        "custom_track_detail.html",
        {
            "request": request,
            "titulo": custom_track.title,
            "current_user": user,
            "custom_track": custom_track,
            "track_verses": ordered_items,
            "progress_map": progress_map,
        },
    )
# --------------------------------------------------
# TRILHAS
# --------------------------------------------------

@app.get("/trilhas", response_class=HTMLResponse)
def trilhas_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    tracks = sort_tracks(db.query(Track).all())

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()

    progress_map = {p.verse_id: p for p in progresses}

    return templates.TemplateResponse(
        "tracks.html",
        {
            "request": request,
            "titulo": "Trilhas",
            "tracks": tracks,
            "progress_map": progress_map,
            "current_user": user,
        },
    )


@app.get("/trilha/{track_id}", response_class=HTMLResponse)
def trilha_detalhe(track_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Trilha não encontrada")

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()
    progress_map = {p.verse_id: p for p in progresses}

    grouped_verses = None

    if track.title == "Evangelismo":
        def ref_clean(v):
            return v.reference.strip()

        grouped_verses = {
            "Deus": [
                v for v in track.verses
                if ref_clean(v) in ["Atos 17:24-28", "Apocalipse 4:11"]
            ],
            "Pecado": [
                v for v in track.verses
                if ref_clean(v) in ["Romanos 3:23", "Romanos 6:23"]
            ],
            "Cristo": [
                v for v in track.verses
                if ref_clean(v) in ["João 3:16", "João 14:6"]
            ],
            "Decisão": [
                v for v in track.verses
                if ref_clean(v) in ["João 1:12", "Romanos 10:9"]
            ],
        }

    return templates.TemplateResponse(
        "track_detail.html",
        {
            "request": request,
            "titulo": track.title,
            "track": track,
            "progress_map": progress_map,
            "current_user": user,
            "grouped_verses": grouped_verses,
        },
    )


# --------------------------------------------------
# VERSÍCULO
# --------------------------------------------------

@app.get("/versiculo/{verse_id}", response_class=HTMLResponse)
def versiculo_detalhe(verse_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    verse = db.query(Verse).filter(Verse.id == verse_id).first()
    if not verse:
        raise HTTPException(status_code=404, detail="Versículo não encontrado")

    progress = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id,
        UserVerseProgress.verse_id == verse.id
    ).first()

    if not progress:
        progress = UserVerseProgress(
            user_id=user.id,
            verse_id=verse.id,
            memorized=False,
            review_stage=0
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return templates.TemplateResponse(
        "verse_detail.html",
        {
            "request": request,
            "titulo": verse.reference,
            "verse": verse,
            "progress": progress,
            "current_user": user,
        },
    )


@app.get("/versiculo/{verse_id}/audio")
def gerar_audio_versiculo(
    verse_id: int,
    request: Request,
    mode: str = "text_only",
    db: Session = Depends(get_db)
):
    user = require_user(request, db)

    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY não configurada")

    verse = db.query(Verse).filter(Verse.id == verse_id).first()
    if not verse:
        raise HTTPException(status_code=404, detail="Versículo não encontrado")

    if mode == "with_reference":
        texto = f"{verse.reference}. {verse.text}"
    else:
        texto = verse.text

    try:
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb",
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            text=texto,
        )

        audio_bytes = b"".join(audio_stream)

        if not audio_bytes:
            raise HTTPException(status_code=500, detail="A API retornou áudio vazio")

        return StreamingResponse(
            BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": f'inline; filename="verse_{verse_id}.mp3"'},
        )

    except Exception as e:
        print("ERRO ELEVENLABS:", repr(e))
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {str(e)}")


@app.post("/versiculo/{verse_id}/memorizar")
def marcar_memorizado(verse_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    verse = db.query(Verse).filter(Verse.id == verse_id).first()
    if not verse:
        raise HTTPException(status_code=404, detail="Versículo não encontrado")

    progress = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id,
        UserVerseProgress.verse_id == verse.id
    ).first()

    if not progress:
        progress = UserVerseProgress(
            user_id=user.id,
            verse_id=verse.id,
            memorized=True,
            review_stage=1,
            last_reviewed_at=datetime.utcnow(),
            next_review_date=get_next_review_date(1),
        )
        db.add(progress)
    else:
        progress.memorized = True
        progress.review_stage = 1
        progress.last_reviewed_at = datetime.utcnow()
        progress.next_review_date = get_next_review_date(1)

    db.commit()

    return RedirectResponse(url=f"/versiculo/{verse_id}", status_code=303)


# --------------------------------------------------
# MINHAS TRILHAS
# --------------------------------------------------

@app.get("/minhas-trilhas", response_class=HTMLResponse)
def minhas_trilhas(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    custom_tracks = db.query(CustomTrack).filter(
        CustomTrack.user_id == user.id
    ).all()

    return templates.TemplateResponse(
        "custom_tracks.html",
        {
            "request": request,
            "titulo": "Minhas Trilhas",
            "current_user": user,
            "custom_tracks": custom_tracks,
        },
    )


@app.get("/minhas-trilhas/nova", response_class=HTMLResponse)
def nova_trilha_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    verses = db.query(Verse).all()

    return templates.TemplateResponse(
        "custom_track_new.html",
        {
            "request": request,
            "titulo": "Nova Trilha",
            "current_user": user,
            "verses": verses,
        },
    )


@app.post("/minhas-trilhas/nova")
def criar_trilha_personalizada(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    verse_ids: list[int] = Form([]),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)

    nova_trilha = CustomTrack(
        user_id=user.id,
        title=title,
        description=description,
    )

    db.add(nova_trilha)
    db.commit()
    db.refresh(nova_trilha)

    for index, verse_id in enumerate(verse_ids):
        item = CustomTrackVerse(
            custom_track_id=nova_trilha.id,
            verse_id=verse_id,
            order_index=index,
        )
        db.add(item)

    db.commit()

    return RedirectResponse(url="/minhas-trilhas", status_code=303)


@app.get("/minhas-trilhas/{track_id}", response_class=HTMLResponse)
def detalhe_trilha_personalizada(track_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    custom_track = db.query(CustomTrack).filter(
        CustomTrack.id == track_id,
        CustomTrack.user_id == user.id
    ).first()

    if not custom_track:
        raise HTTPException(status_code=404, detail="Trilha personalizada não encontrada")

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()
    progress_map = {p.verse_id: p for p in progresses}

    ordered_items = sorted(custom_track.verses, key=lambda x: x.order_index)

    return templates.TemplateResponse(
        "custom_track_detail.html",
        {
            "request": request,
            "titulo": custom_track.title,
            "current_user": user,
            "custom_track": custom_track,
            "track_verses": ordered_items,
            "progress_map": progress_map,
        },
    )