from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    verses = relationship("Verse", back_populates="track")


class Verse(Base):
    __tablename__ = "verses"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"))

    track = relationship("Track", back_populates="verses")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class UserVerseProgress(Base):
    __tablename__ = "user_verse_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    verse_id = Column(Integer, ForeignKey("verses.id"), nullable=False)
    memorized = Column(Boolean, default=False)
    review_stage = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)


class CustomTrack(Base):
    __tablename__ = "custom_tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    verses = relationship(
        "CustomTrackVerse",
        back_populates="custom_track",
        cascade="all, delete-orphan"
    )


class CustomTrackVerse(Base):
    __tablename__ = "custom_track_verses"

    id = Column(Integer, primary_key=True, index=True)
    custom_track_id = Column(Integer, ForeignKey("custom_tracks.id"), nullable=False)
    verse_id = Column(Integer, ForeignKey("verses.id"), nullable=False)
    order_index = Column(Integer, default=0)

    custom_track = relationship("CustomTrack", back_populates="verses")
    verse = relationship("Verse")