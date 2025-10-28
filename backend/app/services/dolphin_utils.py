"""
Dolphin 유틸리티 함수들 (공식 코드 기반)
ByteDance Dolphin 1.5 문서 파서용 헬퍼 함수

Based on: https://github.com/bytedance/Dolphin
"""

import io
import re
from typing import List, Tuple
from PIL import Image


def parse_layout_string(bbox_str: str) -> List[Tuple[List[float], str]]:
    """
    Dolphin-V1.5 레이아웃 문자열 파싱

    Stage 1 출력 형식:
    [x1,y1,x2,y2][label][PAIR_SEP][x1,y1,x2,y2][label][RELATION_SEP]...

    Args:
        bbox_str: Dolphin Stage 1 출력 문자열

    Returns:
        List of (coords, label) tuples
        coords: [x1, y1, x2, y2] in 896x896 normalized space
        label: Element type (header, para, tab, equ, fig, etc.)
    """
    parsed_results = []

    # [PAIR_SEP]와 [RELATION_SEP]로 분할
    segments = bbox_str.split('[PAIR_SEP]')
    new_segments = []
    for seg in segments:
        new_segments.extend(seg.split('[RELATION_SEP]'))
    segments = new_segments

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # 좌표 패턴: [x1,y1,x2,y2]
        coord_pattern = r'\[(\d*\.?\d+),(\d*\.?\d+),(\d*\.?\d+),(\d*\.?\d+)\]'
        # 레이블 패턴: ][label]
        label_pattern = r'\]\[([^\]]+)\]'

        coord_match = re.search(coord_pattern, segment)
        label_matches = re.findall(label_pattern, segment)

        if coord_match and label_matches:
            coords = [float(coord_match.group(i)) for i in range(1, 5)]
            label = label_matches[0].strip()
            parsed_results.append((coords, label))

    return parsed_results


def convert_pdf_to_images_pymupdf(pdf_path: str, target_size: int = 896) -> List[Image.Image]:
    """
    PDF를 이미지로 변환 (PyMuPDF 사용)

    Args:
        pdf_path: PDF 파일 경로
        target_size: 최장변 크기 (기본 896 - Dolphin 모델 입력 크기)

    Returns:
        PIL Image 리스트
    """
    try:
        import pymupdf
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for Dolphin. Install with:\n"
            "  pip install pymupdf"
        )

    images = []
    try:
        doc = pymupdf.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 최장변이 target_size가 되도록 스케일 계산
            rect = page.rect
            scale = target_size / max(rect.width, rect.height)

            # 페이지를 이미지로 렌더링
            mat = pymupdf.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)

            # PIL Image로 변환
            img_data = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_data))
            images.append(pil_image)

        doc.close()
        return images

    except Exception as e:
        raise Exception(f"Failed to convert PDF to images: {str(e)}")


def crop_margin(img: Image.Image) -> Image.Image:
    """
    이미지 여백 제거

    Args:
        img: PIL Image

    Returns:
        여백이 제거된 PIL Image
    """
    try:
        import numpy as np
        import cv2
    except ImportError:
        # opencv 없으면 원본 반환
        return img

    try:
        width, height = img.size
        if width == 0 or height == 0:
            return img

        # 그레이스케일 변환 및 정규화
        data = np.array(img.convert("L"))
        data = data.astype(np.uint8)
        max_val = data.max()
        min_val = data.min()
        if max_val == min_val:
            return img
        data = (data - min_val) / (max_val - min_val) * 255
        gray = 255 * (data < 200).astype(np.uint8)

        # 텍스트 영역 찾기
        coords = cv2.findNonZero(gray)
        if coords is None:
            return img
        a, b, w, h = cv2.boundingRect(coords)

        # 좌표 검증
        a = max(0, a)
        b = max(0, b)
        w = min(w, width - a)
        h = min(h, height - b)

        # 유효한 영역만 crop
        if w > 0 and h > 0:
            return img.crop((a, b, a + w, b + h))
        return img
    except Exception:
        return img


def get_element_prompt(label: str) -> str:
    """
    요소 타입에 맞는 프롬프트 반환 (공식 코드 기준)

    Args:
        label: Element label (tab, equ, para, header, list, etc.)

    Returns:
        Prompt string for Stage 2 parsing
    """
    # 공식 demo_element.py 기준
    if label == "tab":
        return "Parse the table in the image."
    elif label in ["equ", "formula"]:
        return "Read formula in the image."
    elif label in ["code"]:
        return "Read code in the image."
    else:
        # 기본: 텍스트 읽기
        return "Read text in the image."


def crop_element_from_image(image: Image.Image, coords: List[float]) -> Image.Image:
    """
    이미지에서 요소 영역 추출

    Args:
        image: 전체 페이지 이미지 (896x896 기준)
        coords: [x1, y1, x2, y2] in 896x896 space

    Returns:
        Cropped PIL Image
    """
    try:
        # 좌표가 896 기준이라고 가정하고 이미지 크기에 맞게 스케일
        img_w, img_h = image.size
        scale_w = img_w / 896.0
        scale_h = img_h / 896.0

        x1 = int(coords[0] * scale_w)
        y1 = int(coords[1] * scale_h)
        x2 = int(coords[2] * scale_w)
        y2 = int(coords[3] * scale_h)

        # 좌표 검증
        x1 = max(0, min(x1, img_w - 1))
        y1 = max(0, min(y1, img_h - 1))
        x2 = max(x1 + 1, min(x2, img_w))
        y2 = max(y1 + 1, min(y2, img_h))

        cropped = image.crop((x1, y1, x2, y2))

        # 여백 제거
        cropped = crop_margin(cropped)

        return cropped
    except Exception as e:
        # 크롭 실패 시 원본 반환
        return image


def format_element_markdown(label: str, text: str) -> str:
    """
    요소 타입에 맞는 마크다운 형식 생성

    Args:
        label: Element label
        text: Parsed text

    Returns:
        Formatted markdown string
    """
    text = text.strip()
    if not text:
        return ""

    # 섹션 헤더
    if label == "header":
        return f"# {text}\n\n"
    elif label == "sec_1":
        return f"## {text}\n\n"
    elif label == "sec_2":
        return f"### {text}\n\n"
    elif label == "sec_3":
        return f"#### {text}\n\n"

    # 리스트
    elif label == "list":
        # 각 줄을 리스트 아이템으로
        lines = text.split('\n')
        result = []
        for line in lines:
            line = line.strip()
            if line:
                result.append(f"- {line}")
        return '\n'.join(result) + '\n\n'

    # 수식
    elif label in ["equ", "formula"]:
        return f"$$\n{text}\n$$\n\n"

    # 코드
    elif label == "code":
        return f"```\n{text}\n```\n\n"

    # 표 (이미 마크다운 테이블 형식일 것)
    elif label == "tab":
        return f"{text}\n\n"

    # 캡션
    elif label == "cap":
        return f"*{text}*\n\n"

    # 주석/각주
    elif label == "anno":
        return f"> {text}\n\n"

    # 기본 (paragraph)
    else:
        return f"{text}\n\n"
