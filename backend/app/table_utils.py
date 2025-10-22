"""
Table extraction and complexity assessment utilities for RAG-optimized document parsing.
Implements Phase 3 of the integrated-rag-parsing-implementation-plan.md

Supports two extraction modes:
1. Docling-based extraction (default)
2. Camelot-based extraction (high accuracy, PDF only)
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import json
from dataclasses import dataclass, asdict
import logging

# Docling imports
from docling_core.types.doc.document import DoclingDocument, TableItem, TableData

# Camelot imports (optional)
try:
    from .camelot_extractor import (
        extract_tables_hybrid,
        CamelotTableExtraction,
        save_camelot_extractions
    )
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TableComplexity:
    """Table complexity metadata"""
    rows: int
    cols: int
    has_merged_cells: bool
    is_complex: bool


@dataclass
class TableExtraction:
    """Extracted table with metadata"""
    table_id: str
    chunk_id: Optional[str]
    page: Optional[int]
    caption: Optional[str]
    complexity: TableComplexity
    structure: Dict[str, Any]  # headers, rows
    is_complex: bool  # Convenience field


def is_complex_table(table_data: TableData, threshold: int = 4) -> Tuple[bool, TableComplexity]:
    """
    Determine if a table is complex based on size and merged cells.

    Args:
        table_data: TableData object from Docling
        threshold: Size threshold (default: 4x4)

    Returns:
        Tuple of (is_complex, TableComplexity)

    Complexity criteria:
    - Size check: rows >= threshold OR cols >= threshold
    - Merged cells check: any cell has rowspan > 1 or colspan > 1
    """
    num_rows = table_data.num_rows
    num_cols = table_data.num_cols

    # Size check
    size_complex = num_rows >= threshold or num_cols >= threshold

    # Merged cells check
    has_merged = False
    try:
        # Check grid for merged cells (cells with row_span > 1 or col_span > 1)
        for row in table_data.grid:
            for cell in row:
                # Check if cell has span attributes
                if hasattr(cell, 'row_span') and cell.row_span > 1:
                    has_merged = True
                    break
                if hasattr(cell, 'col_span') and cell.col_span > 1:
                    has_merged = True
                    break
            if has_merged:
                break
    except Exception:
        # If grid inspection fails, assume no merged cells
        pass

    is_complex = size_complex or has_merged

    complexity = TableComplexity(
        rows=num_rows,
        cols=num_cols,
        has_merged_cells=has_merged,
        is_complex=is_complex
    )

    return is_complex, complexity


def extract_table_structure(table_item: TableItem, doc: DoclingDocument, assume_header: bool = None) -> Dict[str, Any]:
    """
    Extract table structure from TableItem without hardcoded assumptions.

    Args:
        table_item: TableItem from Docling document
        doc: DoclingDocument for context
        assume_header: If True, treat first row as header. If None (default), auto-detect.

    Returns:
        Dictionary with all rows in uniform format, plus metadata
    """
    structure = {
        "all_rows": [],      # All rows in uniform format
        "has_header": False,  # Whether header was detected/assumed
        "header_row_index": None,  # Index of header row (if any)
        "num_rows": 0,
        "num_cols": 0
    }

    try:
        # Get table data
        table_data = table_item.data

        # Safety check
        if not hasattr(table_data, 'grid') or not table_data.grid:
            # Fallback: try to export as DataFrame or Markdown
            try:
                structure["fallback"] = "No grid available, using export methods"
                structure["markdown"] = table_item.export_to_markdown(doc)
                return structure
            except Exception:
                structure["error"] = "Unable to extract table structure"
                return structure

        structure["num_rows"] = table_data.num_rows
        structure["num_cols"] = table_data.num_cols

        # Extract ALL rows uniformly (no header assumption)
        for row_idx, row in enumerate(table_data.grid):
            row_data = {
                "row_index": row_idx,
                "cells": []
            }

            for col_idx, cell in enumerate(row):
                cell_data = {
                    "col_index": col_idx,
                    "text": str(cell.text) if hasattr(cell, 'text') else str(cell),
                    "row_span": getattr(cell, 'row_span', 1),
                    "col_span": getattr(cell, 'col_span', 1)
                }
                row_data["cells"].append(cell_data)

            structure["all_rows"].append(row_data)

        # Auto-detect or use assumption for header
        if assume_header is None:
            # Auto-detect: simple heuristic - if first row has different formatting
            # or if table has at least 2 rows
            structure["has_header"] = table_data.num_rows >= 2
            structure["header_row_index"] = 0 if structure["has_header"] else None
        else:
            structure["has_header"] = assume_header
            structure["header_row_index"] = 0 if assume_header else None

    except Exception as e:
        # Fallback: use export_to_markdown or export_to_html
        structure["error"] = str(e)
        structure["fallback"] = "Unable to extract detailed structure"
        try:
            structure["markdown"] = table_item.export_to_markdown(doc)
        except Exception:
            pass

    return structure


def extract_tables_from_document(
    doc: DoclingDocument,
    output_dir: Path,
    doc_name: str,
    complexity_threshold: int = 4,
    assume_header: Optional[bool] = None
) -> Tuple[List[TableExtraction], Dict[str, Any]]:
    """
    Extract all tables from a Docling document and save complex tables as JSON.

    Flexible extraction without hardcoded assumptions about document structure.

    Args:
        doc: DoclingDocument from Docling conversion
        output_dir: Output directory for the document (e.g., output/sample/)
        doc_name: Document name (without extension)
        complexity_threshold: Size threshold for complexity (default: 4)
        assume_header: None = auto-detect, True = first row is header, False = no header

    Returns:
        Tuple of (table_extractions, table_summary)
    """
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    table_extractions = []
    markdown_count = 0
    json_count = 0
    json_table_ids = []

    # Extract tables
    for idx, table_item in enumerate(doc.tables):
        table_id = f"table_{idx+1:03d}"

        # Get table caption (optional - document may not have captions)
        caption = None
        try:
            caption = table_item.caption_text(doc) if hasattr(table_item, 'caption_text') else None
        except Exception:
            pass

        # Get page number (optional - may not have provenance)
        page = None
        try:
            if table_item.prov and len(table_item.prov) > 0:
                page = table_item.prov[0].page_no
        except Exception:
            pass

        # Assess complexity
        table_data = table_item.data
        is_complex, complexity = is_complex_table(table_data, complexity_threshold)

        # Extract structure (flexible, no hardcoded assumptions)
        structure = extract_table_structure(table_item, doc, assume_header=assume_header)

        # Create extraction object
        extraction = TableExtraction(
            table_id=table_id,
            chunk_id=None,  # Will be assigned during chunking (Phase 4)
            page=page,
            caption=caption,
            complexity=complexity,
            structure=structure,
            is_complex=is_complex
        )

        table_extractions.append(extraction)

        # Save complex tables as JSON
        if is_complex:
            json_count += 1
            json_table_ids.append(table_id)

            json_path = tables_dir / f"{table_id}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(extraction), f, ensure_ascii=False, indent=2)
        else:
            markdown_count += 1

    # Create table summary
    table_summary = {
        "total_tables": len(table_extractions),
        "markdown_tables": markdown_count,
        "json_tables": json_count,
        "json_table_ids": json_table_ids
    }

    return table_extractions, table_summary


def table_to_markdown(table_item: TableItem, doc: Optional[DoclingDocument] = None) -> str:
    """
    Convert a simple table to Markdown format.

    Args:
        table_item: TableItem from Docling
        doc: Optional DoclingDocument for context

    Returns:
        Markdown string
    """
    try:
        # Use Docling's built-in export_to_markdown method
        return table_item.export_to_markdown(doc)
    except Exception:
        # Fallback: manual markdown generation
        table_data = table_item.data
        md_lines = []

        # Headers
        if table_data.num_rows > 0:
            headers = [cell.text if hasattr(cell, 'text') else str(cell) for cell in table_data.grid[0]]
            md_lines.append("| " + " | ".join(headers) + " |")
            md_lines.append("|" + "|".join(["---" for _ in headers]) + "|")

            # Rows
            for row_idx in range(1, table_data.num_rows):
                row = table_data.grid[row_idx]
                row_text = [cell.text if hasattr(cell, 'text') else str(cell) for cell in row]
                md_lines.append("| " + " | ".join(row_text) + " |")

        return "\n".join(md_lines)


def create_table_reference_markdown(table_id: str, caption: Optional[str] = None) -> str:
    """
    Create a Markdown reference for a complex table stored as JSON.

    Args:
        table_id: Table ID (e.g., "table_001")
        caption: Optional table caption

    Returns:
        Markdown reference string
    """
    ref = f"> **Table {table_id.split('_')[1]}**"
    if caption:
        ref += f": {caption}"
    ref += f" (see `tables/{table_id}.json`)"
    return ref


def extract_tables_with_camelot(
    pdf_path: Path,
    output_dir: Path,
    doc_name: str,
    complexity_threshold: int = 4,
    mode: str = 'hybrid',
    pages: str = 'all',
    lattice_accuracy_threshold: float = 0.7,
    **kwargs
) -> Tuple[List[TableExtraction], Dict[str, Any]]:
    """
    Extract tables from PDF using Camelot library (high accuracy).

    This function uses Camelot's hybrid LATTICE + STREAM strategy for maximum accuracy.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for the document (e.g., output/sample/)
        doc_name: Document name (without extension)
        complexity_threshold: Size threshold for complexity (default: 4)
        mode: Extraction mode ('lattice', 'stream', 'hybrid')
        pages: Pages to process (default: 'all')
        lattice_accuracy_threshold: Minimum accuracy for LATTICE (default: 0.7)
        **kwargs: Additional Camelot parameters

    Returns:
        Tuple of (table_extractions, table_summary)

    Note:
        - Only works with PDF files
        - Requires camelot-py[cv] to be installed
        - Returns empty list if Camelot is not available
    """
    if not CAMELOT_AVAILABLE:
        logger.warning("⚠️ Camelot not available. Install with: pip install camelot-py[cv]")
        return [], {"error": "Camelot not installed"}

    if not pdf_path.suffix.lower() == '.pdf':
        logger.warning(f"⚠️ Camelot only works with PDF files, got: {pdf_path.suffix}")
        return [], {"error": "Camelot requires PDF input"}

    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract tables using Camelot hybrid strategy
        logger.info(f"🚀 Extracting tables with Camelot ({mode} mode) from {pdf_path}")

        if mode == 'hybrid':
            camelot_extractions, extraction_summary = extract_tables_hybrid(
                pdf_path,
                pages=pages,
                lattice_accuracy_threshold=lattice_accuracy_threshold,
                **kwargs
            )
        else:
            # Use single mode (lattice or stream)
            from .camelot_extractor import quick_extract
            camelot_extractions = quick_extract(pdf_path, mode=mode, pages=pages, **kwargs)
            extraction_summary = {
                "total_tables": len(camelot_extractions),
                "mode": mode
            }

        # Convert Camelot extractions to TableExtraction format
        table_extractions = []
        markdown_count = 0
        json_count = 0
        json_table_ids = []

        for camelot_table in camelot_extractions:
            # Assess complexity based on DataFrame shape
            rows = len(camelot_table.dataframe)
            cols = len(camelot_table.dataframe.columns)
            is_complex = rows >= complexity_threshold or cols >= complexity_threshold

            # Create TableComplexity
            complexity = TableComplexity(
                rows=rows,
                cols=cols,
                has_merged_cells=False,  # Camelot doesn't detect merged cells explicitly
                is_complex=is_complex
            )

            # Convert DataFrame to structure format
            structure = {
                "all_rows": [],
                "has_header": True,  # Assume first row is header
                "header_row_index": 0,
                "num_rows": rows,
                "num_cols": cols,
                "camelot_metadata": {
                    "accuracy": camelot_table.accuracy,
                    "extraction_mode": camelot_table.extraction_mode,
                    "bbox": camelot_table.bbox
                }
            }

            # Convert DataFrame to rows format
            for row_idx, row in camelot_table.dataframe.iterrows():
                row_data = {
                    "row_index": row_idx,
                    "cells": []
                }
                for col_idx, col_name in enumerate(camelot_table.dataframe.columns):
                    cell_data = {
                        "col_index": col_idx,
                        "text": str(row[col_name]),
                        "row_span": 1,
                        "col_span": 1
                    }
                    row_data["cells"].append(cell_data)
                structure["all_rows"].append(row_data)

            # Create TableExtraction
            extraction = TableExtraction(
                table_id=camelot_table.table_id,
                chunk_id=None,
                page=camelot_table.page,
                caption=None,  # Camelot doesn't extract captions
                complexity=complexity,
                structure=structure,
                is_complex=is_complex
            )

            table_extractions.append(extraction)

            # Save complex tables as JSON
            if is_complex:
                json_count += 1
                json_table_ids.append(camelot_table.table_id)

                json_path = tables_dir / f"{camelot_table.table_id}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(asdict(extraction), f, ensure_ascii=False, indent=2)

                # Also save Camelot-specific formats (CSV, Markdown)
                csv_path = tables_dir / f"{camelot_table.table_id}.csv"
                camelot_table.dataframe.to_csv(csv_path, index=False, encoding='utf-8')

                md_path = tables_dir / f"{camelot_table.table_id}.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(camelot_table.to_markdown())
            else:
                markdown_count += 1

        # Create table summary
        table_summary = {
            "total_tables": len(table_extractions),
            "markdown_tables": markdown_count,
            "json_tables": json_count,
            "json_table_ids": json_table_ids,
            "extraction_method": f"camelot_{mode}",
            "camelot_summary": extraction_summary
        }

        logger.info(f"✅ Camelot extraction complete: {len(table_extractions)} tables extracted")

        return table_extractions, table_summary

    except Exception as e:
        logger.error(f"❌ Camelot extraction failed: {str(e)}", exc_info=True)
        return [], {"error": str(e)}
