"""
Configuration and constants for the Document Parser API.
"""

from pathlib import Path
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

# Configure logging (level from environment variable)
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(levelname)s: %(message)s'
)

# Suppress verbose loggers
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Create module logger
logger = logging.getLogger(__name__)

# API Configuration
API_VERSION = "2.2.0"
API_TITLE = "Document Parser API"
API_DESCRIPTION = "High-accuracy document parsing with Docling + Camelot hybrid strategy + VLM Picture Description"

# CORS Configuration (from environment variables)
cors_origins_str = os.getenv("CORS_ALLOW_ORIGINS", "*")
CORS_ALLOW_ORIGINS = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() in ("true", "1", "yes")
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "*").split(",") if os.getenv("CORS_ALLOW_METHODS") != "*" else ["*"]
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "*").split(",") if os.getenv("CORS_ALLOW_HEADERS") != "*" else ["*"]

# Directory Configuration
# Point to docu folder relative to backend folder
DOCU_FOLDER = Path(__file__).parent.parent.parent / "docu"
DOCU_FOLDER.mkdir(exist_ok=True)

# Output folder for RAG-optimized parsing (Phase 3+)
OUTPUT_FOLDER = Path(__file__).parent.parent.parent / "output"
OUTPUT_FOLDER.mkdir(exist_ok=True)
