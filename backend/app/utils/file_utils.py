"""
파일 및 출력 구조 관리 유틸리티

중복 코드를 제거하고 일관된 파일 처리를 제공합니다.
"""
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json


def create_document_output_dir(
    file_path: Path,
    base_dir: Path
) -> Path:
    """문서별 출력 디렉토리 생성

    Args:
        file_path: 원본 파일 경로
        base_dir: 기본 출력 디렉토리 (예: OUTPUT_FOLDER)

    Returns:
        생성된 디렉토리 경로 (예: output/document_name/)

    Example:
        >>> from app.config import OUTPUT_FOLDER
        >>> output_dir = create_document_output_dir(
        ...     Path("docu/sample.pdf"),
        ...     OUTPUT_FOLDER
        ... )
        >>> print(output_dir)
        WindowsPath('output/sample')
    """
    doc_output_dir = base_dir / file_path.stem
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    return doc_output_dir


@dataclass
class OutputStructure:
    """출력 구조 표준화

    모든 파서가 동일한 출력 구조를 반환하도록 합니다.
    """
    output_dir: Path
    content_file: Path
    images_dir: Optional[Path] = None
    tables_dir: Optional[Path] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """API 응답용 딕셔너리 변환"""
        return {
            "output_dir": str(self.output_dir),
            "content_file": str(self.content_file),
            "images_dir": str(self.images_dir) if self.images_dir else None,
            "tables_dir": str(self.tables_dir) if self.tables_dir else None
        }


def build_output_structure(
    output_dir: Path,
    has_tables: bool = False,
    has_images: bool = False
) -> OutputStructure:
    """출력 구조 생성

    Args:
        output_dir: 출력 디렉토리
        has_tables: 테이블 디렉토리 포함 여부
        has_images: 이미지 디렉토리 포함 여부

    Returns:
        OutputStructure 객체
    """
    return OutputStructure(
        output_dir=output_dir,
        content_file=output_dir / "content.md",
        images_dir=output_dir / "images" if has_images else None,
        tables_dir=output_dir / "tables" if has_tables else None
    )


def save_parsing_output(
    content: str,
    output_dir: Path,
    format: str = "markdown",
    metadata: Optional[Dict] = None
) -> Path:
    """파싱 결과 저장

    Args:
        content: 파싱된 컨텐츠
        output_dir: 출력 디렉토리
        format: 출력 형식 (markdown, html, json)
        metadata: 파싱 메타데이터 (옵션)

    Returns:
        저장된 컨텐츠 파일 경로
    """
    # 확장자 결정
    ext_map = {"markdown": ".md", "html": ".html", "json": ".json"}
    ext = ext_map.get(format, ".md")

    # 컨텐츠 저장
    content_path = output_dir / f"content{ext}"
    content_path.write_text(content, encoding='utf-8')

    # 메타데이터 저장 (옵션)
    if metadata:
        metadata_path = output_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    return content_path


def generate_version_folder_name(
    strategy: str, options: Optional[Dict[str, Any]] = None
) -> str:
    """파싱 전략 + 옵션 + 타임스탬프 기반 버전 폴더명 생성

    Args:
        strategy: 파싱 전략명 (예: "Remote OCR", "MinerU", "Docling Only")
        options: 파싱 옵션 딕셔너리 (옵션)

    Returns:
        버전 폴더명 (예: "remote-ocr_upstage_20251105-163045")

    Examples:
        >>> generate_version_folder_name("Remote OCR", {"remote_ocr_engine": "upstage"})
        'remote-ocr_upstage_20251105-163045'

        >>> generate_version_folder_name("MinerU")
        'mineru_20251105-171520'

        >>> generate_version_folder_name("Docling+Camelot Hybrid", {"camelot_mode": "lattice"})
        'docling-camelot_lattice_20251105-180010'
    """
    # 전략명 정규화 (소문자, 공백/특수문자 제거)
    strategy_normalized = (
        strategy.lower()
        .replace(" ", "-")
        .replace("+", "-")
        .replace("(", "")
        .replace(")", "")
    )

    # 타임스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # 옵션에서 주요 정보 추출
    option_parts = []
    if options:
        # Remote OCR 엔진
        if "remote_ocr_engine" in options and options["remote_ocr_engine"]:
            option_parts.append(options["remote_ocr_engine"])

        # Camelot 모드
        if "camelot_mode" in options and options["camelot_mode"]:
            option_parts.append(options["camelot_mode"])

        # OCR 엔진 (Docling)
        if "ocr_engine" in options and options["ocr_engine"]:
            option_parts.append(options["ocr_engine"])

        # OCR 언어
        if "ocr_lang" in options and options["ocr_lang"]:
            langs = options["ocr_lang"]
            if isinstance(langs, list) and langs:
                option_parts.append("-".join(langs[:2]))  # 최대 2개 언어만

    # 폴더명 조합
    if option_parts:
        folder_name = f"{strategy_normalized}_{'_'.join(option_parts)}_{timestamp}"
    else:
        folder_name = f"{strategy_normalized}_{timestamp}"

    return folder_name


def create_versioned_output_dir(
    file_path: Path, base_dir: Path, version_folder: str
) -> Path:
    """버전별 출력 디렉토리 생성

    Args:
        file_path: 원본 파일 경로
        base_dir: 기본 출력 디렉토리 (예: OUTPUT_FOLDER)
        version_folder: 버전 폴더명 (예: "remote-ocr_upstage_20251105-163045")

    Returns:
        생성된 버전별 디렉토리 경로
        (예: output/document_name/remote-ocr_upstage_20251105-163045/)

    Example:
        >>> from app.config import OUTPUT_FOLDER
        >>> version_folder = generate_version_folder_name("Remote OCR", {"remote_ocr_engine": "upstage"})
        >>> output_dir = create_versioned_output_dir(
        ...     Path("docu/sample.pdf"),
        ...     OUTPUT_FOLDER,
        ...     version_folder
        ... )
        >>> print(output_dir)
        WindowsPath('output/sample/remote-ocr_upstage_20251105-163045')
    """
    # 문서별 기본 디렉토리
    doc_base_dir = base_dir / file_path.stem

    # 버전별 디렉토리
    versioned_dir = doc_base_dir / version_folder
    versioned_dir.mkdir(parents=True, exist_ok=True)

    return versioned_dir
