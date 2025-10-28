"""
Remote OCR Service Integration
원격 OCR 서버를 사용한 텍스트 추출

OCR API 정보:
  - URL: http://kca-ai.kro.kr:8005/ocr/extract
  - 엔진:
    * "tesseract" - 빠름 (~0.2초)
    * "paddleocr" - 정확 (~1.6초) ⭐ 권장
    * "dolphin" - AI 기반 (~5초)
"""

import requests
import base64
import logging
import os
from pathlib import Path
from typing import Optional, List
from PIL import Image
import io

logger = logging.getLogger(__name__)

# OCR 서버 설정 (환경변수 지원)
REMOTE_OCR_SERVER = os.getenv("REMOTE_OCR_SERVER", "http://kca-ai.kro.kr:8005")
REMOTE_OCR_HEALTH_TIMEOUT = int(os.getenv("REMOTE_OCR_HEALTH_TIMEOUT", "5"))
REMOTE_OCR_REQUEST_TIMEOUT = int(os.getenv("REMOTE_OCR_REQUEST_TIMEOUT", "30"))

# 기본 OCR 언어 설정
DEFAULT_OCR_LANGUAGES = os.getenv("DEFAULT_OCR_LANGUAGES", "eng,kor").split(",")

REMOTE_OCR_AVAILABLE = False

# 서버 연결 테스트
try:
    response = requests.get(f"{REMOTE_OCR_SERVER}/health", timeout=REMOTE_OCR_HEALTH_TIMEOUT)
    if response.status_code == 200:
        REMOTE_OCR_AVAILABLE = True
        logger.info(f"✅ Remote OCR Server connected: {REMOTE_OCR_SERVER}")
    else:
        logger.warning(f"⚠️ Remote OCR Server not healthy: {REMOTE_OCR_SERVER}")
except Exception as e:
    logger.warning(f"⚠️ Remote OCR Server not available: {e}")


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
