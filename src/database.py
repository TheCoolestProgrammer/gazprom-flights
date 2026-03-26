from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config
from contextlib import contextmanager

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_session():
    with Session(engine) as session:
        yield session
# @contextmanager
# def get_session():
#     """Контекстный менеджер для ручного управления сессией."""
#     session = Session(engine)
#     try:
#         yield session
#     finally:
#         session.close()

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

SessionDep = Annotated[Session, Depends(get_session)]