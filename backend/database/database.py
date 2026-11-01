from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = Path(__file__).resolve().parents[1] / "database" / "sentinelai.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_db_and_tables():
    from backend.database.models import Base as ModelBase

    ModelBase.metadata.create_all(bind=engine)
    return DB_PATH


create_db_and_tables()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
