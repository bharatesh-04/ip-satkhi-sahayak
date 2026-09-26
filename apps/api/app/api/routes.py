from collections import defaultdict, deque
import time

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.core import config
from app.db.session import get_db
from app.db.init_db import init_db
from app.core.schemas import ConsultationRequest, MemoryRecord, InnovationProfile
from app.services.orchestrator import Orchestrator
from app.services.memory import MemoryManager

router = APIRouter(prefix="/api/v1")
rate_limits = defaultdict(deque)


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    settings = config.settings
    if not settings.require_api_key:
        return True
    if not settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API security is enabled but no API key is configured.",
        )
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing or invalid.",
        )
    return True


def enforce_rate_limit(client_id: str | None = Header(default="anonymous", alias="X-Client-Id")):
    settings = config.settings
    if not settings.enable_rate_limit:
        return True
    if settings.rate_limit_per_minute <= 0:
        return True

    now = time.monotonic()
    limits = rate_limits[client_id or "anonymous"]
    while limits and now - limits[0] >= 60:
        limits.popleft()

    if len(limits) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    limits.append(now)
    return True


@router.get("/health")
def health():
    return {"status": "ok", "service": "ip-sakti-api"}


@router.post("/consultations/query")
async def query(
    req: ConsultationRequest,
    db: Session = Depends(get_db),
    _api_ok: bool = Depends(require_api_key),
    _rate_ok: bool = Depends(enforce_rate_limit),
):
    init_db()
    return (await Orchestrator(db).run(req)).model_dump(mode="json")


@router.post("/memory")
def save_memory(
    record: MemoryRecord,
    db: Session = Depends(get_db),
    _api_ok: bool = Depends(require_api_key),
    _rate_ok: bool = Depends(enforce_rate_limit),
):
    init_db()
    return MemoryManager(db).save(record).model_dump(mode="json")


@router.get("/memory/{user_id}")
def get_memory(
    user_id: str,
    db: Session = Depends(get_db),
    _api_ok: bool = Depends(require_api_key),
    _rate_ok: bool = Depends(enforce_rate_limit),
):
    init_db()
    return [m.model_dump(mode="json") for m in MemoryManager(db).relevant(user_id)]


@router.post("/profiles")
def save_profile(
    user_id: str,
    profile: InnovationProfile,
    db: Session = Depends(get_db),
    _api_ok: bool = Depends(require_api_key),
    _rate_ok: bool = Depends(enforce_rate_limit),
):
    init_db()
    return {"profile_id": MemoryManager(db).save_profile(user_id, profile)}


@router.get("/countries")
def countries():
    return [
        {"code": "DE", "name": "Germany", "region": "EU", "profile_version": "2026-09-01"},
        {"code": "US", "name": "United States", "region": "US", "profile_version": "2026-09-01"},
        {"code": "AE", "name": "United Arab Emirates", "region": "GCC", "profile_version": "2026-09-01"},
        {"code": "JP", "name": "Japan", "region": "APAC", "profile_version": "2026-09-01"},
        {"code": "AU", "name": "Australia", "region": "APAC", "profile_version": "2026-09-01"},
        {"code": "BR", "name": "Brazil", "region": "LATAM", "profile_version": "2026-09-01"},
    ]
