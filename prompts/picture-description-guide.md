# Picture Description (VLM) & Smart Image Analysis Guide

> **Version**: 2.3.0
> **Updated**: 2025-10-16
> **Features**:
> - Vision Language Model (VLM) for image descriptions
> - **NEW:** Smart Image Analysis (auto OCR vs VLM selection)

---

## 📋 Overview

Automatically analyze images in documents using:
1. **VLM (Vision Language Model)**: Generate natural language descriptions
2. **OCR (Optical Character Recognition)**: Extract text from images
3. **Smart Analysis**: Auto-select the best method for each image

### Key Features

✅ **Smart Image Analysis** ⭐ NEW: Auto-detect image type and apply optimal processing
✅ **Conditional Activation**: Only process images above area threshold
✅ **Size Filtering**: Skip small icons/logos with `picture_area_threshold`
✅ **Performance Optimized**: Disabled by default, enable when needed
✅ **Multiple VLM Models**: SmolVLM (fast), Granite (accurate), Custom (flexible)
✅ **Custom Prompts**: Tailor prompts to your use case

---

## 🚀 Quick Start

### Option 1: Smart Image Analysis (Recommended) ⭐

**Automatically** select OCR or VLM based on image type:

```powershell
$body = @{
    filename = "document.pdf"
    options = @{
        auto_image_analysis = $true  # ← Enable smart mode
        save_to_output_folder = $true
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parse" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**How it works:**
- **Text-heavy images** (tables, forms) → OCR only
- **Visualizations** (charts, graphs) → VLM description
- **Mixed images** → Both OCR + VLM

### Option 2: Manual Picture Description

Manually enable VLM for all images:

```powershell
$body = @{
    filename = "document.pdf"
    options = @{
        do_picture_description = $true
        save_to_output_folder = $true
    }
} | ConvertTo-Json
```

---

## 🛠️ Setup



### 1. VLM 종속성 설치

```powershell
# 방법 1: Docling VLM 패키지 설치 (권장)
cd backend
pip install docling[vlm]

# 방법 2: 수동 설치
pip install transformers>=4.30.0 torch>=2.0.0 pillow>=10.0.0
```

### 2. 백엔드 재시작

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. API 상태 확인

```powershell
curl http://localhost:8000/
```

응답 예시:
```json
{
  "status": "running",
  "version": "2.2.0",
  "picture_description": {
    "available": true,
    "default_enabled": false,
    "models": ["smolvlm", "granite", "custom"],
    "default_model": "smolvlm"
  }
}
```

---

## 📖 사용 방법

### 기본 사용

```powershell
$body = @{
    filename = "sample.pdf"
    options = @{
        do_picture_description = $true
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parse" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### 고급 설정

```powershell
$body = @{
    filename = "research_paper.pdf"
    options = @{
        # Picture Description 활성화
        do_picture_description = $true
        picture_description_model = "smolvlm"  # or "granite", "custom"
        picture_description_prompt = "Describe this scientific figure in detail, including key findings and data trends."
        picture_area_threshold = 0.1  # 더 큰 이미지만 처리 (기본값: 0.05)
        picture_images_scale = 2.0    # 이미지 품질 향상 (기본값: 2.0)

        # 출력 설정
        save_to_output_folder = $true
        output_format = "markdown"

        # 기타 설정
        do_ocr = $false
        extract_tables = $true
    }
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/parse" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### 커스텀 Hugging Face VLM 사용

```powershell
$body = @{
    filename = "document.pdf"
    options = @{
        do_picture_description = $true
        picture_description_model = "custom"
        custom_vlm_repo_id = "llava-hf/llava-1.5-7b-hf"  # Hugging Face 모델 ID
        picture_description_prompt = "What is shown in this image?"
        picture_area_threshold = 0.05
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parse" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## 🎯 응답 형식

### ParseResponse 구조

```json
{
  "success": true,
  "filename": "sample.pdf",
  "markdown": "...",
  "stats": {
    "lines": 450,
    "words": 3200,
    "characters": 18500,
    "size_kb": 18.07
  },
  "pictures_summary": {
    "total_pictures": 5,
    "pictures_with_descriptions": 5,
    "pictures": [
      {
        "ref": "picture-1",
        "caption": "Figure 1: System Architecture",
        "descriptions": [
          {
            "provenance": "smolvlm-256m-instruct",
            "text": "A detailed architecture diagram showing three main components: the frontend layer with React components, the backend API layer with FastAPI, and the database layer with PostgreSQL. Arrows indicate data flow between layers."
          }
        ]
      },
      {
        "ref": "picture-2",
        "caption": "Figure 2: Performance Graph",
        "descriptions": [
          {
            "provenance": "smolvlm-256m-instruct",
            "text": "A line graph displaying performance metrics over time, with a clear upward trend from January to December. The y-axis shows response time in milliseconds, ranging from 100ms to 500ms."
          }
        ]
      }
    ]
  },
  "saved_to": "C:/workspace/parsing-app/output/sample/content.md"
}
```

---

## ⚙️ 설정 옵션

### TableParsingOptions - Picture Description 관련

| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `do_picture_description` | bool | `false` | Picture Description 활성화 여부 |
| `picture_description_model` | "smolvlm" \| "granite" \| "custom" | "smolvlm" | 사용할 VLM 모델 |
| `picture_description_prompt` | str | "Describe this image..." | VLM에 전달할 프롬프트 |
| `picture_area_threshold` | float | 0.05 | 최소 이미지 영역 (0.0-1.0) |
| `picture_images_scale` | float | 2.0 | 이미지 스케일 배율 |
| `custom_vlm_repo_id` | str \| None | None | 커스텀 Hugging Face VLM 모델 ID |

### VLM 모델 비교

| 모델 | 특징 | 속도 | 정확도 | 용도 |
|------|------|------|--------|------|
| **SmolVLM** | 256M 파라미터, 가벼움 | ⚡⚡⚡ 빠름 | ⭐⭐⭐ 양호 | 일반 문서, 빠른 처리 |
| **Granite** | IBM Granite Vision 3.3 2B | ⚡⚡ 보통 | ⭐⭐⭐⭐ 높음 | 기술 문서, 정확도 우선 |
| **Custom** | 사용자 지정 모델 | 모델마다 다름 | 모델마다 다름 | 특수 용도, 도메인 특화 |

---

## 🔍 사용 사례

### 1. 연구 논문 분석

```powershell
$body = @{
    filename = "research_paper.pdf"
    options = @{
        do_picture_description = $true
        picture_description_model = "granite"  # 높은 정확도
        picture_description_prompt = "Describe this scientific figure, including the type of visualization, key data points, trends, and any notable findings."
        picture_area_threshold = 0.08  # 작은 아이콘 제외
    }
} | ConvertTo-Json
```

### 2. 기술 문서 처리

```powershell
$body = @{
    filename = "technical_manual.pdf"
    options = @{
        do_picture_description = $true
        picture_description_model = "smolvlm"  # 빠른 처리
        picture_description_prompt = "Describe this technical diagram, identifying components, connections, and their functions."
        picture_area_threshold = 0.05
    }
} | ConvertTo-Json
```

### 3. 비즈니스 리포트

```powershell
$body = @{
    filename = "quarterly_report.pdf"
    options = @{
        do_picture_description = $true
        picture_description_model = "smolvlm"
        picture_description_prompt = "Describe this chart or graph, focusing on trends, comparisons, and key insights."
        picture_area_threshold = 0.1  # 큰 차트/그래프만
    }
} | ConvertTo-Json
```

---

## 🧪 테스트 방법

### 자동 테스트 스크립트

```powershell
# backend 폴더에 있는 테스트 스크립트 실행
cd backend
.\test_picture_description.ps1
```

### 수동 테스트

1. **이미지가 포함된 PDF 준비**
   ```powershell
   # docu 폴더에 PDF 파일 배치
   cp "path/to/your/document.pdf" "C:/workspace/parsing-app/docu/"
   ```

2. **Picture Description 없이 파싱** (비교용)
   ```powershell
   $body = @{
       filename = "document.pdf"
       options = @{ do_picture_description = $false }
   } | ConvertTo-Json

   $result1 = Invoke-RestMethod -Uri "http://localhost:8000/parse" `
       -Method Post -ContentType "application/json" -Body $body
   ```

3. **Picture Description 활성화하여 파싱**
   ```powershell
   $body = @{
       filename = "document.pdf"
       options = @{
           do_picture_description = $true
           save_to_output_folder = $true
       }
   } | ConvertTo-Json

   $result2 = Invoke-RestMethod -Uri "http://localhost:8000/parse" `
       -Method Post -ContentType "application/json" -Body $body
   ```

4. **결과 비교**
   ```powershell
   # pictures_summary 확인
   $result2.pictures_summary
   ```

---

## 🛠️ 문제 해결

### 1. VLM 모델 로딩 실패

**증상**: `ModuleNotFoundError: No module named 'transformers'`

**해결**:
```powershell
cd backend
pip install docling[vlm]
# 또는
pip install transformers>=4.30.0 torch>=2.0.0
```

### 2. 메모리 부족

**증상**: `CUDA out of memory` 또는 시스템 느려짐

**해결**:
- `picture_area_threshold`를 높여서 큰 이미지만 처리
- 더 작은 모델 사용 (SmolVLM)
- 배치 크기 조정 (코드 수정 필요)

### 3. 이미지 감지되지 않음

**증상**: `pictures_summary.total_pictures == 0`

**원인**:
- 문서에 이미지가 없음
- 이미지가 `picture_area_threshold` 이하

**해결**:
```powershell
# threshold를 낮춰서 작은 이미지도 포함
$body.options.picture_area_threshold = 0.01
```

### 4. 설명 품질이 낮음

**해결**:
- 더 정확한 모델 사용 (Granite)
- 프롬프트 개선
- 이미지 스케일 증가 (`picture_images_scale = 3.0`)

---

## 📊 성능 고려사항

### 처리 시간

| 문서 유형 | 이미지 개수 | 모델 | 예상 시간 |
|----------|-----------|------|----------|
| 논문 (10페이지) | 5개 | SmolVLM | ~30초 |
| 논문 (10페이지) | 5개 | Granite | ~60초 |
| 기술 문서 (50페이지) | 20개 | SmolVLM | ~2분 |

**첫 실행**: 모델 다운로드 시간 추가 (SmolVLM: ~500MB, Granite: ~2GB)

### 최적화 팁

1. **threshold 조정**: 불필요한 작은 이미지 제외
2. **배치 처리**: 여러 문서 처리 시 모델을 재사용 (자동 캐싱)
3. **GPU 사용**: CUDA 사용 가능 시 자동으로 GPU 활용

---

## 🔗 관련 문서

- [Docling Picture Description 공식 문서](https://docling-project.github.io/docling/examples/pictures_description)
- [통합 RAG 구현 계획](./integrated-rag-parsing-implementation-plan.md)
- [FastAPI 구현 가이드](./fastapi-implementation-plan-scenario1-2.md)

---

## 📝 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 2.2.0 | 2025-10-16 | Picture Description 기능 추가 |
| 2.1.1 | - | Camelot 하이브리드 전략 |
| 2.1.0 | - | Phase 3 RAG 최적화 |

---

## 💡 다음 단계

1. ✅ Picture Description 기능 추가 완료
2. 🔲 Phase 6: CLI 인터페이스 구현
3. 🔲 Phase 7: AI 표 요약 기능
4. 🔲 Phase 8: RAG 시스템 통합
5. 🔲 Phase 10: Dify 지식 베이스 자동 업로드

---

**작성자**: Claude Code
**문서 버전**: 1.0
**마지막 업데이트**: 2025-10-16
