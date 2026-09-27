from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from app.core.config import normalize_database_url, settings

database_url = make_url(normalize_database_url(settings.database_url))
if database_url.get_backend_name() == "sqlite" and database_url.database not in {None, "", ":memory:"}:
    database_path = Path(database_url.database)
    if not database_path.is_absolute() and not database_url.database.startswith("file:"):
        project_root = Path(__file__).resolve().parents[4]
        database_url = database_url.set(database=str(project_root / database_path))

connect_args = {"check_same_thread": False} if database_url.get_backend_name() == "sqlite" else {}
engine = create_engine(
    database_url,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
