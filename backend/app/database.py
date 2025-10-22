"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database file path: ../parsing_app.db (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "..", "parsing_app.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
# echo=True for development (logs SQL queries)
# check_same_thread=False is needed for SQLite to work with FastAPI
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

# Create SessionLocal class
# autocommit=False: transactions must be explicitly committed
# autoflush=False: changes are not automatically flushed to DB
# expire_on_commit=False: objects remain usable after commit
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base class for declarative models
Base = declarative_base()


def get_db():
    """
    Dependency function that yields a database session.
    Used with FastAPI's Depends() for automatic session management.

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
