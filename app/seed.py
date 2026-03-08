from app.database import SessionLocal, engine, Base
from app.models import Track, Verse

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if db.query(Track).count() == 0:
    evangelho = Track(
        title="Evangelho",
        description="Versículos essenciais sobre salvação, graça e fé."
    )
    vida_crista = Track(
        title="Vida Cristã",
        description="Versículos para discipulado, santificação e crescimento."
    )
    oracao = Track(
        title="Oração",
        description="Versículos para confiança, súplica e comunhão com Deus."
    )

    db.add_all([evangelho, vida_crista, oracao])
    db.commit()
    db.refresh(evangelho)
    db.refresh(vida_crista)
    db.refresh(oracao)

    verses = [
        Verse(
            reference="João 3:16",
            text="Porque Deus amou ao mundo de tal maneira que deu o seu Filho unigênito, para que todo o que nele crê não pereça, mas tenha a vida eterna.",
            order=1,
            track_id=evangelho.id
        ),
        Verse(
            reference="Romanos 3:23",
            text="Pois todos pecaram e carecem da glória de Deus.",
            order=2,
            track_id=evangelho.id
        ),
        Verse(
            reference="Efésios 2:8-9",
            text="Porque pela graça sois salvos, mediante a fé; e isto não vem de vós; é dom de Deus; não de obras, para que ninguém se glorie.",
            order=3,
            track_id=evangelho.id
        ),
        Verse(
            reference="Romanos 12:2",
            text="E não vos conformeis com este século, mas transformai-vos pela renovação da vossa mente.",
            order=1,
            track_id=vida_crista.id
        ),
        Verse(
            reference="Gálatas 2:20",
            text="Logo, já não sou eu quem vive, mas Cristo vive em mim.",
            order=2,
            track_id=vida_crista.id
        ),
        Verse(
            reference="Colossenses 3:16",
            text="Habite, ricamente, em vós a palavra de Cristo.",
            order=3,
            track_id=vida_crista.id
        ),
        Verse(
            reference="Filipenses 4:6-7",
            text="Não andeis ansiosos de coisa alguma; em tudo, porém, sejam conhecidas, diante de Deus, as vossas petições.",
            order=1,
            track_id=oracao.id
        ),
        Verse(
            reference="1 João 5:14",
            text="E esta é a confiança que temos para com ele: que, se pedirmos alguma coisa segundo a sua vontade, ele nos ouve.",
            order=2,
            track_id=oracao.id
        ),
        Verse(
            reference="Mateus 6:33",
            text="Buscai, pois, em primeiro lugar, o seu reino e a sua justiça, e todas estas coisas vos serão acrescentadas.",
            order=3,
            track_id=oracao.id
        ),
    ]

    db.add_all(verses)
    db.commit()

db.close()
print("Banco populado com sucesso.")