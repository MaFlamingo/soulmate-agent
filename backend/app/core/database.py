"""SQLAlchemy database engine and session factory."""

from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Resolve relative path to absolute, relative to backend/
_data_dir = Path(__file__).resolve().parent.parent.parent / "data"
_data_dir.mkdir(parents=True, exist_ok=True)

# Resolve the database path to an absolute path in the data/ directory
db_url = settings.database_url
# Handle sqlite relative paths by resolving to the backend/data/ directory
if "sqlite" in db_url and db_url.startswith("sqlite:///./"):
    # Use just the filename, store in _data_dir
    filename = db_url.rsplit("/", 1)[-1]
    db_url = f"sqlite:///{_data_dir / filename}"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Enable WAL mode for SQLite for better concurrent reads
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in str(type(dbapi_connection)):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call on app startup."""
    Base.metadata.create_all(bind=engine)
