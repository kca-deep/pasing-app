# Custom Serializers for Markdown + HTML混合 출력
# 표만 HTML로, 나머지는 Markdown으로 출력

from typing import Any
from docling_core.transforms.serializer.base import BaseTableSerializer, SerializationResult
from docling_core.transforms.serializer.common import create_ser_result
from docling_core.types.doc.document import TableItem, DoclingDocument


class HTMLTableSerializer(BaseTableSerializer):
    """
    Custom table serializer that outputs tables as HTML
    while other content remains in Markdown format.

    This is useful for RAG systems that need structured table data
    preserved in HTML while keeping the rest of the document in Markdown.
    """

    def serialize(
        self,
        *,
        item: TableItem,
        doc: DoclingDocument,
        **kwargs: Any,
    ) -> SerializationResult:
        """
        Serialize a table item to HTML format.

        Args:
            item: The table item to serialize
            doc: The parent DoclingDocument
            **kwargs: Additional serialization options

        Returns:
            SerializationResult with HTML table content
        """
        # Use TableItem's built-in export_to_html method
        html_content = item.export_to_html(doc=doc, add_caption=True)

        # Create serialization result
        return create_ser_result(text=html_content, span_source=item)
