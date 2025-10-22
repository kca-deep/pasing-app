"""
Camelot-based table extraction with hybrid LATTICE + STREAM strategy.

This module provides high-accuracy table extraction from PDFs using Camelot library.

Strategy:
1. Primary: Use Camelot LATTICE mode (high accuracy for bordered tables)
2. Fallback: Use STREAM mode for pages where LATTICE fails (borderless tables)
3. Hybrid: Combine both strategies for maximum coverage

Author: Implementation based on user requirements
"""

from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import logging
from dataclasses import dataclass
import pandas as pd
import warnings
import os

try:
    import camelot
    # Suppress Camelot debug logs
    import cv2
    cv2.setLogLevel(0)  # Suppress OpenCV logs

    # Suppress specific warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)

    # Suppress Camelot internal loggers
    logging.getLogger('camelot').setLevel(logging.WARNING)
    logging.getLogger('pdfminer').setLevel(logging.WARNING)
    logging.getLogger('ghostscript').setLevel(logging.WARNING)

except ImportError:
    camelot = None

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# pdfplumber import for fallback (Phase 1 improvement)
try:
    from .pdfplumber_extractor import (
        extract_table_from_region,
        validate_pdfplumber_available,
        PdfPlumberTableExtraction
    )
    PDFPLUMBER_AVAILABLE = validate_pdfplumber_available()
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("⚠️ pdfplumber not available. Install with: pip install pdfplumber")

logger = logging.getLogger(__name__)


@dataclass
class CamelotTableExtraction:
    """Extracted table from Camelot with metadata"""
    table_id: str
    page: int
    dataframe: pd.DataFrame
    accuracy: float  # Accuracy score from Camelot
    parsing_report: Dict
    extraction_mode: str  # "lattice" or "stream"

    # Geometry information
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)

    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {
            "table_id": self.table_id,
            "page": self.page,
            "accuracy": self.accuracy,
            "extraction_mode": self.extraction_mode,
            "bbox": self.bbox,
            "shape": {
                "rows": len(self.dataframe),
                "cols": len(self.dataframe.columns)
            },
            "data": self.dataframe.to_dict(orient='records'),
            "parsing_report": self.parsing_report
        }

    def to_markdown(self) -> str:
        """Convert table to Markdown format"""
        return self.dataframe.to_markdown(index=False)

    def to_html(self) -> str:
        """Convert table to HTML format"""
        return self.dataframe.to_html(index=False, escape=False)


def extract_tables_with_lattice(
    pdf_path: Path,
    pages: str = 'all',
    **kwargs
) -> Tuple[List[CamelotTableExtraction], Set[int]]:
    """
    Extract tables using Camelot LATTICE mode.

    LATTICE mode is best for:
    - Tables with clear borders/lines
    - Grid-based tables
    - High accuracy requirements

    Args:
        pdf_path: Path to PDF file
        pages: Pages to process (default: 'all')
        **kwargs: Additional Camelot parameters

    Returns:
        Tuple of (extracted_tables, successful_pages)
    """
    if camelot is None:
        raise ImportError("Camelot not installed. Install with: pip install camelot-py[cv]")

    # Default LATTICE parameters for high accuracy (optimized for Korean PDFs)
    lattice_kwargs = {
        'flavor': 'lattice',
        'pages': pages,
        'line_scale': 40,  # Sensitivity for line detection (default: 15, optimized: 40)
        'line_tol': 3,  # Line tolerance for incomplete lines (default: 2, optimized: 3 for Korean PDFs)
        'joint_tol': 3,  # Joint tolerance for intersection detection (default: 2, optimized: 3 for merged cells)
        'resolution': 400,  # Image resolution for better Korean character recognition (default: 300, optimized: 400)
        'shift_text': ['l', 't'],  # Shift text to left/top for better alignment
        'copy_text': ['v'],  # Copy text vertically for merged cells
        'split_text': True,  # Split text that spans across multiple cells (Phase 1 improvement)
        'strip_text': ' .\n',  # Remove spaces, dots, newlines to prevent text order corruption
        'suppress_stdout': True,  # Suppress Camelot stdout
        **kwargs
    }

    try:
        # Use tqdm for progress if available
        if TQDM_AVAILABLE:
            desc = f"🔍 LATTICE: {pdf_path.name}"
            with tqdm(desc=desc, unit="table", leave=False) as pbar:
                tables = camelot.read_pdf(str(pdf_path), **lattice_kwargs)
                pbar.total = len(tables)
                pbar.refresh()

                extractions = []
                successful_pages = set()

                for idx, table in enumerate(tables):
                    table_id = f"table_{idx+1:03d}"
                    page_num = table.page

                    # Get accuracy score
                    accuracy = table.accuracy if hasattr(table, 'accuracy') else 0.0

                    # Get parsing report
                    parsing_report = table.parsing_report if hasattr(table, 'parsing_report') else {}

                    # Get bounding box
                    bbox = table._bbox if hasattr(table, '_bbox') else (0, 0, 0, 0)

                    extraction = CamelotTableExtraction(
                        table_id=table_id,
                        page=page_num,
                        dataframe=table.df,
                        accuracy=accuracy,
                        parsing_report=parsing_report,
                        extraction_mode="lattice",
                        bbox=bbox
                    )

                    extractions.append(extraction)
                    successful_pages.add(page_num)

                    pbar.set_postfix({"page": page_num, "acc": f"{accuracy:.2%}"})
                    pbar.update(1)

                logger.info(f"✅ LATTICE: {len(extractions)} tables on {len(successful_pages)} pages")
                return extractions, successful_pages
        else:
            # Fallback without tqdm
            tables = camelot.read_pdf(str(pdf_path), **lattice_kwargs)

            extractions = []
            successful_pages = set()

            for idx, table in enumerate(tables):
                table_id = f"table_{idx+1:03d}"
                page_num = table.page

                accuracy = table.accuracy if hasattr(table, 'accuracy') else 0.0
                parsing_report = table.parsing_report if hasattr(table, 'parsing_report') else {}
                bbox = table._bbox if hasattr(table, '_bbox') else (0, 0, 0, 0)

                extraction = CamelotTableExtraction(
                    table_id=table_id,
                    page=page_num,
                    dataframe=table.df,
                    accuracy=accuracy,
                    parsing_report=parsing_report,
                    extraction_mode="lattice",
                    bbox=bbox
                )

                extractions.append(extraction)
                successful_pages.add(page_num)

            logger.info(f"✅ LATTICE: {len(extractions)} tables on {len(successful_pages)} pages")
            return extractions, successful_pages

    except Exception as e:
        logger.error(f"❌ LATTICE extraction failed: {str(e)}")
        return [], set()


def extract_tables_with_stream(
    pdf_path: Path,
    pages: str = 'all',
    **kwargs
) -> Tuple[List[CamelotTableExtraction], Set[int]]:
    """
    Extract tables using Camelot STREAM mode.

    STREAM mode is best for:
    - Tables without borders
    - Text-aligned tables
    - Fallback when LATTICE fails

    Args:
        pdf_path: Path to PDF file
        pages: Pages to process (default: 'all')
        **kwargs: Additional Camelot parameters

    Returns:
        Tuple of (extracted_tables, successful_pages)
    """
    if camelot is None:
        raise ImportError("Camelot not installed. Install with: pip install camelot-py[cv]")

    # Default STREAM parameters
    stream_kwargs = {
        'flavor': 'stream',
        'pages': pages,
        'edge_tol': 50,  # Edge tolerance for table detection
        'row_tol': 2,    # Row tolerance for grouping
        'column_tol': 0,  # Column tolerance
        'split_text': True,  # Split text that spans across multiple cells (Phase 1 improvement)
        'strip_text': ' .\n',  # Remove spaces, dots, newlines to prevent text order corruption
        'suppress_stdout': True,  # Suppress Camelot stdout
        **kwargs
    }

    try:
        # Use tqdm for progress if available
        if TQDM_AVAILABLE:
            desc = f"🔄 STREAM: {pdf_path.name}"
            with tqdm(desc=desc, unit="table", leave=False) as pbar:
                tables = camelot.read_pdf(str(pdf_path), **stream_kwargs)
                pbar.total = len(tables)
                pbar.refresh()

                extractions = []
                successful_pages = set()

                for idx, table in enumerate(tables):
                    table_id = f"table_{idx+1:03d}"
                    page_num = table.page

                    # Get accuracy score
                    accuracy = table.accuracy if hasattr(table, 'accuracy') else 0.0

                    # Get parsing report
                    parsing_report = table.parsing_report if hasattr(table, 'parsing_report') else {}

                    # Get bounding box
                    bbox = table._bbox if hasattr(table, '_bbox') else (0, 0, 0, 0)

                    extraction = CamelotTableExtraction(
                        table_id=table_id,
                        page=page_num,
                        dataframe=table.df,
                        accuracy=accuracy,
                        parsing_report=parsing_report,
                        extraction_mode="stream",
                        bbox=bbox
                    )

                    extractions.append(extraction)
                    successful_pages.add(page_num)

                    pbar.set_postfix({"page": page_num, "acc": f"{accuracy:.2%}"})
                    pbar.update(1)

                logger.info(f"✅ STREAM: {len(extractions)} tables on {len(successful_pages)} pages")
                return extractions, successful_pages
        else:
            # Fallback without tqdm
            tables = camelot.read_pdf(str(pdf_path), **stream_kwargs)

            extractions = []
            successful_pages = set()

            for idx, table in enumerate(tables):
                table_id = f"table_{idx+1:03d}"
                page_num = table.page

                accuracy = table.accuracy if hasattr(table, 'accuracy') else 0.0
                parsing_report = table.parsing_report if hasattr(table, 'parsing_report') else {}
                bbox = table._bbox if hasattr(table, '_bbox') else (0, 0, 0, 0)

                extraction = CamelotTableExtraction(
                    table_id=table_id,
                    page=page_num,
                    dataframe=table.df,
                    accuracy=accuracy,
                    parsing_report=parsing_report,
                    extraction_mode="stream",
                    bbox=bbox
                )

                extractions.append(extraction)
                successful_pages.add(page_num)

            logger.info(f"✅ STREAM: {len(extractions)} tables on {len(successful_pages)} pages")
            return extractions, successful_pages

    except Exception as e:
        logger.error(f"❌ STREAM extraction failed: {str(e)}")
        return [], set()


def extract_tables_hybrid(
    pdf_path: Path,
    pages: str = 'all',
    lattice_accuracy_threshold: float = 0.0,
    **kwargs
) -> Tuple[List[CamelotTableExtraction], Dict[str, any]]:
    """
    Hybrid table extraction strategy: LATTICE first, STREAM fallback.

    This provides the best accuracy by:
    1. Using LATTICE for high-accuracy bordered table extraction
    2. Using STREAM for pages where LATTICE found no tables or low accuracy

    Args:
        pdf_path: Path to PDF file
        pages: Pages to process (default: 'all')
        lattice_accuracy_threshold: Minimum accuracy for LATTICE (default: 0.0)
        **kwargs: Additional Camelot parameters

    Returns:
        Tuple of (all_extractions, extraction_summary)
    """
    logger.info(f"🚀 HYBRID extraction: {pdf_path.name}")

    # Step 1: Try LATTICE mode first
    lattice_extractions, lattice_pages = extract_tables_with_lattice(
        pdf_path,
        pages=pages,
        **kwargs.get('lattice_kwargs', {})
    )

    # Filter low-accuracy LATTICE results
    high_accuracy_lattice = []
    low_accuracy_pages = set()

    for extraction in lattice_extractions:
        if extraction.accuracy >= lattice_accuracy_threshold:
            high_accuracy_lattice.append(extraction)
        else:
            low_accuracy_pages.add(extraction.page)

    # Step 2: Determine pages that need STREAM fallback
    if pages == 'all':
        # If 'all', we need to know total pages - use LATTICE results as reference
        # For now, we'll skip STREAM if LATTICE found all tables
        stream_pages = low_accuracy_pages
    else:
        # Parse page specification (e.g., "1,2,3" or "1-5")
        requested_pages = parse_page_spec(pages)
        missing_pages = requested_pages - lattice_pages
        stream_pages = missing_pages.union(low_accuracy_pages)

    # Step 3: Run STREAM mode on missing/low-accuracy pages
    stream_extractions = []
    if stream_pages:
        stream_pages_str = ','.join(map(str, sorted(stream_pages)))
        logger.info(f"🔄 STREAM fallback: pages {stream_pages_str}")

        stream_extractions, stream_successful = extract_tables_with_stream(
            pdf_path,
            pages=stream_pages_str,
            **kwargs.get('stream_kwargs', {})
        )

    # Step 4: Validate text order and apply pdfplumber fallback if needed
    validated_extractions = []
    pdfplumber_fallback_count = 0

    all_extractions_temp = high_accuracy_lattice + stream_extractions

    for extraction in all_extractions_temp:
        # Validate text order
        if not validate_table_text_order(extraction.dataframe):
            logger.warning(f"⚠️ {extraction.table_id} (Page {extraction.page}) has text order issues")

            # Try pdfplumber fallback
            fixed_extraction = fix_table_with_pdfplumber(pdf_path, extraction)

            if fixed_extraction:
                validated_extractions.append(fixed_extraction)
                pdfplumber_fallback_count += 1
            else:
                # Keep original even if validation failed
                logger.warning(f"  ⚠️ Keeping original (pdfplumber fallback unavailable)")
                validated_extractions.append(extraction)
        else:
            # Text order is OK
            validated_extractions.append(extraction)

    all_extractions = validated_extractions

    # Re-number table IDs sequentially
    for idx, extraction in enumerate(all_extractions):
        extraction.table_id = f"table_{idx+1:03d}"

    # Create summary
    summary = {
        "total_tables": len(all_extractions),
        "lattice_tables": len(high_accuracy_lattice),
        "stream_tables": len(stream_extractions),
        "pdfplumber_fallbacks": pdfplumber_fallback_count,
        "lattice_pages": sorted(lattice_pages),
        "stream_pages": sorted([e.page for e in stream_extractions]),
        "low_accuracy_fallbacks": len(low_accuracy_pages),
        "extraction_modes": {
            "lattice": len([e for e in all_extractions if e.extraction_mode == "lattice"]),
            "stream": len([e for e in all_extractions if e.extraction_mode == "stream"]),
            "pdfplumber": pdfplumber_fallback_count
        }
    }

    if pdfplumber_fallback_count > 0:
        logger.info(f"✅ Extracted {summary['total_tables']} tables "
                    f"({summary['lattice_tables']} LATTICE + {summary['stream_tables']} STREAM + {pdfplumber_fallback_count} pdfplumber)")
    else:
        logger.info(f"✅ Extracted {summary['total_tables']} tables "
                    f"({summary['lattice_tables']} LATTICE + {summary['stream_tables']} STREAM)")

    return all_extractions, summary


def validate_table_text_order(df: pd.DataFrame) -> bool:
    """
    Validate if table text has correct order (Korean date patterns).

    This detects common text ordering issues where parentheses and weekday names
    are separated or reversed.

    Args:
        df: Pandas DataFrame from table extraction

    Returns:
        True if text order appears correct, False if likely corrupted

    Examples of corrupted patterns:
        - ") 수 10.13( 월" - reversed order
        - "14일화 ( )" - weekday outside parentheses
        - "2.4( ) 화" - space between parenthesis and weekday

    Examples of valid patterns:
        - "10.13(월)" - correct format
        - "2.4(화)~2.7(금)" - correct range format
    """
    import re

    # Extract all cell texts (including cells with newlines)
    all_texts = []
    for col in df.columns:
        for val in df[col]:
            if pd.notna(val):
                all_texts.append(str(val))

    # Combine all cell texts and normalize whitespace
    # Convert all whitespace (spaces, newlines, tabs) to single space
    combined_text = ' '.join(all_texts)
    combined_text = re.sub(r'\s+', ' ', combined_text)

    # Corrupted patterns to detect (improved: removed strict suffix requirements)
    corrupted_patterns = [
        r'\)\s*[월화수목금토일]\s+\d+',           # ") 수 10" (removed trailing '.')
        r'\d+\s*일\s*[월화수목금토일]',            # "14일화" (removed trailing '\(')
        r'\d+\.\d+\s*\(\s*\)\s*[월화수목금토일]',  # "2.4( ) 화"
        r'\(\s*\)\s*[월화수목금토일]',             # "( ) 화"
    ]

    # Check if text contains corrupted patterns
    for pattern in corrupted_patterns:
        if re.search(pattern, combined_text):
            logger.debug(f"   Detected corrupted pattern: {pattern} in text: {combined_text[:100]}...")
            return False

    # If no corrupted patterns found, text order is OK
    return True


def fix_table_with_pdfplumber(
    pdf_path: Path,
    extraction: CamelotTableExtraction
) -> Optional[CamelotTableExtraction]:
    """
    Re-extract a table using pdfplumber to fix text ordering issues.

    Args:
        pdf_path: Path to PDF file
        extraction: Camelot extraction with incorrect text order

    Returns:
        Updated CamelotTableExtraction with fixed DataFrame, or None if failed
    """
    if not PDFPLUMBER_AVAILABLE:
        logger.warning("pdfplumber not available for fallback")
        return None

    try:
        # Use pdfplumber to re-extract from the same region
        fixed_df = extract_table_from_region(
            pdf_path,
            extraction.page,
            extraction.bbox
        )

        if fixed_df is not None and not fixed_df.empty:
            # Create updated extraction with fixed DataFrame
            extraction.dataframe = fixed_df
            extraction.extraction_mode = "pdfplumber_fallback"
            extraction.parsing_report["fallback_reason"] = "text_order_validation_failed"

            logger.info(f"  ✅ Fixed {extraction.table_id} with pdfplumber")
            return extraction

        return None

    except Exception as e:
        logger.warning(f"  ❌ pdfplumber fallback failed for {extraction.table_id}: {e}")
        return None


def parse_page_spec(page_spec: str) -> Set[int]:
    """
    Parse page specification string into set of page numbers.

    Examples:
        "1,2,3" -> {1, 2, 3}
        "1-5" -> {1, 2, 3, 4, 5}
        "1,3-5,7" -> {1, 3, 4, 5, 7}

    Args:
        page_spec: Page specification string

    Returns:
        Set of page numbers
    """
    pages = set()

    for part in page_spec.split(','):
        part = part.strip()
        if '-' in part:
            # Range: "1-5"
            start, end = part.split('-')
            pages.update(range(int(start), int(end) + 1))
        else:
            # Single page: "3"
            pages.add(int(part))

    return pages


def save_camelot_extractions(
    extractions: List[CamelotTableExtraction],
    output_dir: Path,
    format: str = 'json'
) -> List[Path]:
    """
    Save Camelot table extractions to files.

    Args:
        extractions: List of CamelotTableExtraction objects
        output_dir: Output directory
        format: Output format ('json', 'csv', 'markdown', 'html')

    Returns:
        List of saved file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    iterator = tqdm(extractions, desc="💾 Saving tables", unit="file", leave=False) if TQDM_AVAILABLE else extractions

    for extraction in iterator:
        base_filename = f"{extraction.table_id}_page{extraction.page}"

        if format == 'json':
            import json
            filepath = output_dir / f"{base_filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(extraction.to_dict(), f, ensure_ascii=False, indent=2)

        elif format == 'csv':
            filepath = output_dir / f"{base_filename}.csv"
            extraction.dataframe.to_csv(filepath, index=False, encoding='utf-8')

        elif format == 'markdown':
            filepath = output_dir / f"{base_filename}.md"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(extraction.to_markdown())

        elif format == 'html':
            filepath = output_dir / f"{base_filename}.html"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(extraction.to_html())

        else:
            raise ValueError(f"Unsupported format: {format}")

        saved_paths.append(filepath)

    if saved_paths:
        logger.info(f"💾 Saved {len(saved_paths)} files to {output_dir}")

    return saved_paths


# Convenience function for quick extraction
def quick_extract(
    pdf_path: Path,
    mode: str = 'hybrid',
    pages: str = 'all',
    **kwargs
) -> List[CamelotTableExtraction]:
    """
    Quick table extraction with sensible defaults.

    Args:
        pdf_path: Path to PDF file
        mode: Extraction mode ('lattice', 'stream', 'hybrid')
        pages: Pages to process (default: 'all')
        **kwargs: Additional parameters

    Returns:
        List of CamelotTableExtraction objects
    """
    if mode == 'lattice':
        extractions, _ = extract_tables_with_lattice(pdf_path, pages, **kwargs)
        return extractions

    elif mode == 'stream':
        extractions, _ = extract_tables_with_stream(pdf_path, pages, **kwargs)
        return extractions

    elif mode == 'hybrid':
        extractions, _ = extract_tables_hybrid(pdf_path, pages, **kwargs)
        return extractions

    else:
        raise ValueError(f"Invalid mode: {mode}. Choose 'lattice', 'stream', or 'hybrid'")
