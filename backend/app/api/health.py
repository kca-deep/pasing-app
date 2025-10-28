"""
Health check and status endpoints.
"""

from fastapi import APIRouter
from app.models import ParseRequest
from app.table_utils import CAMELOT_AVAILABLE
from app.services.mineru_parser import check_mineru_installation
from app.services.dolphin_remote import check_dolphin_remote_installation
from app.services.remote_ocr import check_remote_ocr_availability

router = APIRouter()


@router.get("/")
async def root():
    """API status check"""
    # Get parser installation status
    mineru_status = check_mineru_installation()
    dolphin_remote_status = check_dolphin_remote_installation()
    remote_ocr_status = check_remote_ocr_availability()

    return {
        "status": "running",
        "version": "2.4.0",  # Updated for Remote OCR support
        "parsing_strategy": {
            "default": "Docling + Camelot Hybrid",
            "pdf_files": "Camelot (LATTICE + STREAM)" if CAMELOT_AVAILABLE else "Docling",
            "other_files": "Docling (DOCX, PPTX, HTML)",
            "available_parsers": {
                "remote_ocr": remote_ocr_status["available"],
                "dolphin_remote": dolphin_remote_status.get("installed", False),
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
        },
        "dolphin_remote_gpu": {
            "available": dolphin_remote_status.get("installed", False),
            "server_url": dolphin_remote_status.get("server_url"),
            "server_status": dolphin_remote_status.get("server_status"),
            "model_loaded": dolphin_remote_status.get("model_loaded", False),
            "cuda_available": dolphin_remote_status.get("cuda_available", False),
            "default_enabled": False,
            "description": "Remote GPU server for Dolphin AI parser (fastest option)",
            "note": "Requires DOLPHIN_GPU_SERVER environment variable"
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
