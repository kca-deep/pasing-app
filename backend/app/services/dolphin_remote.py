"""
Dolphin Remote GPU Parser
원격 GPU 서버의 Dolphin 모델을 사용하는 파서

환경 변수:
    DOLPHIN_GPU_SERVER: GPU 서버 주소 (예: http://192.168.1.100:8001)
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import logging
import requests
import base64
import io
from PIL import Image
import os

logger = logging.getLogger(__name__)

# Import standardized logging utility
from app.utils.logging_utils import ParserLogger, log_resource_available, log_resource_unavailable

# 환경 변수에서 GPU 서버 주소 가져오기 (통합 OCR 서버)
DOLPHIN_GPU_SERVER = os.getenv("DOLPHIN_GPU_SERVER", "http://kca-ai.kro.kr:8005")
DOLPHIN_HEALTH_TIMEOUT = int(os.getenv("DOLPHIN_HEALTH_TIMEOUT", "5"))
DOLPHIN_INFERENCE_TIMEOUT = int(os.getenv("DOLPHIN_INFERENCE_TIMEOUT", "60"))
DOLPHIN_IMAGE_TARGET_SIZE = int(os.getenv("DOLPHIN_IMAGE_TARGET_SIZE", "896"))

# GPU 서버 연결 테스트
DOLPHIN_REMOTE_AVAILABLE = False
try:
    response = requests.get(f"{DOLPHIN_GPU_SERVER}/health", timeout=DOLPHIN_HEALTH_TIMEOUT)
    if response.status_code == 200:
        DOLPHIN_REMOTE_AVAILABLE = True
        log_resource_available(logger, "Dolphin GPU Server", url=DOLPHIN_GPU_SERVER, status="connected")
    else:
        log_resource_unavailable(logger, "Dolphin GPU Server", url=DOLPHIN_GPU_SERVER, status="not healthy")
except Exception as e:
    log_resource_unavailable(logger, "Dolphin GPU Server", url=DOLPHIN_GPU_SERVER, error=str(e))


def call_dolphin_gpu(
    image: Image.Image,
    prompt: str = "Read text in the image.",
    max_length: int = 4096,
    engine: str = "dolphin"
) -> str:
    """
    원격 GPU 서버의 OCR 모델 호출 (Dolphin 또는 PaddleOCR)

    Args:
        image: PIL Image
        prompt: 추론 프롬프트 (Dolphin용)
        max_length: 최대 생성 길이
        engine: OCR 엔진 (dolphin, paddleocr, tesseract)

    Returns:
        모델 생성 텍스트
    """
    # 이미지를 base64로 인코딩
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # GPU 서버 API 호출
    try:
        request_url = f"{DOLPHIN_GPU_SERVER}/ocr/extract"
        logger.info(f"    🌐 [Remote GPU Request] POST {request_url} (engine: {engine})")

        request_payload = {
            "image_base64": image_base64,
            "engine": engine
        }

        # Dolphin용 파라미터
        if engine == "dolphin":
            request_payload["prompt"] = prompt
            request_payload["max_length"] = max_length
        # PaddleOCR/Tesseract용 파라미터
        else:
            request_payload["language"] = "kor"

        response = requests.post(
            request_url,
            json=request_payload,
            timeout=DOLPHIN_INFERENCE_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            raise Exception(f"OCR failed: {error_msg}")

        generated_text = result.get("text", "")
        logger.info(f"    ✓ [Remote GPU Response] Received {len(generated_text)} chars (engine: {result.get('engine_used')})")

        # 응답 검증: 너무 짧거나 의미없는 응답 체크
        if len(generated_text.strip()) < 5:
            logger.warning(f"    ⚠️ Short/invalid response: '{generated_text}' - may indicate OCR failure")

        return generated_text

    except requests.exceptions.Timeout:
        raise Exception(f"GPU server timeout: {DOLPHIN_GPU_SERVER}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"GPU server connection failed: {DOLPHIN_GPU_SERVER}")
    except Exception as e:
        raise Exception(f"GPU server error: {str(e)}")


def parse_with_dolphin_remote(
    file_path: Path,
    output_dir: Optional[Path] = None,
    output_format: str = "markdown",
    parsing_level: str = "page",
    max_batch_size: int = 8,
    progress_callback: Optional[callable] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    원격 GPU 서버를 사용한 Dolphin 파싱

    로컬에서 PDF → 이미지 변환만 수행
    AI 추론은 모두 GPU 서버에서 처리 (속도 향상)

    Args:
        file_path: PDF 파일 경로
        output_dir: 출력 디렉토리
        output_format: 출력 형식
        parsing_level: 파싱 레벨 (미사용)
        max_batch_size: 배치 크기 (미사용)
        device: 디바이스 (미사용, GPU 서버가 처리)
        progress_callback: 진행 상태 콜백

    Returns:
        (content, metadata) 튜플
    """
    if not DOLPHIN_REMOTE_AVAILABLE:
        raise Exception(
            f"Dolphin GPU Server not available at {DOLPHIN_GPU_SERVER}\n"
            "Please check:\n"
            f"1. GPU server is running\n"
            f"2. DOLPHIN_GPU_SERVER environment variable is correct\n"
            f"3. Network connection is available"
        )

    from app.services.dolphin_utils import convert_pdf_to_images_pymupdf

    # Initialize standardized logger
    parser_logger = ParserLogger("Dolphin Remote", logger)

    # Log parser start with configuration
    parser_logger.start(
        file_path.name,
        gpu_server=DOLPHIN_GPU_SERVER,
        parsing_level=parsing_level,
        output_format=output_format
    )

    try:
        # 진행 상태: GPU 서버 연결
        if progress_callback:
            progress_callback(10, "Connecting to GPU server...")

        # 1. GPU 서버 상태 확인
        parser_logger.step(1, 4, "Checking GPU server availability...")
        response = requests.get(f"{DOLPHIN_GPU_SERVER}/health", timeout=DOLPHIN_HEALTH_TIMEOUT)
        response.raise_for_status()
        server_info = response.json()
        parser_logger.detail(f"Server Status: {server_info.get('status', 'healthy')}", last=True)

        # 2. PDF → 이미지 변환 (로컬에서 처리)
        if progress_callback:
            progress_callback(20, "Converting PDF to images...")
        parser_logger.step(2, 4, "Converting PDF to images...")

        if file_path.suffix.lower() == '.pdf':
            images = convert_pdf_to_images_pymupdf(str(file_path), target_size=DOLPHIN_IMAGE_TARGET_SIZE)
        else:
            images = [Image.open(file_path).convert("RGB")]

        if progress_callback:
            progress_callback(25, f"Converted {len(images)} pages")
        parser_logger.detail(f"Converted: {len(images)} pages", last=True)

        # 3. 페이지별 단순 OCR 파싱 (GPU 서버 호출)
        all_page_contents = []
        ocr_engine = "dolphin"  # 기본 엔진
        ocr_fallback = "paddleocr"  # 폴백 엔진

        for page_idx, pil_image in enumerate(images):
            page_progress_start = 25 + int((page_idx / len(images)) * 65)
            page_progress_end = 25 + int(((page_idx + 1) / len(images)) * 65)

            if progress_callback:
                progress_callback(page_progress_start, f"Processing Page {page_idx + 1}/{len(images)}")
            parser_logger.page(page_idx + 1, len(images))

            try:
                # 전체 페이지 OCR (GPU 서버 호출)
                if progress_callback:
                    progress_callback(page_progress_start + 2, f"Running OCR on page...")
                parser_logger.sub_step("Running OCR on full page...", emoji='process')

                # Dolphin으로 먼저 시도
                page_text = call_dolphin_gpu(
                    pil_image,
                    prompt="Read all text in the image.",
                    engine=ocr_engine
                )

                # Dolphin 응답 검증 - 너무 짧거나 의미없으면 PaddleOCR로 폴백
                if len(page_text.strip()) < 10 or page_text.strip() in ["()", "() ()", "() ()) ()"]:
                    parser_logger.warning(
                        f"Dolphin returned invalid response, falling back to {ocr_fallback}",
                        dolphin_response=page_text[:50]
                    )

                    # PaddleOCR로 재시도
                    page_text = call_dolphin_gpu(
                        pil_image,
                        engine=ocr_fallback
                    )

                # 페이지 내용 저장
                if page_text.strip():
                    # 페이지 구분자와 함께 저장
                    page_content = f"## Page {page_idx + 1}\n\n{page_text.strip()}\n\n"
                    all_page_contents.append(page_content)

                    if progress_callback:
                        progress_callback(page_progress_end, f"Page {page_idx + 1}: {len(page_text)} chars extracted")
                    parser_logger.detail(f"Extracted {len(page_text)} characters", last=True)
                else:
                    parser_logger.warning(
                        f"No text extracted from page {page_idx + 1}"
                    )

            except Exception as e:
                parser_logger.warning(
                    f"Error processing page {page_idx + 1}: {str(e)}"
                )
                continue

        # 4. 전체 문서 통합
        if progress_callback:
            progress_callback(90, "Merging all pages...")
        parser_logger.step(4, 4, "Merging all pages...")

        content = "\n".join(all_page_contents)

        # 메타데이터
        total_chars = sum(len(page) for page in all_page_contents)
        metadata = {
            "pages": len(images),
            "pages_processed": len(all_page_contents),
            "total_characters": total_chars,
            "parsing_method": "dolphin_remote_simple_ocr",
            "ocr_engine": ocr_engine,
            "fallback_engine": ocr_fallback,
            "gpu_server": DOLPHIN_GPU_SERVER
        }

        parser_logger.success(
            "Parsing complete",
            pages=metadata['pages'],
            pages_processed=metadata['pages_processed'],
            total_chars=metadata['total_characters'],
            ocr_engine=ocr_engine
        )

        # 5. 저장 (옵션)
        if output_dir:
            if progress_callback:
                progress_callback(93, "Saving to output folder...")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "content.md"
            output_file.write_text(content, encoding="utf-8")
            parser_logger.sub_step(f"Saved to {output_file}", emoji='save')

        # 6. 출력 형식 변환
        if output_format == "json":
            import json
            content_json = {
                "pages": all_page_contents,
                "metadata": metadata
            }
            content = json.dumps(content_json, ensure_ascii=False, indent=2)
        elif output_format == "html":
            html_content = content.replace("\n", "<br>\n")
            content = f"<html><body>\n{html_content}\n</body></html>"

        return content, metadata

    except Exception as e:
        parser_logger.error(f"Dolphin remote parsing failed: {str(e)}", exc_info=True)
        raise


def check_dolphin_remote_installation() -> Dict[str, Any]:
    """Dolphin 원격 서버 상태 확인"""
    try:
        response = requests.get(f"{DOLPHIN_GPU_SERVER}/", timeout=DOLPHIN_HEALTH_TIMEOUT)
        if response.status_code == 200:
            server_info = response.json()
            return {
                "installed": True,
                "version": "remote-gpu",
                "server_url": DOLPHIN_GPU_SERVER,
                "server_status": server_info.get("status"),
                "model_loaded": server_info.get("model_loaded", False),
                "cuda_available": server_info.get("cuda_available", False),
                "features": {
                    "remote_gpu": True,
                    "two_stage_pipeline": True,
                    "layout_analysis": True,
                    "element_parsing": True,
                    "high_accuracy": True
                }
            }
    except Exception as e:
        logger.debug(f"Remote server check failed: {e}")

    return {
        "installed": False,
        "version": "unknown",
        "server_url": DOLPHIN_GPU_SERVER,
        "error": "GPU server not reachable"
    }
