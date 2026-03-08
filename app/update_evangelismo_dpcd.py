from app.database import SessionLocal
from app.models import Track, Verse

db = SessionLocal()

track_title = "Evangelismo"

track = db.query(Track).filter(Track.title == track_title).first()

if not track:
    track = Track(
        title=track_title,
        description="O evangelho em 4 pontos: Deus, Pecado, Cristo e Decisão."
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    print("Trilha criada.")
else:
    track.description = "O evangelho em 4 pontos: Deus, Pecado, Cristo e Decisão."
    db.commit()
    print("Trilha já existia. Atualizando versículos...")

db.query(Verse).filter(Verse.track_id == track.id).delete()
db.commit()

verses = [
    Verse(
        reference="Atos 17:24-28",
        text="O Deus que fez o mundo e tudo o que nele existe, sendo ele Senhor do céu e da terra, não habita em santuários feitos por mãos humanas. Nem é servido por mãos humanas, como se de alguma coisa precisasse; pois ele mesmo é quem a todos dá vida, respiração e tudo mais. De um só fez toda a raça humana para habitar sobre toda a face da terra, havendo fixado os tempos previamente estabelecidos e os limites da sua habitação; para buscarem a Deus se, porventura, tateando, o possam achar, bem que não está longe de cada um de nós; pois nele vivemos, e nos movemos, e existimos, como alguns dos vossos poetas têm dito: Porque dele também somos geração.",
        order=1,
        track_id=track.id
    ),
    Verse(
        reference="Apocalipse 4:11",
        text="Tu és digno, Senhor e Deus nosso, de receber a glória, a honra e o poder, porque todas as coisas tu criaste, sim, por causa da tua vontade vieram a existir e foram criadas.",
        order=2,
        track_id=track.id
    ),
    Verse(
        reference="Romanos 3:23",
        text="Pois todos pecaram e carecem da glória de Deus.",
        order=3,
        track_id=track.id
    ),
    Verse(
        reference="Romanos 6:23",
        text="Porque o salário do pecado é a morte, mas o dom gratuito de Deus é a vida eterna em Cristo Jesus, nosso Senhor.",
        order=4,
        track_id=track.id
    ),
    Verse(
        reference="João 3:16",
        text="Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito, para que todo o que nele crê não pereça, mas tenha a vida eterna.",
        order=5,
        track_id=track.id
    ),
    Verse(
        reference="João 14:6",
        text="Respondeu-lhe Jesus: Eu sou o caminho, e a verdade, e a vida; ninguém vem ao Pai senão por mim.",
        order=6,
        track_id=track.id
    ),
    Verse(
        reference="João 1:12",
        text="Mas, a todos quantos o receberam, deu-lhes o poder de serem feitos filhos de Deus, a saber, aos que creem no seu nome.",
        order=7,
        track_id=track.id
    ),
    Verse(
        reference="Romanos 10:9",
        text="Se, com a tua boca, confessares Jesus como Senhor e, em teu coração, creres que Deus o ressuscitou dentre os mortos, serás salvo.",
        order=8,
        track_id=track.id
    ),
]

db.add_all(verses)
db.commit()
db.close()

print("Trilha Evangelismo DPCD atualizada com 8 versículos.")