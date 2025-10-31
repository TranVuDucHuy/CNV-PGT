from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DatabaseConfig

Base = declarative_base()

engine = create_engine(DatabaseConfig.DATA_SOURCE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine) # Create database tables

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
