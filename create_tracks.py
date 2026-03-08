from app.database import SessionLocal
from app.models import Track

db = SessionLocal()

tracks = [
    ("Seteceb 1º 2026", "Plano semanal de memorização bíblica do SETECEB."),
    ("Evangelho", "Versículos essenciais sobre salvação, graça e fé."),
    ("Vida Cristã", "Versículos para discipulado, santificação e crescimento."),
    ("Oração", "Versículos para confiança, súplica e comunhão com Deus."),
    ("Fé", "Versículos sobre confiança em Deus."),
    ("Palavra de Deus", "Versículos sobre a Escritura."),
    ("Santidade", "Versículos sobre santificação e vida santa."),
    ("Sabedoria", "Versículos sobre sabedoria bíblica."),
    ("Esperança", "Versículos sobre esperança em Deus."),
    ("Evangelismo", "Versículos para compartilhar o evangelho."),
    ("Discipulado", "Versículos sobre seguir a Cristo."),
]

for title, description in tracks:
    existing = db.query(Track).filter(Track.title == title).first()
    if not existing:
        db.add(Track(title=title, description=description))
        print(f"Criada: {title}")
    else:
        existing.description = description
        print(f"Já existia: {title}")

db.commit()
db.close()

print("Trilhas oficiais consolidadas com sucesso.")