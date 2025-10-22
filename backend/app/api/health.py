"""
Health check and status endpoints.
"""

from fastapi import APIRouter
from app.models import ParseRequest
from app.table_utils import CAMELOT_AVAILABLE

router = APIRouter()


@router.get("/")
async def root():
    """API status check"""
    return {
        "status": "running",
        "version": "2.2.0",
        "parsing_strategy": {
            "default": "Docling + Camelot Hybrid",
            "pdf_files": "Camelot (LATTICE + STREAM)" if CAMELOT_AVAILABLE else "Docling",
            "other_files": "Docling (DOCX, PPTX, HTML)"
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
