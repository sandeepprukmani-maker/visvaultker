from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from server.models import Base
import os

SQLITE_DATABASE_URL = os.getenv("SQLITE_DATABASE_URL", "sqlite:///./visionvault.db")

engine = create_engine(
    SQLITE_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
