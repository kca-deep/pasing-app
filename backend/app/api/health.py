"""
Health check and status endpoints.
"""

from fastapi import APIRouter
from app.models import ParseRequest
from app.table_utils import CAMELOT_AVAILABLE
from app.services.mineru_parser import check_mineru_installation
from app.services.remote_ocr_parser import check_remote_ocr_availability
from app.services.docling import EASYOCR_AVAILABLE

router = APIRouter()


@router.get("/")
async def root():
    """API status check"""
    # Get parser installation status
    mineru_status = check_mineru_installation()
    remote_ocr_status = check_remote_ocr_availability()

    return {
        "status": "running",
        "version": "2.5.0",  # Updated: Removed Dolphin Remote strategy
        "parsing_strategy": {
            "default": "Docling + Camelot Hybrid",
            "pdf_files": "Camelot (LATTICE + STREAM)" if CAMELOT_AVAILABLE else "Docling",
            "other_files": "Docling (DOCX, PPTX, HTML)",
            "available_parsers": {
                "remote_ocr": remote_ocr_status["available"],
                "mineru": mineru_status["installed"],
                "camelot": CAMELOT_AVAILABLE,
                "docling": True
            }
        },
        "mineru_parser": {
            "installed": mineru_status["installed"],
            "version": mineru_status.get("version", "unknown"),
            "default_enabled": False,
            "features": mineru_status.get("features", {}),
            "description": "Universal document parser with multi-language support and merged cell handling",
            "note": "Requires: pip install magic-pdf[full]"
        },
        "table_extraction": {
            "docling": True,
            "camelot": CAMELOT_AVAILABLE,
            "camelot_default": True
        },
        "ocr_engines": {
            "local": {
                "engine": "EasyOCR",
                "available": EASYOCR_AVAILABLE,
                "description": "High accuracy for Korean & English (built-in)",
                "languages": ["kor", "eng"],
                "note": "No installation needed, works out of the box"
            },
            "remote": {
                "info": "Use 'Remote OCR' strategy for Tesseract/PaddleOCR/Dolphin engines",
                "see": "remote_ocr_parser section below"
            }
        },
        "picture_description": {
            "available": True,
            "default_enabled": False,
            "models": ["smolvlm", "granite", "custom"],
            "default_model": "smolvlm",
            "note": "Requires VLM dependencies: pip install docling[vlm] or transformers>=4.30.0 torch>=2.0.0"
        },
        "smart_image_analysis": {
            "available": True,
            "default_enabled": False,
            "description": "Auto-select OCR vs VLM based on image type",
            "how_it_works": {
                "text_images": "Tables, forms, documents → OCR only",
                "visualizations": "Charts, graphs, diagrams → VLM description",
                "complex_images": "Mixed content → Both OCR + VLM"
            },
            "note": "Requires both OCR and VLM dependencies"
        },
        "remote_ocr_parser": {
            "available": remote_ocr_status["available"],
            "server_url": remote_ocr_status.get("server_url"),
            "engines": remote_ocr_status.get("engines", []),
            "supported_languages": remote_ocr_status.get("supported_languages", []),
            "supported_formats": ["PDF", "PNG", "JPG", "JPEG", "TIFF", "BMP"],
            "default_enabled": False,
            "description": "Remote OCR service for Korean document parsing with high accuracy",
            "note": "Server: http://kca-ai.kro.kr:8005/ocr/extract",
            "features": {
                "tesseract": "Fast OCR engine (~0.2s, good for simple documents)",
                "paddleocr": "High-accuracy OCR engine (~1.6s, best for Korean documents)",
                "dolphin": "AI-powered OCR engine (~5s, highest accuracy)"
            }
        }
    }


@router.post("/test-options")
async def test_options(request: ParseRequest):
    """Test endpoint to check option parsing"""
    opts = request.get_options()
    return {
        "request_options": request.options.model_dump() if request.options else None,
        "parsed_options": opts.model_dump(),
        "output_format": opts.output_format,
        "use_camelot": opts.use_camelot
    }
