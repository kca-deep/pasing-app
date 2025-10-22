"""
pdfplumber-based table extraction with coordinate-based text ordering.

This module provides a fallback solution for PDFs where Camelot's text extraction
produces incorrect ordering (e.g., parentheses and weekday names separated).

Strategy:
- Use text coordinates to ensure correct reading order
- Focus on text-based alignment rather than line detection
- Suitable for borderless tables and complex text layouts

Key difference from Camelot:
- Camelot: Relies on PDFMiner's text extraction order (can be wrong)
- pdfplumber: Uses (x, y) coordinates to reconstruct proper order

Author: Implementation based on Context7 pdfplumber documentation
"""

from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
import logging
from dataclasses import dataclass
import pandas as pd
import warnings

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PdfPlumberTableExtraction:
    """Extracted table from pdfplumber with metadata"""
    table_id: str
    page: int
    dataframe: pd.DataFrame
    accuracy: float  # Estimated accuracy (always 1.0 for pdfplumber)
    parsing_report: Dict
    extraction_mode: str  # "pdfplumber"

    # Geometry information
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)

    def to_dict(self) -> Dict:
        """Convert to dictionary format (compatible with Camelot)"""
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


def extract_tables_with_pdfplumber(
    pdf_path: Path,
    pages: str = 'all',
    table_bbox: Optional[Tuple[float, float, float, float]] = None,
    **kwargs
) -> Tuple[List[PdfPlumberTableExtraction], Set[int]]:
    """
    Extract tables using pdfplumber with coordinate-based text ordering.

    This is a fallback method when Camelot produces incorrect text order.

    Args:
        pdf_path: Path to PDF file
        pages: Pages to process (default: 'all')
        table_bbox: Optional bounding box to focus on specific region
        **kwargs: Additional pdfplumber parameters

    Returns:
        Tuple of (extracted_tables, successful_pages)

    Example:
        >>> tables, pages = extract_tables_with_pdfplumber("sample.pdf")
        >>> for table in tables:
        ...     print(table.dataframe)
    """
    if not PDFPLUMBER_AVAILABLE:
        logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
        return [], set()

    # Default pdfplumber settings for coordinate-based text alignment
    table_settings = {
        'vertical_strategy': 'text',      # Use text coordinates for columns
        'horizontal_strategy': 'text',    # Use text coordinates for rows
        'text_tolerance': 3,              # Text alignment tolerance
        'intersection_tolerance': 5,      # Intersection detection tolerance
        'snap_tolerance': 3,              # Snap edges to alignment
        'join_tolerance': 3,              # Join nearby edges
        'edge_min_length': 3,             # Minimum edge length
        **kwargs
    }

    try:
        # Parse pages parameter
        if pages == 'all':
            page_nums = None  # Extract from all pages
        else:
            # Parse "1,3-5,7" format
            page_nums = []
            for part in pages.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    page_nums.extend(range(start - 1, end))  # pdfplumber uses 0-based indexing
                else:
                    page_nums.append(int(part) - 1)

        extractions = []
        successful_pages = set()

        # Open PDF with pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages_to_process = pdf.pages if page_nums is None else [pdf.pages[i] for i in page_nums]

            # Progress bar if available
            if TQDM_AVAILABLE:
                desc = f"🔄 pdfplumber: {pdf_path.name}"
                pages_iter = tqdm(pages_to_process, desc=desc, unit="page", leave=False)
            else:
                pages_iter = pages_to_process

            for page_idx, page in enumerate(pages_iter):
                page_num = page.page_number

                # Crop to specific region if bbox provided
                if table_bbox:
                    page = page.crop(table_bbox)

                # Extract all tables on the page
                try:
                    tables = page.extract_tables(table_settings)

                    if not tables:
                        continue

                    # Process each table
                    for table_idx, table_data in enumerate(tables):
                        if not table_data or len(table_data) < 2:
                            continue

                        table_id = f"table_{len(extractions)+1:03d}"

                        # Convert to DataFrame
                        # First row as header (if looks like header)
                        df = pd.DataFrame(table_data[1:], columns=table_data[0])

                        # Clean empty columns and rows
                        df = df.dropna(how='all', axis=1)  # Remove all-empty columns
                        df = df.dropna(how='all', axis=0)  # Remove all-empty rows

                        if df.empty:
                            continue

                        # Estimate bounding box (approximate)
                        bbox = (0, 0, page.width, page.height)  # Full page for now

                        # Create extraction object
                        extraction = PdfPlumberTableExtraction(
                            table_id=table_id,
                            page=page_num,
                            dataframe=df,
                            accuracy=1.0,  # pdfplumber doesn't provide accuracy score
                            parsing_report={
                                "extraction_method": "pdfplumber",
                                "table_settings": table_settings,
                                "shape": {"rows": len(df), "cols": len(df.columns)}
                            },
                            extraction_mode="pdfplumber",
                            bbox=bbox
                        )

                        extractions.append(extraction)
                        successful_pages.add(page_num)

                        if TQDM_AVAILABLE:
                            pages_iter.set_postfix({"tables": len(extractions)})

                except Exception as e:
                    logger.warning(f"Failed to extract tables from page {page_num}: {e}")
                    continue

        logger.info(f"✅ pdfplumber: {len(extractions)} tables on {len(successful_pages)} pages")
        return extractions, successful_pages

    except Exception as e:
        logger.error(f"❌ pdfplumber extraction failed: {str(e)}")
        return [], set()


def extract_table_from_region(
    pdf_path: Path,
    page_num: int,
    bbox: Tuple[float, float, float, float],
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Extract a single table from a specific region of a PDF page.

    This is useful for re-extracting a specific table identified by Camelot
    but with incorrect text order.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-based)
        bbox: Bounding box (x1, y1, x2, y2) in PDF coordinates
        **kwargs: Additional pdfplumber parameters

    Returns:
        DataFrame or None if extraction fails

    Example:
        >>> df = extract_table_from_region("sample.pdf", 1, (100, 200, 500, 600))
    """
    if not PDFPLUMBER_AVAILABLE:
        return None

    table_settings = {
        'vertical_strategy': 'text',
        'horizontal_strategy': 'text',
        'text_tolerance': 3,
        'intersection_tolerance': 5,
        **kwargs
    }

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            page = pdf.pages[page_num - 1]  # Convert to 0-based

            # Crop to the specified region
            cropped = page.crop(bbox)

            # Extract table
            table = cropped.extract_table(table_settings)

            if table and len(table) >= 2:
                # Convert to DataFrame
                df = pd.DataFrame(table[1:], columns=table[0])
                df = df.dropna(how='all', axis=1)
                df = df.dropna(how='all', axis=0)

                return df if not df.empty else None

        return None

    except Exception as e:
        logger.warning(f"Failed to extract table from region: {e}")
        return None


def validate_pdfplumber_available() -> bool:
    """
    Check if pdfplumber is available.

    Returns:
        True if pdfplumber is installed, False otherwise
    """
    return PDFPLUMBER_AVAILABLE


if __name__ == "__main__":
    # Test code
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdfplumber_extractor.py <pdf_path>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Extracting tables from {pdf_path.name} using pdfplumber...")
    tables, pages = extract_tables_with_pdfplumber(pdf_path)

    print(f"\nExtracted {len(tables)} tables from {len(pages)} pages")

    for table in tables:
        print(f"\n{table.table_id} (Page {table.page}):")
        print(table.dataframe.head())
