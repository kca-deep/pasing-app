"""
Remote OCR Parser (Unified)
원격 OCR 서비스를 사용한 문서 파싱 (통합 모듈)

이 모듈은 remote_ocr.py와 remote_ocr_parser.py를 통합한 것입니다.
- 저수준 OCR 호출 함수
- 고수준 문서 파싱 함수
를 모두 제공합니다.

OCR API 정보:
  - URL: http://kca-ai.kro.kr:8005/ocr/extract
  - 엔진:
    * "tesseract" - 빠름 (~0.2초)
    * "paddleocr" - 정확 (~1.6초) ⭐ 권장
    * "dolphin" - AI 기반 (~5초)

특히 한글 문서나 스캔된 PDF에 효과적입니다.
"""

import requests
import base64
import logging
import os
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from PIL import Image
import io
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Import standardized logging utility
from app.utils.logging_utils import ParserLogger

# ========================================
# Configuration & Constants
# ========================================

# OCR 서버 설정 (환경변수 지원)
REMOTE_OCR_SERVER = os.getenv("REMOTE_OCR_SERVER", "http://kca-ai.kro.kr:8005")
REMOTE_OCR_HEALTH_TIMEOUT = int(os.getenv("REMOTE_OCR_HEALTH_TIMEOUT", "5"))
REMOTE_OCR_REQUEST_TIMEOUT = int(os.getenv("REMOTE_OCR_REQUEST_TIMEOUT", "30"))

# 기본 OCR 언어 설정
DEFAULT_OCR_LANGUAGES = os.getenv("DEFAULT_OCR_LANGUAGES", "eng,kor").split(",")

# PDF 렌더링 DPI 설정
PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "300"))

# 서버 연결 테스트
REMOTE_OCR_AVAILABLE = False
try:
    response = requests.get(f"{REMOTE_OCR_SERVER}/health", timeout=REMOTE_OCR_HEALTH_TIMEOUT)
    if response.status_code == 200:
        REMOTE_OCR_AVAILABLE = True
        logger.info(f"✅ Remote OCR Server connected: {REMOTE_OCR_SERVER}")
    else:
        logger.warning(f"⚠️ Remote OCR Server not healthy: {REMOTE_OCR_SERVER}")
except Exception as e:
    logger.warning(f"⚠️ Remote OCR Server not available: {e}")


# ========================================
# Low-Level OCR Functions (Private)
# ========================================

def _ocr_extract_from_file(
    image_path: str,
    engine: str = "paddleocr",
    languages: Optional[List[str]] = None
) -> str:
    """
    원격 OCR 서비스를 사용하여 이미지 파일에서 텍스트 추출 (내부 함수)

    Args:
        image_path: 이미지 파일 경로
        engine: OCR 엔진 ("tesseract", "paddleocr", "dolphin")
        languages: 인식할 언어 리스트 (기본: ["eng", "kor"])

    Returns:
        추출된 텍스트

    Raises:
        Exception: OCR 서버 연결 실패 또는 처리 오류
    """
    if not REMOTE_OCR_AVAILABLE:
        raise Exception(
            f"Remote OCR Server not available at {REMOTE_OCR_SERVER}\n"
            "Please check:\n"
            "1. OCR server is running\n"
            "2. Network connection is available"
        )

    if languages is None:
        languages = DEFAULT_OCR_LANGUAGES

    try:
        # 이미지를 base64로 인코딩
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        logger.info(f"  🌐 [Remote OCR] Engine: {engine}, Languages: {languages}")

        # OCR API 호출
        response = requests.post(
            f"{REMOTE_OCR_SERVER}/ocr/extract",
            json={
                "image_base64": image_base64,
                "engine": engine,
                "languages": languages
            },
            timeout=REMOTE_OCR_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()

        extracted_text = result.get("text", "")
        logger.info(f"  ✓ [Remote OCR] Extracted {len(extracted_text)} characters")

        return extracted_text

    except requests.exceptions.Timeout:
        raise Exception(f"Remote OCR timeout: {REMOTE_OCR_SERVER}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Remote OCR connection failed: {REMOTE_OCR_SERVER}")
    except Exception as e:
        raise Exception(f"Remote OCR error: {str(e)}")


def _ocr_extract_from_pil_image(
    image: Image.Image,
    engine: str = "paddleocr",
    languages: Optional[List[str]] = None
) -> str:
    """
    PIL Image 객체에서 직접 텍스트 추출 (파일 저장 없이, 내부 함수)

    Args:
        image: PIL Image 객체
        engine: OCR 엔진 ("tesseract", "paddleocr", "dolphin")
        languages: 인식할 언어 리스트

    Returns:
        추출된 텍스트
    """
    if not REMOTE_OCR_AVAILABLE:
        raise Exception(f"Remote OCR Server not available at {REMOTE_OCR_SERVER}")

    if languages is None:
        languages = DEFAULT_OCR_LANGUAGES

    try:
        # PIL Image를 bytes로 변환
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        logger.info(f"  🌐 [Remote OCR] Engine: {engine}, Languages: {languages}")

        # OCR API 호출
        response = requests.post(
            f"{REMOTE_OCR_SERVER}/ocr/extract",
            json={
                "image_base64": image_base64,
                "engine": engine,
                "languages": languages
            },
            timeout=REMOTE_OCR_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()

        extracted_text = result.get("text", "")
        logger.info(f"  ✓ [Remote OCR] Extracted {len(extracted_text)} characters")

        return extracted_text

    except Exception as e:
        logger.error(f"  ✗ [Remote OCR] Error: {str(e)}")
        raise Exception(f"Remote OCR error: {str(e)}")


# ========================================
# Public API Functions (Backward Compatibility)
# ========================================

def ocr_extract(
    image_path: str,
    engine: str = "paddleocr",
    languages: Optional[List[str]] = None
) -> str:
    """
    원격 OCR 서비스를 사용하여 이미지에서 텍스트 추출

    Args:
        image_path: 이미지 파일 경로
        engine: OCR 엔진 ("tesseract", "paddleocr", "dolphin")
        languages: 인식할 언어 리스트 (기본: ["eng", "kor"])

    Returns:
        추출된 텍스트

    Raises:
        Exception: OCR 서버 연결 실패 또는 처리 오류

    Note:
        이 함수는 backward compatibility를 위해 유지됩니다.
        내부적으로 _ocr_extract_from_file()을 호출합니다.
    """
    return _ocr_extract_from_file(image_path, engine, languages)


def ocr_extract_from_pil(
    image: Image.Image,
    engine: str = "paddleocr",
    languages: Optional[List[str]] = None
) -> str:
    """
    PIL Image 객체에서 직접 텍스트 추출 (파일 저장 없이)

    Args:
        image: PIL Image 객체
        engine: OCR 엔진 ("tesseract", "paddleocr", "dolphin")
        languages: 인식할 언어 리스트

    Returns:
        추출된 텍스트

    Note:
        이 함수는 backward compatibility를 위해 유지됩니다.
        내부적으로 _ocr_extract_from_pil_image()를 호출합니다.
    """
    return _ocr_extract_from_pil_image(image, engine, languages)


def check_remote_ocr_availability() -> dict:
    """
    원격 OCR 서버 상태 확인

    Returns:
        서버 상태 정보 딕셔너리
    """
    try:
        response = requests.get(f"{REMOTE_OCR_SERVER}/health", timeout=REMOTE_OCR_HEALTH_TIMEOUT)
        if response.status_code == 200:
            health_data = response.json()
            return {
                "available": True,
                "server_url": REMOTE_OCR_SERVER,
                "engines": ["tesseract", "paddleocr", "dolphin"],
                "supported_languages": ["eng", "kor", "chi_sim", "jpn"],
                "health": health_data
            }
    except Exception as e:
        logger.debug(f"Remote OCR health check failed: {e}")

    return {
        "available": False,
        "server_url": REMOTE_OCR_SERVER,
        "error": "Server not reachable"
    }


# ========================================
# High-Level Document Parsing Functions
# ========================================

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
        progress_callback: 진행 상태 콜백 함수

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
    parser_logger: ParserLogger,
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
            page_text = _ocr_extract_from_pil_image(
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
    parser_logger: ParserLogger,
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
        text = _ocr_extract_from_file(
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
