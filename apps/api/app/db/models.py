from datetime import datetime
from sqlalchemy import String, Text, DateTime, Float, Integer, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

try:
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(384)
except Exception:  # local test fallback; production image installs pgvector
    VECTOR_TYPE = JSON


class Base(DeclarativeBase):
    pass


class SourceDocument(Base):
    __tablename__ = "legal_documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    canonical_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    authority: Mapped[str] = mapped_column(String(200))
    authority_level: Mapped[str] = mapped_column(String(30), default="tier_1")
    jurisdiction: Mapped[str] = mapped_column(String(50), index=True)
    document_type: Mapped[str] = mapped_column(String(100))
    access_level: Mapped[str] = mapped_column(String(30), default="PUBLIC")
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LegalVersion(Base):
    __tablename__ = "legal_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(200), index=True)
    version: Mapped[str] = mapped_column(String(100))
    effective_from: Mapped[datetime | None] = mapped_column(DateTime)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="current")
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    content_hash: Mapped[str | None] = mapped_column(String(64))


class LegalProvision(Base):
    __tablename__ = "legal_provisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chunk_id: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    source_id: Mapped[str] = mapped_column(String(200), index=True)
    document_title: Mapped[str] = mapped_column(Text)
    authority: Mapped[str] = mapped_column(String(200))
    authority_level: Mapped[str] = mapped_column(String(30), default="tier_1")
    jurisdiction: Mapped[str] = mapped_column(String(50), index=True)
    regime: Mapped[str] = mapped_column(String(100), index=True)
    instrument: Mapped[str] = mapped_column(Text)
    section: Mapped[str | None] = mapped_column(String(100), index=True)
    subsection: Mapped[str | None] = mapped_column(String(100))
    article: Mapped[str | None] = mapped_column(String(100))
    chapter: Mapped[str | None] = mapped_column(String(100))
    paragraph: Mapped[str | None] = mapped_column(String(100))
    page: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(20), default="en")
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime)
    version: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="current", index=True)
    citation: Mapped[str] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(String(30), default="PUBLIC")
    source_url: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR_TYPE)
    demo_only: Mapped[bool] = mapped_column(default=False)


Index("ix_provision_jurisdiction_status", LegalProvision.jurisdiction, LegalProvision.status)


class InnovationProfileRow(Base):
    __tablename__ = "innovation_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemoryRow(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    memory_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    memory_type: Mapped[str] = mapped_column(String(50), index=True)
    key: Mapped[str] = mapped_column(String(200), index=True)
    value: Mapped[dict] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(String(50), default="user")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(100), index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
