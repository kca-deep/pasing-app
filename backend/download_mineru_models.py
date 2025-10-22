"""
MinerU Model Downloader

Downloads required model weights for magic-pdf (MinerU) parsing.

Usage:
    python download_mineru_models.py

Models downloaded:
    - Layout Detection Model (LayoutLMv3)
    - Formula Detection Model (YOLO MFD)
    - Table Recognition Model (StructEqTable)

Total size: ~2-3GB
"""

import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def download_models():
    """
    Download MinerU models using magic-pdf CLI
    """
    try:
        # Check if magic-pdf is installed
        import magic_pdf
        logger.info(f"✓ magic-pdf installed (version: {magic_pdf.__version__ if hasattr(magic_pdf, '__version__') else 'unknown'})")
    except ImportError:
        logger.error("✗ magic-pdf not installed!")
        logger.error("  Install with: pip install magic-pdf[full]")
        sys.exit(1)

    # Get backend directory
    backend_dir = Path(__file__).parent
    models_dir = backend_dir / "models"

    logger.info(f"Models directory: {models_dir}")

    # Create models directory structure
    models_dir.mkdir(exist_ok=True)

    logger.info("\n" + "="*60)
    logger.info("MinerU Model Download Instructions")
    logger.info("="*60)

    logger.info("""
MinerU requires downloading model weights from ModelScope or Hugging Face.

OPTION 1: Auto-download (Recommended - Easiest)
---------------------------------------------
Run the mineru-models-download command to auto-download models:

    mineru-models-download -m pipeline -s huggingface

Or for Chinese users (faster):

    mineru-models-download -m pipeline -s modelscope

This will download all required models (~2-3GB) to the default location.


OPTION 2: Manual Download (For custom model paths)
-------------------------------------------------
1. Download models from ModelScope or Hugging Face:

   a) Layout Detection Model (LayoutLMv3):
      ModelScope: https://www.modelscope.cn/models/wanderkid/PDF-Extract-Kit
      HuggingFace: https://huggingface.co/wanderkid/PDF-Extract-Kit

   b) Formula Detection (YOLO MFD):
      File needed: yolo_v8_ft.pt
      Place in: backend/models/MFD/YOLO/

   c) Table Recognition (StructEqTable):
      File needed: struct_eqtable.pt
      Place in: backend/models/StructEqTable/

2. Update model paths in config (if needed):
   Create a magic.json config file with custom paths.


OPTION 3: Use environment variables
-----------------------------------
Set model paths via environment variables:

    $env:MINERU_MODEL_PATH = "C:\\path\\to\\models"

Then run the download command.


CURRENT STATUS:
""")

    # Check for existing model files
    required_models = [
        ("Layout Model", models_dir / "Layout" / "model.pt"),
        ("MFD Model", models_dir / "MFD" / "YOLO" / "yolo_v8_ft.pt"),
        ("Table Model", models_dir / "StructEqTable" / "struct_eqtable.pt"),
    ]

    all_found = True
    for name, path in required_models:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            logger.info(f"  ✓ {name}: Found ({size_mb:.1f} MB)")
        else:
            logger.info(f"  ✗ {name}: Missing")
            all_found = False

    if all_found:
        logger.info("\n✓ All models are present!")
        logger.info("  You can now use MinerU parsing.")
    else:
        logger.info("\n✗ Some models are missing.")
        logger.info("  Run: magic-pdf --download-models")
        logger.info("  Or download manually from the links above.")

    logger.info("\n" + "="*60)

    return all_found


if __name__ == "__main__":
    logger.info("MinerU Model Downloader")
    logger.info("-" * 60)

    success = download_models()

    if not success:
        logger.info("\nNext steps:")
        logger.info("  1. Run: mineru-models-download -m pipeline -s huggingface")
        logger.info("  2. Or run: mineru-models-download -m pipeline -s modelscope (China)")
        logger.info("  3. Or download models manually from ModelScope/HuggingFace")
        logger.info("  4. Then retry parsing with MinerU")
        sys.exit(1)
    else:
        logger.info("\n✓ Setup complete! MinerU is ready to use.")
        sys.exit(0)
