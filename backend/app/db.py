"""Database: SQLite by default, any SQLAlchemy URL via DATABASE_URL."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterator, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.config import DATA_DIR, DATABASE_URL

DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Diagnosis(Base):
    """One completed check: what the rider entered and what the engine answered."""

    __tablename__ = "diagnoses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    bike_name: Mapped[Optional[str]] = mapped_column(String(80))
    overall: Mapped[str] = mapped_column(String(16))
    answers: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)

    feedback: Mapped[Optional["Feedback"]] = relationship(
        back_populates="diagnosis", cascade="all, delete-orphan", uselist=False
    )


class Feedback(Base):
    """What a mechanic actually found. These rows are the training data for the symptom model."""

    __tablename__ = "feedback"

    diagnosis_id: Mapped[str] = mapped_column(ForeignKey("diagnoses.id", ondelete="CASCADE"), primary_key=True)
    confirmed_fault: Mapped[str] = mapped_column(String(40))   # a fault id, "other" or "none"
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    diagnosis: Mapped[Diagnosis] = relationship(back_populates="feedback")


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
