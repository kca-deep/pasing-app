"""
Table integration service.

Handles integration of Camelot tables into Docling content and table conversion.
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def integrate_camelot_tables_into_content(markdown_content: str, table_extractions: list, docling_doc) -> str:
    """
    Replace Docling tables with Camelot tables in Markdown content.

    This function matches Docling tables with Camelot tables by page number
    and replaces them in the final Markdown output for higher accuracy.

    Args:
        markdown_content: Original Markdown content from Docling (with tables)
        table_extractions: List of TableExtraction objects from Camelot
        docling_doc: DoclingDocument for accessing Docling table information

    Returns:
        Modified Markdown content with Docling tables replaced by Camelot tables
    """
    if not table_extractions or not docling_doc:
        return markdown_content

    # Build map of Camelot tables by page
    camelot_by_page = {}
    for extraction in table_extractions:
        page = extraction.page
        if page not in camelot_by_page:
            camelot_by_page[page] = []
        camelot_by_page[page].append(extraction)

    # Build replacement map: Docling table markdown -> Camelot table markdown
    replacements = []

    for table_idx, table_item in enumerate(docling_doc.tables):
        # Get page number from Docling table
        docling_page = None
        try:
            if table_item.prov and len(table_item.prov) > 0:
                docling_page = table_item.prov[0].page_no
        except Exception:
            pass

        if docling_page is None:
            continue

        # Find matching Camelot table on the same page
        if docling_page not in camelot_by_page:
            continue

        camelot_tables = camelot_by_page[docling_page]
        if table_idx >= len(camelot_tables):
            # No more Camelot tables on this page
            continue

        camelot_extraction = camelot_tables[0]  # Use first table on this page
        camelot_by_page[docling_page].pop(0)  # Remove from list

        # Get Docling table markdown
        try:
            docling_table_md = table_item.export_to_markdown(docling_doc).strip()
        except Exception as e:
            logger.warning(f"Failed to export Docling table {table_idx}: {e}")
            continue

        # Get Camelot table markdown
        try:
            camelot_table_md = structure_to_markdown_table(camelot_extraction.structure).strip()
        except Exception as e:
            logger.warning(f"Failed to convert Camelot table to markdown: {e}")
            continue

        # Store replacement
        replacements.append((docling_table_md, camelot_table_md))

    # Apply replacements
    modified_content = markdown_content
    for docling_md, camelot_md in replacements:
        # Replace first occurrence only (to handle duplicate tables)
        modified_content = modified_content.replace(docling_md, camelot_md, 1)

    return modified_content


def structure_to_markdown_table(structure: dict) -> str:
    """
    Convert TableExtraction structure to Markdown table format.

    Args:
        structure: Table structure dictionary with 'all_rows' key

    Returns:
        Markdown table string
    """
    if not structure or 'all_rows' not in structure or not structure['all_rows']:
        return "_Empty table_"

    all_rows = structure['all_rows']
    if len(all_rows) == 0:
        return "_Empty table_"

    # Build Markdown table
    md_lines = []

    # Determine if first row is header
    has_header = structure.get('has_header', True)

    for row_idx, row_data in enumerate(all_rows):
        cells = row_data.get('cells', [])
        cell_texts = [cell.get('text', '') for cell in cells]

        # Replace newlines with spaces (for cells with line breaks)
        cell_texts = [text.replace('\n', ' ').replace('\r', ' ') for text in cell_texts]

        # Escape pipe characters in cell text
        cell_texts = [text.replace('|', '\\|') for text in cell_texts]

        # Add row
        md_lines.append("| " + " | ".join(cell_texts) + " |")

        # Add separator after first row if it's a header
        if row_idx == 0 and has_header:
            md_lines.append("|" + "|".join(["---" for _ in cells]) + "|")

    return "\n".join(md_lines)
