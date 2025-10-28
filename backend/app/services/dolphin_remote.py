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
        logger.info(f"✅ Dolphin GPU Server connected: {DOLPHIN_GPU_SERVER}")
    else:
        logger.warning(f"⚠️ Dolphin GPU Server not healthy: {DOLPHIN_GPU_SERVER}")
except Exception as e:
    logger.warning(f"⚠️ Dolphin GPU Server not available: {e}")


def call_dolphin_gpu(image: Image.Image, prompt: str, max_length: int = 4096) -> str:
    """
    원격 GPU 서버의 Dolphin 모델 호출

    Args:
        image: PIL Image
        prompt: 추론 프롬프트
        max_length: 최대 생성 길이

    Returns:
        모델 생성 텍스트
    """
    # 이미지를 base64로 인코딩
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # GPU 서버 API 호출
    try:
        request_url = f"{DOLPHIN_GPU_SERVER}/vision"
        logger.info(f"    🌐 [Remote GPU Request] POST {request_url}")
        logger.info(f"       Prompt: {prompt[:50]}...")

        response = requests.post(
            request_url,
            json={
                "prompt": prompt,
                "image_base64": image_base64,
                "max_length": max_length
            },
            timeout=DOLPHIN_INFERENCE_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()

        generated_text = result.get("generated_text", result.get("text", ""))
        logger.info(f"    ✓ [Remote GPU Response] Received {len(generated_text)} chars")

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

    from app.services.dolphin_utils import (
        convert_pdf_to_images_pymupdf,
        parse_layout_string,
        crop_element_from_image,
        get_element_prompt,
        format_element_markdown
    )

    logger.info(f"🐬 Dolphin Remote Parsing: {file_path.name}")
    logger.info(f"  GPU Server: {DOLPHIN_GPU_SERVER}")

    try:
        # 진행 상태: GPU 서버 연결
        if progress_callback:
            progress_callback(10, "📡 Connecting to GPU server...")

        # 1. GPU 서버 상태 확인
        response = requests.get(f"{DOLPHIN_GPU_SERVER}/health", timeout=DOLPHIN_HEALTH_TIMEOUT)
        response.raise_for_status()
        server_info = response.json()
        logger.info(f"  GPU Server Status: {server_info}")

        # 2. PDF → 이미지 변환 (로컬에서 처리)
        if progress_callback:
            progress_callback(20, "📄 Converting PDF to images...")
        logger.info("  📄 Converting PDF to images...")

        if file_path.suffix.lower() == '.pdf':
            images = convert_pdf_to_images_pymupdf(str(file_path), target_size=DOLPHIN_IMAGE_TARGET_SIZE)
        else:
            images = [Image.open(file_path).convert("RGB")]

        if progress_callback:
            progress_callback(25, f"Converted {len(images)} pages")
        logger.info(f"  Converted {len(images)} pages")

        # 3. 페이지별 2단계 파싱 (GPU 서버 호출)
        all_page_contents = []
        total_elements = 0
        total_tables = 0
        total_formulas = 0

        for page_idx, pil_image in enumerate(images):
            page_progress_start = 25 + int((page_idx / len(images)) * 65)
            page_progress_end = 25 + int(((page_idx + 1) / len(images)) * 65)

            if progress_callback:
                progress_callback(page_progress_start, f"📖 Processing Page {page_idx + 1}/{len(images)}")
            logger.info(f"\n  📖 Processing Page {page_idx + 1}/{len(images)}")

            # ===== STAGE 1: Layout Analysis (GPU 서버 호출) =====
            if progress_callback:
                progress_callback(page_progress_start + 1, f"    Stage 1: Layout Analysis (GPU)...")
            logger.info("    Stage 1: Layout Analysis (GPU)...")

            layout_prompt = "Parse the reading order of this document."
            layout_output = call_dolphin_gpu(pil_image, layout_prompt)

            # 레이아웃 파싱 (로컬)
            layout_results = parse_layout_string(layout_output)
            if progress_callback:
                progress_callback(page_progress_start + 2, f"    Detected {len(layout_results)} elements")
            logger.info(f"    Detected {len(layout_results)} elements")

            if not layout_results:
                logger.warning(f"    ⚠️ No layout elements found on page {page_idx + 1}")
                continue

            # ===== STAGE 2: Element Parsing (GPU 서버 호출) =====
            if progress_callback:
                progress_callback(page_progress_start + 3, f"    Stage 2: Parsing elements (GPU)...")
            logger.info(f"    Stage 2: Parsing {len(layout_results)} elements (GPU)...")

            page_elements = []

            for elem_idx, (coords, label) in enumerate(layout_results):
                try:
                    # 요소 영역 crop (로컬)
                    cropped_image = crop_element_from_image(pil_image, coords)

                    # 프롬프트 선택 (로컬)
                    element_prompt = get_element_prompt(label)

                    # 텍스트 추출 (GPU 서버 호출)
                    element_text = call_dolphin_gpu(cropped_image, element_prompt)

                    if element_text.strip():
                        formatted = format_element_markdown(label, element_text)
                        page_elements.append(formatted)

                        total_elements += 1
                        if label == "tab":
                            total_tables += 1
                        elif label in ["equ", "formula"]:
                            total_formulas += 1

                        # 진행 상태 업데이트
                        element_progress = page_progress_start + 3 + int((elem_idx / len(layout_results)) * (page_progress_end - page_progress_start - 3))
                        if progress_callback:
                            progress_callback(element_progress, f"      Parsed {elem_idx + 1}/{len(layout_results)} elements...")
                        logger.info(f"      Element {elem_idx + 1}/{len(layout_results)} ({label}) parsed")

                except Exception as e:
                    logger.warning(f"      ⚠️ Error parsing element {elem_idx}: {str(e)}")
                    continue

            # 페이지 내용 통합
            page_content = "".join(page_elements)
            all_page_contents.append(page_content)

            if progress_callback:
                progress_callback(page_progress_end, f"    ✅ Page {page_idx + 1}: {len(page_elements)} elements")
            logger.info(f"    ✅ Page {page_idx + 1}: {len(page_elements)} elements")

        # 4. 전체 문서 통합
        if progress_callback:
            progress_callback(90, "🔗 Merging all pages...")
        logger.info("\n  🔗 Merging all pages...")

        content = "\n\n---\n\n".join(all_page_contents)

        # 메타데이터
        metadata = {
            "tables": total_tables,
            "images": 0,
            "formulas": total_formulas,
            "pages": len(images),
            "total_elements": total_elements,
            "parsing_method": "dolphin_remote_gpu",
            "gpu_server": DOLPHIN_GPU_SERVER
        }

        logger.info(
            f"\n✅ Dolphin Remote Parsing Complete:\n"
            f"  - GPU Server: {DOLPHIN_GPU_SERVER}\n"
            f"  - Pages: {metadata['pages']}\n"
            f"  - Elements: {metadata['total_elements']}\n"
            f"  - Tables: {metadata['tables']}\n"
            f"  - Formulas: {metadata['formulas']}"
        )

        # 5. 저장 (옵션)
        if output_dir:
            if progress_callback:
                progress_callback(93, "💾 Saving to output folder...")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "content.md"
            output_file.write_text(content, encoding="utf-8")
            logger.info(f"  💾 Saved to {output_file}")

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
        logger.error(f"❌ Dolphin remote parsing failed: {str(e)}", exc_info=True)
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
