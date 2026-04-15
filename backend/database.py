from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models import Base

load_dotenv()

# Default to SQLite for easy setup if Postgres isn't provided/working
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./feasibility.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
