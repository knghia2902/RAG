from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

engine = create_engine(get_settings().database_url.get_secret_value(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        try:
            yield db
        finally:
            db.rollback()
