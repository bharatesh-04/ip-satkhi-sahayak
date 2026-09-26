from uuid import uuid4
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.db.models import MemoryRow, InnovationProfileRow
from app.core.schemas import MemoryRecord, MemoryType, InnovationProfile


class MemoryManager:
    """Persistent user/innovation context; never authoritative legal evidence."""

    def __init__(self, db: Session):
        self.db = db

    def save(self, record: MemoryRecord) -> MemoryRecord:
        if not record.memory_id:
            record.memory_id = str(uuid4())
        existing = self.db.execute(select(MemoryRow).where(MemoryRow.memory_id == record.memory_id)).scalar_one_or_none()
        if existing:
            existing.value = record.value
            existing.confidence = record.confidence
            existing.expires_at = record.expires_at
        else:
            self.db.add(MemoryRow(
                memory_id=record.memory_id,
                user_id=record.user_id,
                memory_type=record.memory_type.value,
                key=record.key,
                value=record.value,
                source=record.source,
                confidence=record.confidence,
                expires_at=record.expires_at,
            ))
        self.db.commit()
        return record

    def relevant(self, user_id: str, keys: list[str] | None = None, limit: int = 10) -> list[MemoryRecord]:
        stmt = select(MemoryRow).where(MemoryRow.user_id == user_id).order_by(MemoryRow.updated_at.desc()).limit(limit)
        if keys:
            stmt = stmt.where(or_(*[MemoryRow.key.ilike(f"%{k}%") for k in keys]))
        rows = self.db.execute(stmt).scalars().all()
        now = datetime.utcnow()
        out = []
        for r in rows:
            if r.expires_at and r.expires_at < now:
                continue
            try:
                mt = MemoryType(r.memory_type)
            except ValueError:
                mt = MemoryType.semantic
            out.append(MemoryRecord(
                memory_id=r.memory_id, user_id=r.user_id, memory_type=mt,
                key=r.key, value=r.value, source=r.source,
                confidence=r.confidence, expires_at=r.expires_at,
            ))
        return out

    def save_profile(self, user_id: str, profile: InnovationProfile) -> str:
        profile_id = profile.profile_id or str(uuid4())
        profile.profile_id = profile_id
        existing = self.db.execute(select(InnovationProfileRow).where(InnovationProfileRow.profile_id == profile_id)).scalar_one_or_none()
        if existing:
            existing.data = profile.model_dump()
        else:
            self.db.add(InnovationProfileRow(profile_id=profile_id, user_id=user_id, data=profile.model_dump()))
        self.db.commit()
        return profile_id

    def latest_profile(self, user_id: str) -> InnovationProfile | None:
        row = self.db.execute(
            select(InnovationProfileRow)
            .where(InnovationProfileRow.user_id == user_id)
            .order_by(InnovationProfileRow.updated_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return InnovationProfile.model_validate(row.data) if row else None
