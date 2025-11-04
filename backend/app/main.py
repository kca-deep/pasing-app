"""
Document Parser API - Main Application

A high-accuracy document parsing service using Docling + Camelot hybrid strategy
with optional VLM picture description.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from app.config import (
    API_VERSION,
    API_TITLE,
    API_DESCRIPTION,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS
)

# Import routers
from app.api import health, documents, parsing, results, database, async_parsing, dify

# Import database initialization
from app.init_db import init_db

# Import logging configuration
from app.logging_config import configure_logging

# Configure UTF-8 logging
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes the database on startup.
    """
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup (if needed)


# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router, tags=["Documents"])
app.include_router(parsing.router, tags=["Parsing"])
app.include_router(async_parsing.router, tags=["Async Parsing"])
app.include_router(results.router, tags=["Results"])
app.include_router(database.router, tags=["Database"])
app.include_router(dify.router, tags=["Dify"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
