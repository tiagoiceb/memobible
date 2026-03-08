from app.database import SessionLocal
from app.models import Track, Verse

db = SessionLocal()

track_title = "Seteceb 1º 2026"

track = db.query(Track).filter(Track.title == track_title).first()

if not track:
    track = Track(
        title=track_title,
        description="Plano semanal de memorização bíblica do 1º semestre de 2026, com foco em Provérbios."
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    print("Trilha criada.")
else:
    print("Trilha já existia. Atualizando versículos...")

# apaga os versículos antigos dessa trilha
db.query(Verse).filter(Verse.track_id == track.id).delete()
db.commit()

verses = [
    Verse(
        reference="01 a 07 de fevereiro · Provérbios 1:23",
        text="Deem ouvidos à minha repreensão; eis que derramarei o meu espírito sobre vocês e lhes darei a conhecer as minhas palavras.",
        order=1,
        track_id=track.id
    ),
    Verse(
        reference="08 a 14 de fevereiro · Provérbios 2:6",
        text="Porque o Senhor dá a sabedoria, e da sua boca vem o conhecimento e a inteligência.",
        order=2,
        track_id=track.id
    ),
    Verse(
        reference="15 a 21 de fevereiro · Provérbios 3:5",
        text="Confie no Senhor de todo o seu coração e não se apoie no seu próprio entendimento.",
        order=3,
        track_id=track.id
    ),
    Verse(
        reference="22 a 28 de fevereiro · Provérbios 3:6",
        text="Reconheça o Senhor em todos os seus caminhos, e ele endireitará as suas veredas.",
        order=4,
        track_id=track.id
    ),
    Verse(
        reference="01 a 07 de março · Provérbios 3:15",
        text="A sabedoria é mais preciosa do que as joias, e tudo o que você possa desejar não se compara com ela.",
        order=5,
        track_id=track.id
    ),
    Verse(
        reference="08 a 14 de março · Provérbios 4:18",
        text="Mas a vereda dos justos é como a luz do alvorecer, que vai brilhando mais e mais até ser dia claro.",
        order=6,
        track_id=track.id
    ),
    Verse(
        reference="15 a 21 de março · Provérbios 4:23",
        text="De tudo o que se deve guardar, guarde bem o seu coração, porque dele procedem as fontes da vida.",
        order=7,
        track_id=track.id
    ),
    Verse(
        reference="22 a 28 de março · Provérbios 5:7",
        text="E agora, meu filho, escute o que eu digo e não se desvie das palavras da minha boca.",
        order=8,
        track_id=track.id
    ),
    Verse(
        reference="29 de março a 04 de abril · Provérbios 6:6",
        text="Vá ter com a formiga, ó preguiçoso! Observe os caminhos dela e seja sábio.",
        order=9,
        track_id=track.id
    ),
    Verse(
        reference="05 a 11 de abril · Provérbios 7:24",
        text="Agora, meu filho, escute o que eu digo e dê atenção às palavras da minha boca.",
        order=10,
        track_id=track.id
    ),
    Verse(
        reference="12 a 18 de abril · Provérbios 8:14",
        text="Meu é o conselho e a verdadeira sabedoria; eu sou o Entendimento, minha é a fortaleza.",
        order=11,
        track_id=track.id
    ),
    Verse(
        reference="19 a 25 de abril · Provérbios 9:9",
        text="Dê instrução ao sábio, e ele se tornará mais sábio ainda; ensine o justo, e ele crescerá na prudência.",
        order=12,
        track_id=track.id
    ),
    Verse(
        reference="26 de abril a 02 de maio · Provérbios 10:21",
        text="As palavras dos justos alimentam muitos, mas os insensatos morrem por falta de juízo.",
        order=13,
        track_id=track.id
    ),
    Verse(
        reference="03 a 09 de maio · Provérbios 11:13",
        text="O mexeriqueiro revela os segredos, mas o fiel de espírito os encobre.",
        order=14,
        track_id=track.id
    ),
    Verse(
        reference="10 a 16 de maio · Provérbios 12:1",
        text="Quem ama a disciplina ama o conhecimento, mas o que odeia a repreensão é tolo.",
        order=15,
        track_id=track.id
    ),
    Verse(
        reference="17 a 23 de maio · Provérbios 13:9",
        text="A luz dos justos brilha intensamente, mas a lâmpada dos ímpios se apagará.",
        order=16,
        track_id=track.id
    ),
    Verse(
        reference="24 a 30 de maio · Provérbios 13:13",
        text="Quem despreza a palavra terá de pagar por isso, mas o que teme o mandamento será recompensado.",
        order=17,
        track_id=track.id
    ),
    Verse(
        reference="31 de maio a 04 de junho · Provérbios 14:12",
        text="Há caminho que ao ser humano parece direito, mas o fim dele é caminho de morte.",
        order=18,
        track_id=track.id
    ),
    Verse(
        reference="07 a 13 de junho · Provérbios 15:1",
        text="A resposta branda desvia o furor, mas a palavra dura suscita a ira.",
        order=19,
        track_id=track.id
    ),
    Verse(
        reference="14 a 20 de junho · Provérbios 15:3",
        text="Os olhos do Senhor estão em todo lugar, contemplando os maus e os bons.",
        order=20,
        track_id=track.id
    ),
    Verse(
        reference="21 a 27 de junho · Provérbios 15:28",
        text="O coração do justo medita o que há de responder, mas a boca dos ímpios derrama maldades.",
        order=21,
        track_id=track.id
    ),
    Verse(
        reference="28 de junho a 04 de julho · Provérbios 16:32",
        text="É melhor ter paciência do que ser herói de guerra; o que domina o seu espírito é melhor do que o que conquista uma cidade.",
        order=22,
        track_id=track.id
    ),
]

db.add_all(verses)
db.commit()
db.close()

print(f"Trilha '{track_title}' atualizada com {len(verses)} versículos.")