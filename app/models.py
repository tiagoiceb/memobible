from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    progresses = relationship("UserVerseProgress", back_populates="user")


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
    order = Column(Integer, default=1)
    track_id = Column(Integer, ForeignKey("tracks.id"))

    track = relationship("Track", back_populates="verses")
    progresses = relationship("UserVerseProgress", back_populates="verse")


class UserVerseProgress(Base):
    __tablename__ = "user_verse_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    verse_id = Column(Integer, ForeignKey("verses.id"))
    memorized = Column(Boolean, default=False)
    review_stage = Column(Integer, default=0)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="progresses")
    verse = relationship("Verse", back_populates="progresses")