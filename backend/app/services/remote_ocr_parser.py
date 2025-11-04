"""
Remote OCR Parser
원격 OCR 서비스를 사용한 문서 파싱 (이미지/스캔된 PDF 전용)

이 파서는 Docling 대신 직접 원격 OCR 서비스를 호출합니다.
특히 한글 문서나 스캔된 PDF에 효과적입니다.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import logging
import os
from PIL import Image
import fitz  # PyMuPDF

from app.services.remote_ocr import (
    ocr_extract,
    ocr_extract_from_pil,
    REMOTE_OCR_AVAILABLE,
    DEFAULT_OCR_LANGUAGES
)

logger = logging.getLogger(__name__)

# Import standardized logging utility
from app.utils.logging_utils import ParserLogger

# PDF 렌더링 DPI 설정
PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "300"))


def parse_with_remote_ocr(
    file_path: Path,
    ocr_engine: str = "paddleocr",
    ocr_languages: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    progress_callback: Optional[callable] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    원격 OCR 서비스로 문서 파싱 (이미지 및 스캔된 PDF)

    Args:
        file_path: 문서 파일 경로 (PDF, PNG, JPG 등)
        ocr_engine: OCR 엔진 ("tesseract", "paddleocr", "dolphin")
        ocr_languages: 인식할 언어 리스트 (기본: ["kor", "eng"])
        output_dir: 출력 디렉토리 (옵션)

    Returns:
        (content, metadata) 튜플
        - content: 추출된 텍스트 (Markdown 형식)
        - metadata: 파싱 메타데이터

    Raises:
        Exception: OCR 서버 연결 실패 또는 처리 오류
    """
    if not REMOTE_OCR_AVAILABLE:
        raise Exception(
            "Remote OCR Server not available. Please check:\n"
            "1. OCR server is running at http://kca-ai.kro.kr:8005\n"
            "2. Network connection is available"
        )

    if ocr_languages is None:
        ocr_languages = DEFAULT_OCR_LANGUAGES

    # Initialize standardized logger
    parser_logger = ParserLogger("Remote OCR", logger)

    # Log parser start with configuration
    parser_logger.start(
        file_path.name,
        engine=ocr_engine,
        languages=', '.join(ocr_languages)
    )

    try:
        file_extension = file_path.suffix.lower()

        # PDF 처리
        if file_extension == '.pdf':
            content, metadata = _parse_pdf_with_remote_ocr(
                file_path, ocr_engine, ocr_languages, parser_logger, progress_callback
            )
        # 이미지 파일 처리 (PNG, JPG, JPEG, TIFF, BMP)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp']:
            content, metadata = _parse_image_with_remote_ocr(
                file_path, ocr_engine, ocr_languages, parser_logger, progress_callback
            )
        else:
            raise Exception(
                f"Unsupported file type: {file_extension}\n"
                "Remote OCR parser supports: PDF, PNG, JPG, TIFF, BMP"
            )

        # 결과 저장 (옵션)
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "content.md"
            output_file.write_text(content, encoding="utf-8")
            parser_logger.sub_step(f"Saved to {output_file}", emoji='save')

        parser_logger.success(
            "Parsing complete",
            engine=ocr_engine,
            pages=metadata.get('pages', 1),
            characters=len(content)
        )

        return content, metadata

    except Exception as e:
        parser_logger.error(f"Remote OCR parsing failed: {str(e)}", exc_info=True)
        raise


def _parse_pdf_with_remote_ocr(
    pdf_path: Path,
    ocr_engine: str,
    ocr_languages: List[str],
    parser_logger: 'ParserLogger',
    progress_callback: Optional[callable] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    PDF를 페이지별로 이미지로 변환하고 원격 OCR 처리

    Args:
        pdf_path: PDF 파일 경로
        ocr_engine: OCR 엔진
        ocr_languages: 언어 리스트
        parser_logger: ParserLogger instance for standardized logging
        progress_callback: Optional progress callback function

    Returns:
        (content, metadata) 튜플
    """
    try:
        # PDF 열기
        pdf_document = fitz.open(str(pdf_path))
        num_pages = len(pdf_document)

        parser_logger.step(1, 2, f"Converting PDF to images...")
        parser_logger.detail(f"Pages: {num_pages}", last=True)

        if progress_callback:
            progress_callback(20, f"Converting PDF ({num_pages} pages) to images...")

        all_page_contents = []

        # 페이지별 처리
        for page_num in range(num_pages):
            parser_logger.page(page_num + 1, num_pages)

            # Progress update
            if progress_callback:
                current_progress = 20 + int((page_num / num_pages) * 70)  # 20-90%
                progress_callback(current_progress, f"OCR processing page {page_num + 1}/{num_pages}...")

            page = pdf_document[page_num]

            # 페이지를 이미지로 렌더링 (환경변수에서 설정한 DPI 사용)
            mat = fitz.Matrix(PDF_RENDER_DPI / 72, PDF_RENDER_DPI / 72)  # 72 DPI → PDF_RENDER_DPI
            pix = page.get_pixmap(matrix=mat)

            # PIL Image로 변환
            img_data = pix.tobytes("png")
            from io import BytesIO
            pil_image = Image.open(BytesIO(img_data))

            # 원격 OCR 호출
            parser_logger.remote_call("Remote OCR", f"Page {page_num + 1}")
            page_text = ocr_extract_from_pil(
                pil_image,
                engine=ocr_engine,
                languages=ocr_languages
            )

            if page_text.strip():
                all_page_contents.append(page_text)
                parser_logger.detail(f"Extracted {len(page_text)} characters")
            else:
                parser_logger.warning(f"No text extracted from page {page_num + 1}")

        pdf_document.close()

        # 페이지 구분자로 통합
        parser_logger.step(2, 2, "Merging all pages...")
        content = "\n\n---\n\n".join(all_page_contents)
        parser_logger.detail(f"Total characters: {len(content)}", last=True)

        # 메타데이터
        metadata = {
            "pages": num_pages,
            "parser_used": "remote_ocr",
            "ocr_engine": f"remote-{ocr_engine}",
            "ocr_languages": ocr_languages,
            "characters_extracted": len(content)
        }

        return content, metadata

    except Exception as e:
        raise Exception(f"PDF parsing failed: {str(e)}")


def _parse_image_with_remote_ocr(
    image_path: Path,
    ocr_engine: str,
    ocr_languages: List[str],
    parser_logger: 'ParserLogger',
    progress_callback: Optional[callable] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    이미지 파일을 원격 OCR로 처리

    Args:
        image_path: 이미지 파일 경로
        ocr_engine: OCR 엔진
        ocr_languages: 언어 리스트
        parser_logger: ParserLogger instance for standardized logging
        progress_callback: Optional progress callback function

    Returns:
        (content, metadata) 튜플
    """
    parser_logger.step(1, 1, "Processing image file...")

    try:
        if progress_callback:
            progress_callback(30, "Processing image with Remote OCR...")

        # 원격 OCR 호출 (파일 경로로 직접)
        parser_logger.remote_call("Remote OCR", "Image processing")
        text = ocr_extract(
            str(image_path),
            engine=ocr_engine,
            languages=ocr_languages
        )

        parser_logger.detail(f"Extracted {len(text)} characters", last=True)

        if progress_callback:
            progress_callback(80, "Finalizing OCR results...")

        # 메타데이터
        metadata = {
            "pages": 1,
            "parser_used": "remote_ocr",
            "ocr_engine": f"remote-{ocr_engine}",
            "ocr_languages": ocr_languages,
            "characters_extracted": len(text)
        }

        return text, metadata

    except Exception as e:
        raise Exception(f"Image parsing failed: {str(e)}")


def check_remote_ocr_parser_availability() -> Dict[str, Any]:
    """
    원격 OCR 파서 사용 가능 여부 확인

    Returns:
        사용 가능 여부 및 정보
    """
    from app.services.remote_ocr import check_remote_ocr_availability

    ocr_status = check_remote_ocr_availability()

    return {
        "available": ocr_status["available"],
        "parser": "remote_ocr",
        "ocr_server": ocr_status.get("server_url"),
        "engines": ocr_status.get("engines", []),
        "supported_formats": ["PDF", "PNG", "JPG", "JPEG", "TIFF", "BMP"],
        "features": {
            "multi_page_pdf": True,
            "scanned_documents": True,
            "korean_support": True,
            "high_accuracy": True  # paddleocr 또는 dolphin 사용 시
        }
    }
