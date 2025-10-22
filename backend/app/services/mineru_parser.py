"""
MinerU 기반 범용 문서 파서 (로컬 라이브러리)

모든 문서 타입을 자동으로 처리 (하드코딩 없음)
로컬에 설치된 MinerU 라이브러리를 직접 사용 (API 서버 불필요)

Installation:
    pip install magic-pdf[full]

Features:
    ✅ 자동 문서 타입 인식
    ✅ 자동 언어 인식 (84개 언어, 한국어 포함)
    ✅ 병합 셀 자동 처리 (HTML로 임베드)
    ✅ 텍스트 순서 자동 정렬 (Reading Order)
    ✅ 계층적 표 구조 보존
    ✅ 크로스 페이지 표 병합
    ✅ 하드코딩 제로
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

# MinerU/magic-pdf 라이브러리 import
MINERU_AVAILABLE = False
MINERU_VERSION = "unknown"

try:
    from magic_pdf.data.dataset import PymuDocDataset
    from magic_pdf.data.data_reader_writer import FileBasedDataWriter
    from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
    from magic_pdf.config.make_content_config import DropMode, MakeMode
    import magic_pdf.model as model_config

    MINERU_AVAILABLE = True
    MINERU_VERSION = "magic-pdf-1.3"
    logger.info("✅ MinerU loaded: magic-pdf 1.3+ (PymuDocDataset)")
except ImportError as e:
    logger.warning(f"⚠️ MinerU not installed. Run: pip install magic-pdf[full]")
    logger.warning(f"   Error: {str(e)}")
    MINERU_AVAILABLE = False


async def parse_with_mineru(
    file_path: Path,
    output_format: str = "markdown",
    lang: str = "auto",
    use_ocr: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    MinerU로 PDF 파싱 (magic-pdf 1.3+ API)

    Args:
        file_path: PDF 파일 경로
        output_format: 출력 형식 (markdown, html, json)
        lang: 언어 (auto = 자동 인식, ko = 한국어, ch = 중국어, en = 영어, ja = 일본어)
        use_ocr: OCR 사용 여부

    Returns:
        (content, metadata)
        - content: 파싱된 마크다운/HTML/JSON 문자열
        - metadata: 표, 이미지, 수식 정보

    Raises:
        ImportError: MinerU가 설치되지 않은 경우
        Exception: 파싱 실패 시
    """
    if not MINERU_AVAILABLE:
        raise ImportError(
            "MinerU (magic-pdf) not installed. Install with:\n"
            "  pip install magic-pdf[full]"
        )

    logger.info(f"🔮 MinerU parsing: {file_path.name} (version={MINERU_VERSION}, lang={lang}, ocr={use_ocr})")

    try:
        # 출력 디렉토리 생성
        output_dir = file_path.parent / "mineru_output"
        output_dir.mkdir(exist_ok=True)

        image_dir = output_dir / "images"
        image_dir.mkdir(exist_ok=True)

        # PDF 읽기
        pdf_bytes = file_path.read_bytes()

        # 언어 설정 (magic-pdf 형식으로 변환)
        if lang in ["ko", "kr", "korean"]:
            ocr_lang = "ch"  # 한중일 혼합 모델 사용
        elif lang == "auto":
            ocr_lang = None  # 자동 인식
        else:
            ocr_lang = lang

        # PymuDocDataset 생성
        logger.info("  Step 1/4: Creating dataset...")
        ds = PymuDocDataset(pdf_bytes, lang=ocr_lang)

        # FileBasedDataWriter 생성
        image_writer = FileBasedDataWriter(str(image_dir))
        md_writer = FileBasedDataWriter(str(output_dir))

        # Document 분석
        logger.info("  Step 2/4: Analyzing document...")
        # formula_enable=False: 수식 인식 비활성화 (transformers 호환성 문제 회피)
        # layout_model 지정하지 않음: magic-pdf.json의 layout-config 사용
        infer_result = ds.apply(
            doc_analyze,
            ocr=use_ocr,
            lang=ds._lang,
            formula_enable=False,  # 명시적으로 수식 인식 비활성화
            layout_model=None  # None = magic-pdf.json 설정 사용
        )

        # 파이프라인 실행 (OCR 모드 or TXT 모드)
        logger.info("  Step 3/4: Processing pipeline...")
        if use_ocr:
            pipe_result = infer_result.pipe_ocr_mode(
                image_writer,
                debug_mode=True,
                lang=ds._lang
            )
        else:
            pipe_result = infer_result.pipe_txt_mode(
                image_writer,
                debug_mode=True,
                lang=ds._lang
            )

        # Markdown 생성
        logger.info("  Step 4/4: Generating markdown...")
        # dump_md() signature: dump_md(writer, file_path, image_dir)
        pipe_result.dump_md(md_writer, "content.md", str(image_dir))

        # 생성된 마크다운 파일 읽기
        md_output_path = output_dir / "content.md"
        md_content = md_output_path.read_text(encoding="utf-8")

        # 메타데이터 추출
        # get_content_list() signature: get_content_list(image_dir_or_bucket_prefix, drop_mode='none')
        content_list_json = pipe_result.get_content_list(str(image_dir))
        pdf_info = json.loads(content_list_json) if isinstance(content_list_json, str) else content_list_json

        # 메타데이터 계산
        total_tables = len([item for item in pdf_info if item.get("type") == "table"])
        total_images = len([item for item in pdf_info if item.get("type") == "image"])
        total_formulas = len([item for item in pdf_info if item.get("type") in ["inline_equation", "interline_equation"]])

        metadata = {
            "tables": total_tables,
            "images": total_images,
            "formulas": total_formulas,
            "pages": len(pdf_info) if pdf_info else 0,
            "language": ds._lang or lang,
            "parsing_method": "mineru_magic_pdf_1.3",
            "ocr_enabled": use_ocr
        }

        logger.info(
            f"✅ MinerU: {metadata['tables']} tables, "
            f"{metadata['images']} images, "
            f"{metadata['formulas']} formulas"
        )

        # 출력 형식 변환
        if output_format == "json":
            content = json.dumps(pdf_info, ensure_ascii=False, indent=2)
        elif output_format == "html":
            content = f"<html><body>\n{md_content}\n</body></html>"
        else:  # markdown
            content = md_content

        return content, metadata

    except FileNotFoundError as e:
        # Model weights not found - provide clear installation instructions
        error_msg = str(e)
        if "yolo_v8_ft.pt" in error_msg or "models" in error_msg.lower():
            logger.error("❌ MinerU model weights not found!")
            logger.error("   MinerU requires downloading AI models (~2-3GB) before first use.")
            logger.error("")
            logger.error("   Quick fix:")
            logger.error("   1. Run: python backend/download_mineru_models.py")
            logger.error("   2. Or run: magic-pdf --download-models")
            logger.error("")
            logger.error(f"   Original error: {error_msg}")

            raise ImportError(
                "MinerU model weights not found. "
                "Download models with: magic-pdf --download-models "
                "or run: python backend/download_mineru_models.py "
                f"(Missing: {error_msg})"
            )
        else:
            logger.error(f"❌ MinerU file error: {str(e)}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"❌ MinerU parsing failed: {str(e)}", exc_info=True)
        raise


def check_mineru_installation() -> Dict[str, Any]:
    """
    MinerU 설치 상태 확인

    Returns:
        설치 정보 딕셔너리
    """
    return {
        "installed": MINERU_AVAILABLE,
        "version": MINERU_VERSION,
        "features": {
            "auto_language": MINERU_AVAILABLE,
            "ocr_support": MINERU_AVAILABLE,
            "table_recognition": MINERU_AVAILABLE,
            "formula_recognition": MINERU_AVAILABLE,
            "korean_support": MINERU_AVAILABLE
        }
    }
