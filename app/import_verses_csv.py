import csv
from pathlib import Path

from app.database import SessionLocal
from app.models import Track, Verse


CSV_PATH = Path("data/verses_500.csv")


def get_or_create_track(db, title: str, description: str) -> Track:
    track = db.query(Track).filter(Track.title == title).first()
    if not track:
        track = Track(title=title, description=description)
        db.add(track)
        db.commit()
        db.refresh(track)
    else:
        # atualiza descrição se vier nova e diferente
        if description and track.description != description:
            track.description = description
            db.commit()
            db.refresh(track)
    return track


def verse_exists(db, track_id: int, reference: str) -> bool:
    existing = (
        db.query(Verse)
        .filter(Verse.track_id == track_id, Verse.reference == reference)
        .first()
    )
    return existing is not None


def main():
    if not CSV_PATH.exists():
        print(f"Arquivo não encontrado: {CSV_PATH}")
        return

    db = SessionLocal()
    inserted = 0
    skipped = 0

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        required = {"track_title", "track_description", "reference", "text", "order"}
        if not required.issubset(set(reader.fieldnames or [])):
            print("CSV inválido. Colunas obrigatórias:")
            print(", ".join(sorted(required)))
            db.close()
            return

        for row in reader:
            track_title = (row.get("track_title") or "").strip()
            track_description = (row.get("track_description") or "").strip()
            reference = (row.get("reference") or "").strip()
            text = (row.get("text") or "").strip()
            order_raw = (row.get("order") or "").strip()

            if not track_title or not reference or not text:
                skipped += 1
                continue

            try:
                order = int(order_raw) if order_raw else 1
            except ValueError:
                skipped += 1
                continue

            track = get_or_create_track(db, track_title, track_description)

            if verse_exists(db, track.id, reference):
                skipped += 1
                continue

            verse = Verse(
                reference=reference,
                text=text,
                order=order,
                track_id=track.id,
            )
            db.add(verse)
            inserted += 1

        db.commit()
        db.close()

    print(f"Importação concluída. Inseridos: {inserted}. Ignorados: {skipped}.")


if __name__ == "__main__":
    main()