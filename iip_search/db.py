import os

from sqlalchemy import create_engine

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv(
    "DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/iip_search_dev"
)

engine = create_engine(
    DB_URL, pool_size=10, max_overflow=2, pool_recycle=300, pool_use_lifo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
