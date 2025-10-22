"""
Configuration and constants for the Document Parser API.
"""

from pathlib import Path
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

# CORS Configuration
CORS_ALLOW_ORIGINS = ["*"]  # In production, specify exact domains
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Directory Configuration
# Point to docu folder relative to backend folder
DOCU_FOLDER = Path(__file__).parent.parent.parent / "docu"
DOCU_FOLDER.mkdir(exist_ok=True)

# Output folder for RAG-optimized parsing (Phase 3+)
OUTPUT_FOLDER = Path(__file__).parent.parent.parent / "output"
OUTPUT_FOLDER.mkdir(exist_ok=True)
