# MinerU Model Setup Guide

## Overview

MinerU (magic-pdf) requires downloading AI model weights before first use. These models enable advanced document parsing features like layout detection, formula recognition, and table extraction.

**Total download size:** ~2-3 GB
**One-time setup:** Models are downloaded once and reused

## Quick Start (Recommended)

### Method 1: Auto-Download (Easiest)

```powershell
# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Download all models automatically
mineru-models-download -m pipeline -s huggingface

# Or for Chinese users (faster):
mineru-models-download -m pipeline -s modelscope
```

This downloads all required models to the default location and is the **recommended approach**.

### Method 2: Check Status and Download

```powershell
# Check current model status
cd backend
python download_mineru_models.py
```

This script will:
- ✓ Check if magic-pdf is installed
- ✓ Show which models are missing
- ✓ Provide download instructions
- ✓ Verify successful installation

## Required Models

MinerU needs these models:

| Model | Purpose | Size | File |
|-------|---------|------|------|
| **Layout Detection** | Detects document structure (paragraphs, headers, etc.) | ~400 MB | `layout_model.pt` |
| **Formula Detection (MFD)** | Detects mathematical formulas | ~100 MB | `yolo_v8_ft.pt` |
| **Table Recognition** | Extracts table structure | ~200 MB | `struct_eqtable.pt` |
| **OCR Models** | Text recognition (if using OCR) | ~1 GB | Various |

## Installation Options

### Option A: Use magic-pdf CLI (Recommended)

```powershell
# Download all models at once (HuggingFace)
mineru-models-download -m pipeline -s huggingface

# Or use ModelScope (faster for China users)
mineru-models-download -m pipeline -s modelscope

# Download ALL models including VLM (larger, optional)
mineru-models-download -m all -s huggingface
```

### Option B: Manual Download

If auto-download fails (firewall, proxy, etc.), download manually:

1. **From ModelScope (China users):**
   - Layout + MFD + Table models: https://www.modelscope.cn/models/wanderkid/PDF-Extract-Kit

2. **From Hugging Face (International users):**
   - Layout + MFD + Table models: https://huggingface.co/wanderkid/PDF-Extract-Kit

3. **Extract and place files:**
   ```
   backend/
   └── models/
       ├── Layout/
       │   └── model.pt
       ├── MFD/
       │   └── YOLO/
       │       └── yolo_v8_ft.pt
       └── StructEqTable/
           └── struct_eqtable.pt
   ```

### Option C: Use Environment Variable

```powershell
# Set custom model path
$env:MINERU_MODEL_PATH = "C:\path\to\models"

# Then download
magic-pdf --download-models
```

## Troubleshooting

### Error: `FileNotFoundError: yolo_v8_ft.pt`

**Cause:** Model weights not downloaded.

**Solution:**
```powershell
cd backend
python download_mineru_models.py
# Then run: magic-pdf --download-models
```

### Error: `mineru: command not found` or `magic-pdf: command not found`

**Cause:** MinerU not installed or venv not activated.

**Solution:**
```powershell
# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Check if mineru is installed
mineru --version

# If not installed, install it
pip install mineru[pipeline]

# Verify installation
mineru-models-download --help
```

### Download fails (network/firewall issues)

**Solution 1 - Use proxy:**
```powershell
$env:HTTP_PROXY = "http://your-proxy:port"
$env:HTTPS_PROXY = "http://your-proxy:port"
mineru-models-download -m pipeline -s huggingface
```

**Solution 2 - Manual download:**
- Download from ModelScope or Hugging Face (see Option B above)
- Extract files to `backend/models/` directory

### Models download but still get errors

**Check model paths:**
```powershell
cd backend
python download_mineru_models.py
```

This will verify all model files are in the correct location.

## Verification

After downloading models, verify the setup:

```powershell
cd backend
python download_mineru_models.py
```

Expected output:
```
✓ Layout Model: Found (400.5 MB)
✓ MFD Model: Found (95.2 MB)
✓ Table Model: Found (180.3 MB)

✓ All models are present!
  You can now use MinerU parsing.
```

## Model Download Locations

By default, magic-pdf stores models in:

**Windows:**
- `C:\Users\<YourName>\.magic-pdf\models\`
- Or custom path: `backend/models/` (if configured)

**Linux/Mac:**
- `~/.magic-pdf/models/`

## Performance Notes

- **First parse:** May take 30-60 seconds (model loading + parsing)
- **Subsequent parses:** ~5-15 seconds (models stay in memory)
- **Memory usage:** ~2-4 GB RAM (models loaded in memory)

## Alternative: Disable Specific Models

If you don't need certain features, you can disable models:

```python
# In mineru_parser.py, modify the parsing call:
infer_result = ds.apply(
    doc_analyze,
    ocr=use_ocr,
    lang=ds._lang,
    # Disable formula detection to skip MFD model
    formula_enable=False,
    # Disable table detection
    table_enable=False
)
```

**Note:** This reduces model requirements but also reduces parsing accuracy.

## Additional Resources

- **MinerU Documentation:** https://github.com/opendatalab/MinerU
- **magic-pdf PyPI:** https://pypi.org/project/magic-pdf/
- **Model Repository:** https://huggingface.co/wanderkid/PDF-Extract-Kit
- **Chinese Mirror:** https://www.modelscope.cn/models/wanderkid/PDF-Extract-Kit

## Summary

**Quick setup (3 steps):**

1. Activate venv: `.\backend\venv\Scripts\Activate.ps1`
2. Download models: `mineru-models-download -m pipeline -s huggingface`
3. Verify: `python backend/download_mineru_models.py`

After this one-time setup, MinerU is ready to parse documents!
