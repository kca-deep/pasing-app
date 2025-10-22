"""
Picture processing service.

Handles image classification, VLM filtering, and picture information extraction.
"""

import logging
from docling_core.types.doc.document import PictureItem, PictureDescriptionData, PictureClassificationData

logger = logging.getLogger(__name__)


def classify_image_type(picture: PictureItem) -> str:
    """
    Classify image type based on PictureClassificationData.

    Returns:
        - "text": Text-heavy images (tables, forms, documents) - Use OCR only
        - "visualization": Charts, graphs, diagrams - Use VLM description
        - "mixed": Complex images - Use both OCR + VLM
        - "unknown": No classification available
    """
    if not hasattr(picture, 'annotations') or not picture.annotations:
        return "unknown"

    # Find classification annotation
    for annotation in picture.annotations:
        if isinstance(annotation, PictureClassificationData):
            if not annotation.predicted_classes:
                continue

            # Get top prediction
            top_prediction = annotation.predicted_classes[0]
            class_name = top_prediction.class_name.lower()

            # Text-heavy categories (OCR is sufficient)
            text_categories = [
                "table", "form", "document", "text",
                "formula", "equation", "code"
            ]

            # Visualization categories (VLM description needed)
            viz_categories = [
                "chart", "graph", "plot", "diagram",
                "naturalimage", "photograph", "illustration",
                "architecture", "flowchart", "map"
            ]

            # Check category
            if any(cat in class_name for cat in text_categories):
                return "text"
            elif any(cat in class_name for cat in viz_categories):
                return "visualization"
            else:
                return "mixed"

    return "unknown"


def filter_picture_descriptions_smart(docling_doc, auto_mode: bool = False):
    """
    Smart filtering of picture descriptions based on image classification.

    When auto_image_analysis is enabled:
    - Text-heavy images (tables, forms) → Remove VLM descriptions (OCR only)
    - Visualizations (charts, graphs) → Keep VLM descriptions
    - Complex/Unknown images → Keep both OCR + VLM

    Args:
        docling_doc: DoclingDocument object
        auto_mode: Whether auto_image_analysis mode is enabled

    Returns:
        Modified DoclingDocument with filtered descriptions
    """
    if not auto_mode or not docling_doc:
        return docling_doc

    removed_count = 0
    kept_count = 0

    for picture in docling_doc.pictures:
        image_type = classify_image_type(picture)

        # For text-heavy images, remove VLM descriptions (OCR is sufficient)
        if image_type == "text":
            if hasattr(picture, 'annotations'):
                # Remove PictureDescriptionData annotations
                original_count = len(picture.annotations)
                picture.annotations = [
                    ann for ann in picture.annotations
                    if not isinstance(ann, PictureDescriptionData)
                ]
                removed = original_count - len(picture.annotations)
                if removed > 0:
                    removed_count += 1
                    logger.debug(f"    Removed VLM description for text-heavy image: {picture.self_ref}")

        # For visualizations and complex images, keep VLM descriptions
        elif image_type in ["visualization", "mixed", "unknown"]:
            kept_count += 1

    if removed_count > 0 or kept_count > 0:
        logger.info(f"    Smart Filter: Removed {removed_count} text-image VLM descriptions, kept {kept_count} visualization descriptions")

    return docling_doc


def extract_pictures_info(docling_doc, include_classification: bool = False) -> dict:
    """
    Extract picture information from DoclingDocument.

    Args:
        docling_doc: DoclingDocument object
        include_classification: Include image classification info

    Returns:
        Dictionary with pictures summary:
        - total_pictures: Total number of pictures
        - pictures_with_descriptions: Number of pictures with VLM descriptions
        - pictures: List of picture information (ref, caption, descriptions, classification)
    """
    if not docling_doc:
        return {
            "total_pictures": 0,
            "pictures_with_descriptions": 0,
            "pictures": []
        }

    pictures_info = []
    pictures_with_descriptions = 0
    classification_stats = {
        "text": 0,
        "visualization": 0,
        "mixed": 0,
        "unknown": 0
    }

    for picture in docling_doc.pictures:
        # Extract basic info
        picture_data = {
            "ref": picture.self_ref if hasattr(picture, 'self_ref') else None,
            "caption": None,
            "descriptions": [],
            "classification": None
        }

        # Extract caption
        try:
            caption_text = picture.caption_text(doc=docling_doc)
            if caption_text:
                picture_data["caption"] = caption_text
        except Exception:
            pass

        # Extract image classification
        if include_classification:
            image_type = classify_image_type(picture)
            classification_stats[image_type] += 1

            # Extract detailed classification
            if hasattr(picture, 'annotations'):
                for annotation in picture.annotations:
                    if isinstance(annotation, PictureClassificationData):
                        if annotation.predicted_classes:
                            top_class = annotation.predicted_classes[0]
                            picture_data["classification"] = {
                                "type": image_type,
                                "class_name": top_class.class_name,
                                "confidence": top_class.confidence if hasattr(top_class, 'confidence') else None
                            }
                        break

        # Extract VLM descriptions from annotations
        if hasattr(picture, 'annotations'):
            for annotation in picture.annotations:
                if isinstance(annotation, PictureDescriptionData):
                    picture_data["descriptions"].append({
                        "provenance": annotation.provenance if hasattr(annotation, 'provenance') else "unknown",
                        "text": annotation.text if hasattr(annotation, 'text') else ""
                    })

        if picture_data["descriptions"]:
            pictures_with_descriptions += 1

        pictures_info.append(picture_data)

    result = {
        "total_pictures": len(pictures_info),
        "pictures_with_descriptions": pictures_with_descriptions,
        "pictures": pictures_info
    }

    # Add classification stats if enabled
    if include_classification:
        result["classification_stats"] = classification_stats

    return result
