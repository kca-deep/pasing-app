"""
Database initialization script.
Creates all tables if they don't exist.
"""
from app.database import Base, engine
from app import db_models  # Import models to register them with Base


def init_db():
    """
    Initialize the database by creating all tables.
    This is safe to call multiple times - it only creates tables that don't exist.
    """
    print("Initializing database...")
    print(f"Database URL: {engine.url}")

    # Create all tables defined in db_models
    Base.metadata.create_all(bind=engine)

    print("Database initialized successfully!")
    print("Created tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    # Run this script directly to initialize the database
    init_db()
