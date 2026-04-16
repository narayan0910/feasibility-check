from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from models import Base

engine = create_engine(settings.POSTGRES_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
