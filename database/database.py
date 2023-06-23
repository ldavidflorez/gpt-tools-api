from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os

SQLALCHEMY_DATABASE_URL = os.environ["CONNECTION_STRING"]

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       'connect_timeout': 10}, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
