from datetime import datetime, timedelta
from collections import Counter

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import Base, engine, get_db
from app.models import Track, Verse, User, UserVerseProgress

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="memolab-chave-secreta-mvp")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


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


def get_next_review_date(review_stage: int) -> datetime:
    now = datetime.utcnow()

    intervals = {
        1: 1,
        2: 3,
        3: 7,
        4: 14,
        5: 30,
        6: 90,
    }

    days = intervals.get(review_stage, 120)
    return now + timedelta(days=days)


def apply_correct_review(progress):
    current_stage = progress.review_stage or 0
    new_stage = current_stage + 1

    progress.memorized = True
    progress.review_stage = new_stage
    progress.last_reviewed_at = datetime.utcnow()
    progress.next_review_date = get_next_review_date(new_stage)


def apply_wrong_review(progress):
    current_stage = progress.review_stage or 1

    if current_stage <= 2:
        new_stage = 1
    else:
        new_stage = current_stage - 2

    progress.memorized = False if new_stage == 1 else True
    progress.review_stage = new_stage
    progress.last_reviewed_at = datetime.utcnow()
    progress.next_review_date = get_next_review_date(new_stage)


def build_heatmap_data(progresses, days=90):
    counts = Counter()

    for p in progresses:
        if p.last_reviewed_at is not None:
            day_key = p.last_reviewed_at.date().isoformat()
            counts[day_key] += 1

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
        progresso = sum(1 for p in progresses if p.memorized is True)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "titulo": "MemoLab",
            "versiculo": versiculo,
            "progresso": progresso,
            "tracks": tracks,
            "current_user": current_user,
        },
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "register.html",
        {"request": request, "titulo": "Criar Conta", "erro": None},
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


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "titulo": "Entrar", "erro": None},
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


@app.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)

    tracks = sort_tracks(db.query(Track).all())
    total_verses = db.query(Verse).count()

    progresses = db.query(UserVerseProgress).filter(
        UserVerseProgress.user_id == user.id
    ).all()

    memorized_count = sum(1 for p in progresses if p.memorized is True)
    remaining_count = total_verses - memorized_count

    progress_map = {p.verse_id: p for p in progresses}

    now = datetime.utcnow()
    review_count = sum(
        1 for p in progresses
        if p.memorized is True and p.next_review_date is not None and p.next_review_date <= now
    )

    today = datetime.utcnow().date()

    done_today = sum(
        1 for p in progresses
        if p.last_reviewed_at is not None and p.last_reviewed_at.date() == today
    )

    heatmap_data = build_heatmap_data(progresses, days=90)

    track_stats = []
    for track in tracks:
        total_track_verses = len(track.verses)
        memorized_track_verses = sum(
            1 for verse in track.verses
            if verse.id in progress_map and progress_map[verse.id].memorized is True
        )

        percentage = 0
        if total_track_verses > 0:
            percentage = int((memorized_track_verses / total_track_verses) * 100)

        track_stats.append({
            "track": track,
            "total": total_track_verses,
            "memorized": memorized_track_verses,
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
            "Deus": [v for v in track.verses if ref_clean(v) in ["Atos 17:24-28", "Apocalipse 4:11"]],
            "Pecado": [v for v in track.verses if ref_clean(v) in ["Romanos 3:23", "Romanos 6:23"]],
            "Cristo": [v for v in track.verses if ref_clean(v) in ["João 3:16", "João 14:6"]],
            "Decisão": [v for v in track.verses if ref_clean(v) in ["João 1:12", "Romanos 10:9"]],
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
    