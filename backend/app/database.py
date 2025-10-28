"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database file path: from environment variable or default
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH_RELATIVE = os.getenv("DATABASE_PATH", "../parsing_app.db")
DATABASE_PATH = os.path.join(BASE_DIR, DATABASE_PATH_RELATIVE)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
# echo: from environment variable (True for development, False for production)
# check_same_thread=False is needed for SQLite to work with FastAPI
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "True").lower() in ("true", "1", "yes")
engine = create_engine(
    DATABASE_URL,
    echo=DATABASE_ECHO,
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
        # Commit any pending transactions before closing
        # This prevents ROLLBACK warnings when session closes
        if db.in_transaction():
            db.commit()
    except Exception:
        # Rollback on error
        db.rollback()
        raise
    finally:
        db.close()
