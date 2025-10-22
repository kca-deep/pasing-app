# RAG 최적화 PDF 파싱 시스템 통합 구현 플랜

> **최종 업데이트**: 2025-10-17
> **버전**: 1.2 (SQLite 통합)
> **상태**: 통합 플랜 (rag-optimized + fastapi-implementation + test-plan + sqlite-db)
>
> **⚠️ 중요 아키텍처 결정**:
> - **Docling 라이브러리 직접 호출** 방식 사용 (docling-serve 사용 안 함)
> - FastAPI에서 Docling을 in-process로 실행
> - VLM pipeline을 통한 문서 파싱
> - 별도의 Docling 서버 불필요

## 📋 문서 개요

이 문서는 **Docling 라이브러리를 직접 활용한 RAG 최적화 PDF 파싱 시스템**의 전체 구현 플랜입니다.

**아키텍처**: FastAPI → Docling 라이브러리 (직접 호출) → VLM Pipeline → Markdown + HTML 혼합 출력 → Dify Dataset API (자동 임베딩)

### 최종 목표
- ✅ PDF 문서를 RAG 시스템에 최적화된 형태로 파싱
- ✅ **Markdown + HTML 혼합 출력**으로 문서 구조 보존
- ✅ 표(Table)의 복잡도에 따라 Markdown 또는 JSON으로 자동 분리
- ✅ 복잡한 표는 **AI 요약** 생성하여 검색 정확도 향상
- ✅ 헤딩 기반 청킹 및 메타데이터 자동 생성
- ✅ FastAPI 백엔드 + CLI 인터페이스 제공
- ✅ **Dify Dataset API**를 통한 자동 임베딩 및 벡터 검색
- ✅ Dify 지식베이스 자동 업로드 시스템 제공 (Phase 11)

---

## 🎯 프로젝트 아키텍처

### 출력 구조

```
output/
└── {doc_name}/                    # 문서명 폴더
    ├── content.md                 # Markdown 본문 (청킹 메타데이터 포함)
    ├── manifest.json              # 청킹 순서 및 메타데이터
    └── tables/                    # 복잡한 표 저장 폴더
        ├── table_001.json
        ├── table_002.json
        └── ...
```

### 핵심 기능

1. **Markdown + HTML 혼합 출력**: 문서 구조(표, 리스트, 헤딩)를 보존하면서 RAG 최적화
2. **헤딩 기반 청킹**: Markdown 헤딩(#, ##, ###)을 기준으로 의미 단위 분리
3. **표 복잡도 자동 판단**: 4x4 이상 또는 병합 셀 포함 시 JSON 분리 + AI 요약 생성
4. **메타데이터 주입**: HTML 주석으로 chunk_id, page, table_ref 삽입
5. **순서 보장**: manifest.json에 chunk_order 배열로 문서 구조 보존
6. **Dify 자동 임베딩**: Dify Dataset API가 Markdown + HTML을 텍스트로 변환하여 임베딩 생성
7. **검색 최적화**: 표 AI 요약을 청크에 포함하여 벡터 검색 정확도 극대화

---

## 📅 전체 구현 타임라인

| Phase | 주제 | 예상 기간 | 우선순위 | 진행 상태 |
|-------|------|-----------|----------|----------|
| Phase 1 | 환경 설정 및 검증 | 1-2일 | 🔴 필수 | ✅ 완료 |
| Phase 2 | 기본 파싱 구현 | 2-3일 | 🔴 필수 | ✅ 완료 |
| Phase 3 | 표 추출 및 복잡도 판단 | 3-4일 | 🔴 필수 | ✅ 완료 |
| Phase 4 | SQLite 데이터베이스 통합 | 2-3일 | 🔴 필수 | ⏸️ 대기 |
| Phase 5 | 헤딩 기반 청킹 구현 | 2-3일 | 🔴 필수 | ⏸️ 대기 |
| Phase 6 | 메타데이터 및 manifest 생성 | 2-3일 | 🔴 필수 | ⏸️ 대기 |
| Phase 7 | CLI 인터페이스 구현 | 1-2일 | 🟡 중요 | ⏸️ 대기 |
| Phase 8 | 표 요약 생성 (AI) | 2-3일 | 🟡 중요 | ⏸️ 대기 |
| Phase 9 | RAG 시스템 통합 | 3-5일 | 🟢 선택 | ⏸️ 대기 |
| Phase 10 | 최적화 및 성능 테스트 | 3-5일 | 🟢 선택 | ⏸️ 대기 |
| Phase 11 | Dify 지식베이스 업로드 | 2-3일 | 🟡 중요 | ⏸️ 대기 |

**총 예상 기간**: 5-6주 (핵심 기능만: 2-3주)
**현재 진행률**: Phase 1-3 완료 (27% 완료)

---

## 🚀 Phase 1: 환경 설정 및 검증

### 목표
Python 환경, Docling 라이브러리, FastAPI 백엔드의 기본 구조를 설정하고 정상 동작을 검증합니다.

**⚠️ 중요**: Docling 라이브러리를 **직접 호출**하는 방식입니다. docling-serve를 사용하지 않습니다.

### 구현 범위
- Python 가상 환경 생성
- Docling 라이브러리 직접 설치 (docling-serve 제외)
- FastAPI 기본 프로젝트 구조 생성
- 샘플 PDF 파일 준비

### 체크리스트

#### 1.1 Python 환경 설정
- [x] Python 3.9 이상 설치 확인 (`python --version`)
- [x] Python 3.13 권장 (현재 프로젝트 버전)
- [x] pip 최신 버전 확인 (`pip --version`)
- [x] `backend/` 디렉토리 생성 (이미 존재하면 건너뛰기)
- [x] Python 가상 환경 생성 (`python -m venv venv`)
- [x] 가상 환경 활성화 (Windows PowerShell: `.\venv\Scripts\Activate.ps1`)
- [x] 활성화 확인 (프롬프트에 `(venv)` 표시)

#### 1.2 Docling 라이브러리 설치
- [x] Docling 라이브러리 설치 (`pip install docling`)
- [x] Docling-IBM-Models 설치 (`pip install docling-ibm-models`) - VLM pipeline용
- [x] EasyOCR 설치 (`pip install easyocr`) - OCR 기능용
- [x] 설치 확인 (`pip list | findstr docling`)

#### 1.3 Docling 라이브러리 테스트
- [x] Python에서 Docling import 테스트
- [x] DocumentConverter 인스턴스 생성 테스트
- [x] VLM pipeline 초기화 확인
- [x] 첫 실행 시 모델 다운로드 시간 예상 (수 분 소요)

#### 1.4 FastAPI 프로젝트 구조
- [x] `backend/app/` 디렉토리 생성 (이미 존재하면 건너뛰기)
- [x] `backend/app/__init__.py` 생성 (빈 파일)
- [x] `backend/app/main.py` 스켈레톤 작성
- [x] `backend/requirements.txt` 작성:
  - `fastapi==0.115.0`
  - `uvicorn[standard]==0.32.0`
  - `python-multipart==0.0.12`
  - `python-dotenv==1.0.1`
  - `pydantic==2.10.3`
  - `docling>=2.5.0`
  - `docling-ibm-models`
  - `easyocr`
- [x] `backend/.env` 파일 생성 (환경 변수 설정용)
- [x] FastAPI 의존성 설치 (`pip install -r requirements.txt`)

#### 1.5 테스트 문서 준비
- [x] `/docu` 폴더 존재 확인
- [x] 기본 PDF 파일 준비 (1-5 페이지, 텍스트 위주)
- [x] 테이블 포함 PDF 파일 준비 (sample2_bokmu.pdf 확인됨)
- [ ] 이미지 포함 PDF 파일 준비 (선택사항)
- [x] 샘플 파일이 `/docu` 폴더에 배치됨

### 성공 기준
- ✅ Python 가상 환경이 정상 작동
- ✅ Docling 라이브러리가 import 가능
- ✅ DocumentConverter가 정상적으로 초기화됨
- ✅ VLM 모델이 다운로드됨 (첫 실행 시)
- ✅ FastAPI 서버가 실행되며 기본 엔드포인트 응답
- ✅ 최소 2개 이상의 테스트 PDF 파일 준비 완료

### 검증 방법
```powershell
# Python 및 Docling 확인 (PowerShell)
python -c "from docling.document_converter import DocumentConverter; print('Docling OK')"

# DocumentConverter 초기화 테스트
python -c "from docling.document_converter import DocumentConverter; dc = DocumentConverter(); print('VLM Pipeline OK')"

# FastAPI 서버 실행 테스트
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# http://localhost:8000 접속 확인
```

---

## 🚀 Phase 2: 기본 파싱 구현 (Docling → Markdown)

### 목표
Docling 라이브러리를 **직접 호출**하여 PDF를 Markdown으로 변환하는 기본 파싱 기능을 구현합니다.

**⚠️ 중요**: Docling API 서버를 거치지 않고, 라이브러리를 in-process로 직접 호출합니다.

**⚠️ 출력 형식 전략 (2025-10-15 업데이트)**:
- **Markdown 최적화 출력**: Docling의 `export_to_markdown()` 메서드를 파라미터로 최적화
  - `escape_html=False`: HTML 태그 허용 (구조 보존)
  - `strict_text=False`: Markdown 포맷팅 유지 (헤딩, 리스트 등)
  - `image_mode`: 이미지 참조 모드 제어 (placeholder/embedded/referenced)
  - `enable_chart_tables=True`: 차트 테이블 처리 활성화
- **Context7 MCP 활용**: 최신 Docling 라이브러리 문서로 구현 검증 완료
- **구조 보존**: 표, 리스트, 헤딩 계층 구조를 최대한 보존
- **임베딩 변환**: Dify Dataset API가 업로드 시 자동으로 순수 텍스트로 변환

### 구현 범위
- DocumentConverter 초기화 (VLM pipeline 포함)
- PDF → Markdown + HTML 변환 함수 (라이브러리 직접 호출)
- 기본 Markdown + HTML 출력 저장
- FastAPI 엔드포인트 연동

### 체크리스트

#### 2.1 Docling 파싱 함수 구현
- [x] `backend/app/main.py`에 `parse_document_with_docling()` 함수 작성
- [x] DocumentConverter 인스턴스 생성 (함수 내에서 생성, 재사용 가능하도록 개선 필요)
- [x] VLM pipeline 설정:
  - `PipelineOptions` 설정 (OCR, table mode 등)
  - `vlm_model` 선택 (granite, smoldocling 등)
  - Standard PDF Pipeline (fast) 기본 사용
- [x] `convert()` 메서드로 PDF 파싱 (경로 전달)
- [x] **`export_to_markdown()` 메서드로 Markdown 최적화 출력**:
  - [x] `escape_html=False` 옵션 추가 (HTML 태그 허용)
  - [x] `strict_text` 옵션 추가 (순수 텍스트 모드 제어)
  - [x] `image_mode` 옵션 추가 (placeholder/embedded/referenced)
  - [x] `enable_chart_tables` 옵션 추가 (차트 테이블 활성화)
  - [x] `image_placeholder` 커스터마이징 지원
  - [x] `indent` 옵션 추가 (들여쓰기 제어)
  - [x] Context7 MCP로 최신 Docling 문서 확인 완료
  - [x] export_to_html(), export_to_json() 지원 완료
- [x] 에러 핸들링 추가:
  - 파일 없음 에러
  - 변환 실패 에러
  - 타임아웃 에러

#### 2.2 FastAPI 엔드포인트 구현
- [x] `GET /` - API 상태 확인
  - 현재 파싱 모드 표시 ("library_direct")
  - 버전 정보 반환
- [x] `GET /documents` - `/docu` 폴더의 문서 목록 조회
  - 지원 형식: `.pdf`, `.docx`, `.pptx`, `.html`
  - 파일 크기 정보 포함
- [x] `POST /parse` - 단일 문서 Markdown 변환
  - 라이브러리 직접 호출 방식
  - `parse_document_with_docling()` 함수 사용
- [x] Pydantic 모델 정의:
  - `ParseRequest`: filename, options (do_ocr, table_mode, vlm_model 등)
  - `ParseResponse`: success, content, stats, saved_to, error
  - `DocumentInfo`: filename, size, extension
  - `TableParsingOptions`: Phase 3 옵션 포함
- [x] CORS 미들웨어 설정 (Next.js 연동 대비)

#### 2.3 기본 Markdown 출력
- [x] 초기에는 `/docu` 폴더에 저장 (예: `sample.md`)
- [x] 파일명 규칙: `{원본파일명}.md` (또는 .html, .json)
- [x] UTF-8 인코딩으로 저장 (Windows 환경 주의)
- [x] 통계 정보 수집:
  - 라인 수 (`lines`)
  - 단어 수 (`words`)
  - 문자 수 (`characters`)
  - 파일 크기 (`size_kb`)

#### 2.4 테스트 (Scenario 1: 기본 PDF → Markdown)
- [x] `POST /parse` 요청으로 `sample.pdf` 변환
- [x] HTTP 200 응답 확인
- [x] `success: true` 확인
- [x] Markdown 파일 생성 확인
- [x] Markdown 품질 검증:
  - [x] 제목이 `#`, `##`, `###` 형식으로 변환됨
  - [x] 단락 구분이 적절함 (`\n\n`)
  - [x] 리스트가 `-` 또는 `1.` 형식으로 변환됨
  - [x] HTML 태그가 포함되지 않음 (순수 Markdown 출력)
  - [x] 특수 문자가 올바르게 처리됨

### 성공 기준
- ✅ PDF 파일이 Markdown으로 정상 변환됨 (라이브러리 직접 호출)
- ✅ 텍스트 추출 정확도 95% 이상
- ✅ 문서 구조(제목, 단락, 목록)가 Markdown 형식으로 보존됨
- ✅ FastAPI 엔드포인트가 정상 동작
- ✅ VLM pipeline이 안정적으로 작동

### 검증 방법
```powershell
# API 테스트 (PowerShell)
$body = @{
    filename = "sample.pdf"
    options = @{
        do_ocr = $true
        output_format = "markdown"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body

# Markdown 파일 확인
cat docu/sample.md
```

---

## 🚀 Phase 3: 표 추출 및 복잡도 판단

### 목표
PDF 문서에서 표를 추출하고, 복잡도에 따라 Markdown 테이블 또는 JSON으로 분리하는 로직을 구현합니다.

**⚠️ 핵심 파싱 전략**:
- **Markdown + HTML 혼합 출력**: 구조적 정보를 보존하기 위해 Markdown과 HTML을 함께 사용
- **구조 보존 우선**: 표, 리스트, 헤딩 계층 구조를 최대한 보존
- **임베딩 시 변환**: 벡터 임베딩 생성 시 순수 텍스트로 변환하거나 AI 요약 활용 (Dify Dataset API가 처리)

### 구현 범위
- 표 추출 로직 구현
- 표 복잡도 판단 알고리즘
- 단순 표 → Markdown 테이블 변환
- 복잡 표 → JSON 파일 저장 (AI 요약 포함)
- Markdown + HTML 혼합 출력으로 구조 보존

### 체크리스트

#### 3.1 표 추출 로직
- [x] Docling의 `TableItem` 추출
- [x] 각 표의 행/열 개수 확인
- [x] 병합 셀 정보 추출 (rowspan, colspan)
- [x] 표 캡션/제목 추출 (있는 경우)
- [x] 페이지 번호 매핑

#### 3.2 표 복잡도 판단 알고리즘
- [x] `is_complex_table(table)` 함수 구현
- [x] 크기 체크: 4x4 이상이면 복잡
- [x] 병합 셀 체크: rowspan > 1 또는 colspan > 1이면 복잡
- [ ] 다층 헤더 체크 (선택)
- [x] 복잡도 판단 결과 반환 (boolean)

#### 3.3 단순 표 → Markdown 테이블
- [x] Markdown 테이블 문법 생성 (`| col1 | col2 |`)
- [x] 헤더 구분선 생성 (`|------|------|`)
- [x] 각 행을 Markdown 행으로 변환
- [x] Markdown 본문에 인라인으로 포함

#### 3.4 복잡 표 → JSON 파일
- [x] `tables/` 디렉토리 생성
- [x] 표 ID 생성 (`table_001`, `table_002`, ...)
- [x] JSON 스키마 정의:
  - `table_id`, `chunk_id`, `page`, `caption`
  - `complexity`: `rows`, `cols`, `has_merged_cells`, `is_complex`
  - `structure`: `headers`, `rows` (셀 배열)
  - `summary`: AI 요약 필드 (Phase 8에서 추가)
- [x] JSON 파일로 저장 (`tables/table_001.json`)
- [x] Markdown 본문에 참조 추가 (`> **Table 001**: ...`)

#### 3.5 Markdown + HTML 혼합 출력 구현
- [x] Docling의 `export_to_markdown()` 옵션 설정:
  - HTML 태그 포함 옵션 활성화
  - 표를 HTML `<table>` 태그로 보존 (복잡한 경우)
  - 리스트를 HTML `<ul>`, `<ol>` 태그로 보존 (필요 시)
- [x] 단순 표는 Markdown 테이블 문법 유지
- [x] 복잡한 표는 HTML 테이블로 보존 또는 JSON 분리
- [x] 출력 검증: Markdown + HTML 혼합 형식 확인

#### 3.6 테스트 (Scenario 2: 테이블 포함 PDF)
- [x] 테이블 포함 PDF 파싱 (sample2_bokmu.pdf 파싱 완료)
- [x] 단순 표가 Markdown 테이블로 변환됨
- [x] 복잡 표가 JSON으로 분리됨 (3개 표: table_001.json, table_002.json, table_003.json)
- [x] JSON 파일 구조 검증 (table_id, page, complexity, structure 확인됨)
- [x] Markdown에 표 참조가 포함됨 (`> **Table 001** (see tables/table_001.json)`)

### 성공 기준
- ✅ 표의 행/열 구조가 올바르게 인식됨
- ✅ 4x4 이상 또는 병합 셀 포함 표가 JSON으로 분리됨
- ✅ 단순 표가 Markdown 테이블 문법으로 변환됨
- ✅ JSON 파일이 정의된 스키마에 맞게 생성됨
- ✅ Markdown에서 JSON 표를 참조 가능

### 검증 방법
```bash
# 테이블 포함 PDF 파싱
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"filename": "document-with-tables.pdf"}'

# 출력 구조 확인
ls output/document-with-tables/
# content.md, tables/table_001.json 확인

# JSON 파일 확인
cat output/document-with-tables/tables/table_001.json
```

---

## 🚀 Phase 4: SQLite 데이터베이스 통합

### 목표
파싱 문서 메타데이터와 청크, 표 정보를 SQLite 데이터베이스로 관리하여 검색, 히스토리 관리, 관계 추적을 용이하게 합니다.

**⚠️ 핵심 전략**:
- **파일 + DB 하이브리드**: Markdown/JSON 파일은 유지하되, 메타데이터는 SQLite로 관리
- **관계형 데이터 모델**: 문서 → 청크 → 표의 관계를 명확히 정의
- **히스토리 관리**: 파싱 히스토리, 재파싱 추적, 버전 관리
- **검색 최적화**: 메타데이터 기반 빠른 검색 (full-text search 지원)

### 구현 범위
- SQLite 데이터베이스 스키마 설계
- SQLAlchemy ORM 설정
- 테이블 정의 (documents, chunks, tables, parsing_history)
- CRUD 함수 구현
- FastAPI 엔드포인트 연동
- 기존 파일 저장소와 병행 운영

### 데이터베이스 스키마

#### 테이블 구조

```sql
-- 1. documents: 문서 메타데이터
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL UNIQUE,
    original_path TEXT NOT NULL,
    file_size INTEGER,
    file_extension TEXT,
    total_pages INTEGER,
    parsing_status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    parsing_strategy TEXT,  -- docling, camelot, hybrid
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_parsed_at DATETIME,
    output_folder TEXT,
    content_md_path TEXT,
    manifest_json_path TEXT
);

-- 2. chunks: 청크 메타데이터
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id TEXT NOT NULL,  -- chunk_001, chunk_002, ...
    chunk_index INTEGER NOT NULL,
    heading_level INTEGER,
    heading_text TEXT,
    content_preview TEXT,  -- 처음 200자
    char_count INTEGER,
    word_count INTEGER,
    page_start INTEGER,
    page_end INTEGER,
    has_table BOOLEAN DEFAULT 0,
    has_image BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE (document_id, chunk_id)
);

-- 3. tables: 표 메타데이터
CREATE TABLE tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,  -- 표가 속한 청크
    table_id TEXT NOT NULL,  -- table_001, table_002, ...
    table_index INTEGER NOT NULL,
    page INTEGER,
    caption TEXT,
    rows INTEGER,
    cols INTEGER,
    has_merged_cells BOOLEAN DEFAULT 0,
    is_complex BOOLEAN DEFAULT 0,
    complexity_score REAL,
    summary TEXT,  -- AI 요약 (Phase 8에서 추가)
    json_path TEXT,  -- tables/table_001.json
    parsing_method TEXT,  -- docling, camelot_lattice, camelot_stream
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL,
    UNIQUE (document_id, table_id)
);

-- 4. parsing_history: 파싱 히스토리
CREATE TABLE parsing_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    parsing_status TEXT NOT NULL,  -- started, completed, failed
    parsing_strategy TEXT,
    options_json TEXT,  -- 파싱 옵션 JSON
    total_chunks INTEGER,
    total_tables INTEGER,
    markdown_tables INTEGER,
    json_tables INTEGER,
    error_message TEXT,
    duration_seconds REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 5. pictures: 그림 메타데이터 (선택)
CREATE TABLE pictures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    picture_id TEXT NOT NULL,
    page INTEGER,
    width INTEGER,
    height INTEGER,
    area INTEGER,
    description TEXT,  -- VLM Picture Description
    image_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE SET NULL,
    UNIQUE (document_id, picture_id)
);

-- 인덱스
CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_status ON documents(parsing_status);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_chunk_id ON chunks(chunk_id);
CREATE INDEX idx_tables_document_id ON tables(document_id);
CREATE INDEX idx_tables_table_id ON tables(table_id);
CREATE INDEX idx_parsing_history_document_id ON parsing_history(document_id);
CREATE INDEX idx_pictures_document_id ON pictures(document_id);
```

### 체크리스트

#### 4.1 SQLAlchemy 설치 및 설정
- [x] `requirements.txt`에 추가:
  - `sqlalchemy==2.0.36`
  - `alembic==1.14.0` (마이그레이션 도구)
- [x] 의존성 설치: `pip install sqlalchemy alembic`
- [x] `backend/app/database.py` 파일 생성
- [x] SQLAlchemy 엔진 설정:
  - 데이터베이스 경로: `../parsing_app.db` (프로젝트 루트)
  - `echo=True` 옵션 (개발 시)
- [x] Session 관리 설정 (sessionmaker)
- [ ] `.env` 파일에 DATABASE_URL 추가 (선택)

#### 4.2 데이터베이스 스키마 정의
- [x] `backend/app/db_models.py` 파일 생성
- [x] SQLAlchemy 모델 정의:
  - [x] `Document` 모델 (documents 테이블)
  - [x] `Chunk` 모델 (chunks 테이블)
  - [x] `Table` 모델 (tables 테이블)
  - [x] `ParsingHistory` 모델 (parsing_history 테이블)
  - [x] `Picture` 모델 (pictures 테이블, 선택)
- [x] 관계 정의:
  - `Document.chunks` (one-to-many)
  - `Document.tables` (one-to-many)
  - `Document.parsing_history` (one-to-many)
  - `Chunk.tables` (one-to-many)
- [x] Pydantic 스키마 정의 (API 응답용):
  - `DocumentSchema`, `ChunkSchema`, `TableSchema` 등 (backend/app/schemas.py)

#### 4.3 데이터베이스 초기화
- [x] `backend/app/init_db.py` 스크립트 작성
- [x] `create_all()` 함수로 테이블 생성
- [ ] 초기 데이터 삽입 (선택)
- [x] 데이터베이스 존재 확인 로직
- [x] FastAPI 시작 시 자동 초기화 (lifespan 이벤트)

#### 4.4 CRUD 함수 구현
- [x] `backend/app/crud.py` 파일 생성
- [x] Document CRUD:
  - `create_document()`: 새 문서 등록
  - `get_document_by_id()`: ID로 문서 조회
  - `get_document_by_filename()`: 파일명으로 조회
  - `update_document()`: 문서 메타데이터 업데이트
  - `delete_document()`: 문서 삭제
  - `list_documents()`: 모든 문서 목록
  - `get_document_with_counts()`: 문서 + 통계 조회
- [x] Chunk CRUD:
  - `create_chunk()`: 청크 생성
  - `create_chunks_bulk()`: 청크 일괄 생성
  - `get_chunks_by_document_id()`: 문서의 모든 청크 조회
  - `get_chunk_by_chunk_id()`: chunk_id로 조회
- [x] Table CRUD:
  - `create_table()`: 표 메타데이터 생성
  - `create_tables_bulk()`: 표 일괄 생성
  - `get_tables_by_document_id()`: 문서의 모든 표 조회
  - `get_table_by_table_id()`: table_id로 조회
  - `update_table_summary()`: AI 요약 업데이트 (Phase 8)
- [x] ParsingHistory CRUD:
  - `create_parsing_history()`: 파싱 히스토리 생성
  - `get_parsing_history()`: 문서 파싱 히스토리 조회
- [x] Picture CRUD:
  - `create_picture()`: 그림 생성
  - `create_pictures_bulk()`: 그림 일괄 생성
  - `get_pictures_by_document_id()`: 문서의 모든 그림 조회

#### 4.5 FastAPI 엔드포인트 연동
- [x] `POST /parse` 엔드포인트 수정:
  - [x] 파싱 시작 시 Document 레코드 생성 (`status=processing`)
  - [x] 파싱 완료 시 Document 업데이트 (`status=completed`)
  - [x] 청크, 표 메타데이터 자동 저장 (표는 완료, 청크는 Phase 5에서)
  - [x] ParsingHistory 레코드 생성
- [ ] `GET /documents` 엔드포인트 수정 (기존 파일 기반 → DB 기반 조회로 전환은 Phase 5 이후):
  - 데이터베이스에서 문서 목록 조회
  - 파싱 상태, 청크 수, 표 수 포함
- [x] 새 엔드포인트 추가 (backend/app/api/database.py):
  - `GET /db/documents`: 문서 목록 조회
  - `GET /db/documents/{document_id}`: 문서 상세 조회
  - `GET /db/documents/{document_id}/chunks`: 문서의 청크 목록
  - `GET /db/documents/{document_id}/tables`: 문서의 표 목록
  - `GET /db/documents/{document_id}/history`: 파싱 히스토리
  - `DELETE /db/documents/{document_id}`: 문서 삭제 (DB only)

#### 4.6 기존 파일 저장과 병행
- [x] 파일 기반 저장 유지:
  - [x] `output/{doc_name}/content.md`
  - [ ] `output/{doc_name}/manifest.json` (Phase 6에서 구현)
  - [x] `output/{doc_name}/tables/*.json`
- [x] DB에는 메타데이터만 저장
- [x] 파일 경로를 DB에 저장 (`content_md_path`, `json_path` 등)
- [x] 파일과 DB 간 동기화 로직 (parsing.py에서 구현)
- [x] 파일 삭제 시 DB 레코드도 삭제 (cascade delete 검증 완료)

#### 4.7 Alembic 마이그레이션 설정 (선택)
- [ ] `alembic init alembic` 실행
- [ ] `alembic/env.py` 설정
- [ ] 초기 마이그레이션 생성:
  - `alembic revision --autogenerate -m "Initial schema"`
- [ ] 마이그레이션 적용:
  - `alembic upgrade head`
- [ ] 향후 스키마 변경 시 마이그레이션 사용

#### 4.8 테스트
- [x] 데이터베이스 초기화 테스트 (5개 테이블 정상 생성 확인)
- [x] Document 생성 및 조회 테스트 (Receipt-2735-7794-5160.pdf)
- [x] `POST /parse` 실행 후 DB 레코드 확인 (status: completed)
- [ ] 청크, 표 메타데이터 저장 확인 (Phase 5에서 청킹 구현 후)
- [x] ParsingHistory 레코드 생성 확인 (duration: 6.21초)
- [x] 문서 삭제 시 cascade 동작 확인 (Document 1 삭제 → ParsingHistory 자동 삭제 검증 완료)
- [x] 파일과 DB 동기화 확인 (output_folder, content_md_path 저장됨)

### 성공 기준
- ✅ SQLite 데이터베이스가 정상 생성됨 (C:\workspace\parsing-app\parsing_app.db)
- ✅ 모든 테이블이 정의된 스키마에 맞게 생성됨 (documents, chunks, tables, parsing_history, pictures)
- ✅ 파싱 시 자동으로 DB에 메타데이터 저장됨 (POST /parse 연동 완료)
- ✅ FastAPI 엔드포인트에서 DB 조회 가능 (GET /db/documents/* 구현 완료)
- ✅ 파일 기반 저장과 병행 운영됨 (파일: content.md/tables/*.json, DB: 메타데이터)
- ✅ 관계형 데이터 무결성 유지 (foreign key, cascade delete 검증 완료)
- ✅ 파싱 히스토리 추적 가능 (POST /parse 연동 완료, duration/options 저장)

### 검증 방법

#### 데이터베이스 초기화 확인
```powershell
# FastAPI 시작 시 자동 생성
cd backend
python -m uvicorn app.main:app --reload

# DB 파일 확인
ls ../parsing_app.db

# SQLite CLI로 확인 (선택)
sqlite3 ../parsing_app.db
.tables
.schema documents
.quit
```

#### 파싱 후 DB 확인
```powershell
# 문서 파싱
$body = @{ filename = "sample.pdf" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body

# 문서 목록 조회 (DB에서)
Invoke-RestMethod -Uri "http://localhost:8000/documents" -Method Get

# 특정 문서 상세 조회
Invoke-RestMethod -Uri "http://localhost:8000/documents/1" -Method Get

# 청크 목록 조회
Invoke-RestMethod -Uri "http://localhost:8000/documents/1/chunks" -Method Get

# 표 목록 조회
Invoke-RestMethod -Uri "http://localhost:8000/documents/1/tables" -Method Get

# 파싱 히스토리 조회
Invoke-RestMethod -Uri "http://localhost:8000/documents/1/history" -Method Get
```

#### SQLite 직접 쿼리
```powershell
# PowerShell에서 SQLite 쿼리 (sqlite3 CLI 설치 필요)
sqlite3 ../parsing_app.db "SELECT * FROM documents;"
sqlite3 ../parsing_app.db "SELECT chunk_id, heading_text FROM chunks WHERE document_id=1;"
sqlite3 ../parsing_app.db "SELECT table_id, rows, cols, is_complex FROM tables WHERE document_id=1;"
```

### 플로우 다이어그램

```
POST /parse (sample.pdf)
    ↓
1. Document 레코드 생성 (status=processing)
    ↓
2. Docling/Camelot 파싱 실행
    ↓
3. 파일 저장 (content.md, tables/*.json)
    ↓
4. 청크 메타데이터 추출
    ↓
5. Chunk 레코드 생성 (bulk insert)
    ↓
6. 표 메타데이터 추출
    ↓
7. Table 레코드 생성 (bulk insert)
    ↓
8. Document 업데이트 (status=completed)
    ↓
9. ParsingHistory 레코드 생성
    ↓
10. ParseResponse 반환 (success=true)
```

### 에러 처리 플로우

```
파싱 실패 시:
    ↓
1. Document 업데이트 (status=failed)
    ↓
2. ParsingHistory 생성 (error_message 포함)
    ↓
3. ParseResponse 반환 (success=false)
```

### 핵심 가치

#### 왜 SQLite인가?

1. **메타데이터 관리 최적화**
   - 파일 기반: 전체 파일을 읽어야 검색 가능
   - DB 기반: 인덱스를 통한 빠른 검색

2. **히스토리 추적**
   - 언제, 어떤 옵션으로 파싱했는지 추적
   - 재파싱 시 이전 결과와 비교

3. **관계 관리**
   - 문서 → 청크 → 표의 관계를 명확히 정의
   - 외래 키로 데이터 무결성 보장

4. **확장성**
   - 향후 full-text search 추가 가능
   - 통계, 분석 쿼리 용이

5. **Dify 통합 준비**
   - Phase 11에서 Dify 업로드 시 DB에서 메타데이터 조회
   - 업로드 상태 추적 (uploaded, pending 등)

#### 파일 vs DB 역할 분담

| 항목 | 파일 (Markdown/JSON) | DB (SQLite) |
|------|---------------------|-------------|
| 청크 본문 | ✅ content.md | ❌ (preview만) |
| 표 구조 | ✅ tables/*.json | ❌ (경로만) |
| 메타데이터 | ✅ manifest.json | ✅ (주 저장소) |
| 검색 | ❌ (느림) | ✅ (인덱스) |
| 히스토리 | ❌ | ✅ |
| 관계 관리 | ❌ | ✅ |

---

## 🚀 Phase 5: 헤딩 기반 청킹 구현

### 목표
Markdown 헤딩(#, ##, ###)을 기준으로 의미 단위로 청킹하는 로직을 구현합니다.

**⚠️ RAG 최적화 청킹 전략**:
- **구조 보존**: Markdown + HTML 혼합 형식으로 청크 저장 (표, 리스트 구조 유지)
- **임베딩 변환**: Dify Dataset API에 업로드 시 순수 텍스트로 자동 변환
- **AI 요약 활용**: 복잡한 표는 AI 요약을 청크에 포함하여 검색 정확도 향상
- **OpenAI 실무 관행**: 문서 원본은 구조 보존, 임베딩 시점에 텍스트 변환

### 구현 범위
- 헤딩 패턴 매칭 (정규표현식)
- 헤딩별로 콘텐츠 분리
- 청크 ID 자동 생성
- 청크 메타데이터 수집
- Markdown + HTML 혼합 형식 유지

### 체크리스트

#### 4.1 헤딩 기반 청킹 알고리즘
- [ ] `chunk_by_heading(markdown_content)` 함수 구현
- [ ] 헤딩 패턴 정규표현식 (`^(#{1,6})\s+(.+)$`)
- [ ] Markdown 줄 단위로 순회
- [ ] 헤딩 발견 시 이전 청크 저장 및 새 청크 시작
- [ ] 헤딩 레벨 및 텍스트 추출
- [ ] 마지막 청크 저장

#### 4.2 청크 ID 생성
- [ ] 청크 ID 형식: `chunk_001`, `chunk_002`, ...
- [ ] 3자리 제로 패딩 (`{chunk_id_counter:03d}`)
- [ ] 헤딩 없는 상단 콘텐츠는 `chunk_000`
- [ ] 각 청크에 고유 ID 부여

#### 4.3 청크 메타데이터 수집
- [ ] `chunk_id`: 고유 식별자
- [ ] `chunk_index`: 순서 (0부터 시작)
- [ ] `heading_level`: 헤딩 레벨 (1=#, 2=##, 3=###)
- [ ] `heading_text`: 헤딩 텍스트 (섹션 제목)
- [ ] `content`: 청크 본문 텍스트 (Markdown + HTML 혼합 형식)
- [ ] `char_count`, `word_count`: 청크 크기
- [ ] `has_table`: 표 포함 여부
- [ ] `table_refs`: 참조하는 표 ID 배열

#### 4.4 Markdown + HTML 구조 보존
- [ ] 청크 분리 시 HTML 태그 유지
- [ ] 표 구조(HTML `<table>`)를 청크 내에 보존
- [ ] 리스트 구조(HTML `<ul>`, `<ol>`)를 청크 내에 보존
- [ ] 청크 경계에서 HTML 태그가 깨지지 않도록 처리
- [ ] 순수 텍스트 변환은 Dify API에 위임

#### 4.5 페이지 번호 매핑
- [ ] Docling의 페이지 정보 추출
- [ ] 각 청크의 시작/끝 페이지 매핑
- [ ] `page_start`, `page_end` 필드 추가
- [ ] 페이지 범위 계산

#### 4.6 테스트
- [ ] 다양한 헤딩 레벨이 있는 문서 테스트
- [ ] 헤딩 없는 문서 테스트 (chunk_000만 생성)
- [ ] 중첩된 헤딩 구조 테스트
- [ ] 청크 개수 확인
- [ ] 각 청크의 메타데이터 확인

### 성공 기준
- ✅ 모든 헤딩이 청크 경계로 인식됨
- ✅ 헤딩 레벨이 올바르게 추출됨 (1-6)
- ✅ 각 청크에 고유 ID가 부여됨
- ✅ 청크 순서가 문서 순서와 일치함
- ✅ 청크 크기 정보가 정확함

### 검증 방법
```python
# 청킹 테스트
markdown = read_file("sample.md")
chunks = chunk_by_heading(markdown)

print(f"총 청크 개수: {len(chunks)}")
for chunk in chunks:
    print(f"{chunk.chunk_id}: {chunk.heading_text} (level {chunk.heading_level})")
```

---

## 🚀 Phase 6: 메타데이터 주입 및 manifest.json 생성

### 목표
청크에 HTML 주석으로 메타데이터를 주입하고, manifest.json 파일을 생성하여 전체 문서 구조를 보존합니다.

### 구현 범위
- HTML 주석 형태 메타데이터 주입
- 표 참조(table_ref) 연결
- manifest.json 스키마 정의 및 생성
- content.md 파일 저장

### 체크리스트

#### 5.1 메타데이터 주입
- [ ] `inject_metadata(chunk, page, table_refs)` 함수 구현
- [ ] HTML 주석 생성:
  - `<!-- chunk_id: chunk_001 -->`
  - `<!-- page: 1 -->`
  - `<!-- table_ref: table_001 -->` (있는 경우)
- [ ] 메타데이터를 청크 본문 상단에 삽입
- [ ] 여러 표 참조가 있는 경우 모두 주입

#### 5.2 표 참조 연결
- [ ] 각 청크가 참조하는 JSON 표 ID 추적
- [ ] 청크 내에 표가 있는지 확인 (`has_table`)
- [ ] `table_refs` 배열에 표 ID 추가
- [ ] Markdown에 표 참조 문구 추가 (`> **Table 001**: ...`)

#### 5.3 content.md 파일 생성
- [ ] 모든 청크를 순서대로 결합
- [ ] 각 청크 사이에 구분자 추가 (선택)
- [ ] `output/{doc_name}/content.md` 경로에 저장
- [ ] UTF-8 인코딩으로 저장

#### 5.4 manifest.json 스키마 정의
- [ ] 최상위 필드:
  - `document_name`: 원본 파일명
  - `total_pages`: 총 페이지 수
  - `total_chunks`: 총 청크 수
  - `parsing_date`: 파싱 일시 (ISO 8601)
- [ ] `chunk_order` 배열:
  - 각 청크의 메타데이터 포함
  - 문서 순서대로 정렬
- [ ] `table_summary`:
  - `total_tables`: 총 표 개수
  - `markdown_tables`: Markdown 테이블 개수
  - `json_tables`: JSON 표 개수
  - `json_table_ids`: JSON 표 ID 배열

#### 5.5 manifest.json 생성
- [ ] 청크 메타데이터 수집
- [ ] 표 통계 계산
- [ ] JSON 구조 생성
- [ ] `output/{doc_name}/manifest.json` 저장
- [ ] JSON 들여쓰기 2칸으로 저장 (가독성)

#### 5.6 테스트
- [ ] content.md에 메타데이터 주석이 포함됨
- [ ] manifest.json이 정의된 스키마에 맞게 생성됨
- [ ] chunk_order 배열 순서 확인
- [ ] table_summary 통계 확인
- [ ] JSON 파일 유효성 검증

### 성공 기준
- ✅ 모든 청크에 메타데이터가 주입됨
- ✅ 표 참조가 올바르게 연결됨
- ✅ manifest.json이 정의된 스키마에 맞게 생성됨
- ✅ chunk_order가 문서 순서를 정확히 보존함
- ✅ 파일 구조가 `output/{doc_name}/` 규칙을 따름

### 검증 방법
```bash
# 출력 구조 확인
ls output/sample/
# content.md, manifest.json, tables/ 확인

# content.md에서 메타데이터 확인
head -n 10 output/sample/content.md
# <!-- chunk_id: chunk_001 --> 등 확인

# manifest.json 확인
cat output/sample/manifest.json | jq
```

---

## 🚀 Phase 7: CLI 인터페이스 구현

### 목표
커맨드라인에서 간편하게 문서를 파싱할 수 있는 CLI 인터페이스를 구현합니다.

### 구현 범위
- argparse 기반 CLI 구현
- 입력/출력 파라미터 처리
- 파싱 옵션 설정
- 진행 상황 표시

### 체크리스트

#### 6.1 CLI 인수 정의
- [ ] `--input` (필수): 입력 PDF 파일 경로
- [ ] `--output` (선택): 출력 디렉토리 경로 (기본값: `output/`)
- [ ] `--chunk-by` (선택): 청킹 방식 (`heading`, `page`, `token`)
- [ ] `--table-threshold` (선택): 복잡한 표 판단 크기 (기본값: 4)
- [ ] `--generate-summary` (선택): 표 요약 생성 여부 (기본값: False)
- [ ] `--vlm-model` (선택): VLM 모델 선택 (기본값: `granite`)

#### 6.2 CLI 스크립트 구현
- [ ] `backend/app/cli.py` 파일 생성
- [ ] argparse 설정
- [ ] 인수 파싱 및 검증
- [ ] 파일 존재 확인
- [ ] 출력 디렉토리 생성
- [ ] 메인 파싱 함수 호출

#### 6.3 진행 상황 표시
- [ ] tqdm 라이브러리 설치 (`pip install tqdm`)
- [ ] 파싱 진행률 표시
- [ ] 단계별 메시지 출력:
  - "📄 Parsing PDF..."
  - "📊 Extracting tables..."
  - "✂️ Chunking by headings..."
  - "💾 Saving output..."
- [ ] 완료 메시지 및 통계 표시

#### 6.4 에러 핸들링
- [ ] 파일 없음 에러 처리
- [ ] 파싱 실패 에러 처리
- [ ] 디스크 쓰기 에러 처리
- [ ] 사용자 친화적 에러 메시지

#### 6.5 사용 예제 작성
- [ ] README 또는 별도 문서에 CLI 사용법 추가
- [ ] 기본 사용법 예제
- [ ] 고급 옵션 예제
- [ ] 배치 처리 예제

#### 6.6 테스트
- [ ] `--help` 옵션 확인
- [ ] 기본 인수로 실행 (`--input sample.pdf`)
- [ ] 모든 옵션 지정하여 실행
- [ ] 잘못된 파일 경로로 실행 (에러 확인)
- [ ] 출력 파일 확인

### 성공 기준
- ✅ CLI가 정상적으로 실행됨
- ✅ 모든 인수가 올바르게 처리됨
- ✅ 진행 상황이 시각적으로 표시됨
- ✅ 에러가 사용자 친화적으로 처리됨
- ✅ 출력이 예상대로 생성됨

### 검증 방법
```bash
# 기본 사용법
python backend/app/cli.py --input docu/sample.pdf

# 모든 옵션 사용
python backend/app/cli.py \
  --input docu/sample.pdf \
  --output results/ \
  --chunk-by heading \
  --table-threshold 4 \
  --generate-summary

# 도움말 확인
python backend/app/cli.py --help
```

---

## 🚀 Phase 8: 표 요약 생성 (AI 통합)

### 목표
복잡한 표에 대해 AI를 활용하여 자연어 요약을 생성하고, 벡터 검색에 최적화합니다.

**⚠️ AI 요약 기반 청킹 전략**:
- **표 구조 보존**: 원본 표는 Markdown/JSON으로 보존
- **검색 최적화**: AI 요약을 청크에 추가하여 벡터 임베딩 품질 향상
- **Dify 통합**: 표 요약이 포함된 청크를 Dify Dataset API로 업로드
- **실무 관행**: 구조화된 데이터(표)는 AI 요약으로 자연어 변환하여 검색 정확도 극대화

### 구현 범위
- AI API 연동 (OpenAI, Anthropic 등)
- 표 → 자연어 요약 생성
- JSON 파일에 summary 필드 추가
- 요약 품질 검증
- 청크에 표 요약 통합

### 체크리스트

#### 7.1 AI API 연동
- [ ] OpenAI 또는 Anthropic API 키 설정 (.env)
- [ ] API 클라이언트 초기화
- [ ] 요약 생성 함수 구현 (`generate_table_summary()`)
- [ ] API 호출 에러 핸들링

#### 7.2 프롬프트 설계
- [ ] 표 요약 프롬프트 작성:
  - "Summarize the following table in 2-3 sentences."
  - "Focus on key insights, trends, or patterns."
- [ ] 표 구조를 텍스트로 변환
- [ ] 헤더, 샘플 데이터 포함
- [ ] 캡션/제목 포함 (있는 경우)

#### 7.3 요약 생성 로직
- [ ] 복잡한 표만 요약 생성 (단순 표는 skip)
- [ ] 표 데이터를 AI API에 전송
- [ ] 요약 결과 수신 및 검증
- [ ] JSON 파일의 `summary` 필드에 저장
- [ ] 실패 시 기본 요약 사용 (예: "Table containing X rows and Y columns")

#### 7.4 청크에 표 요약 통합
- [ ] 청크 생성 시 table_ref 확인
- [ ] 참조된 표의 summary 필드 로드
- [ ] 청크 콘텐츠에 표 요약 추가:
  - 형식: `\n\n**Table Summary (table_001)**: [AI 요약 텍스트]\n\n`
  - 위치: 표 참조 바로 다음 또는 청크 끝
- [ ] 여러 표가 있는 경우 모든 요약 추가
- [ ] manifest.json에 표 요약 포함 여부 기록

#### 7.5 요약 품질 검증
- [ ] 요약 길이 확인 (최소 10자, 최대 500자)
- [ ] 특수 문자 제거/정규화
- [ ] 표 내용과의 관련성 확인 (선택)
- [ ] 요약이 없는 경우 경고 로그

#### 7.6 CLI 옵션 추가
- [ ] `--generate-summary` 플래그 구현
- [ ] 플래그가 있는 경우에만 AI 요약 생성
- [ ] 기본값은 False (비용 절감)
- [ ] 진행 상황 메시지 추가 ("🤖 Generating AI summaries...")

#### 7.7 테스트
- [ ] 단일 표에 대해 요약 생성
- [ ] 여러 표가 있는 문서 테스트
- [ ] 요약 품질 확인 (수동)
- [ ] API 호출 실패 시 에러 처리 확인
- [ ] `--generate-summary` 플래그 동작 확인

### 성공 기준
- ✅ AI API가 정상적으로 호출됨
- ✅ 표 요약이 2-3 문장으로 생성됨
- ✅ 요약이 표 내용과 관련성이 높음
- ✅ JSON 파일에 summary 필드가 추가됨
- ✅ API 비용이 합리적인 범위 내

### 검증 방법
```bash
# AI 요약 생성
python backend/app/cli.py \
  --input docu/document-with-tables.pdf \
  --generate-summary

# JSON 파일에서 요약 확인
cat output/document-with-tables/tables/table_001.json | jq '.summary'
```

---

## 🚀 Phase 9: RAG 시스템 통합

### 목표
파싱된 문서를 RAG 시스템에 통합하여 벡터 임베딩 생성, 검색, 문맥 복원이 가능하도록 합니다.

**⚠️ Dify Dataset API 기반 임베딩 전략**:
- **임베딩 처리는 Dify가 담당**: 청크를 Dify Dataset API로 업로드하면 Dify가 자동으로 임베딩 생성
- **텍스트 변환 자동화**: Dify API가 Markdown + HTML을 순수 텍스트로 변환하여 임베딩
- **벡터 DB 불필요**: Dify 내장 벡터 DB 사용 (별도 Pinecone/Weaviate 불필요)
- **검색 최적화**: Dify의 semantic_search, reranking 기능 활용

### 구현 범위
- ~~청크 단위 벡터 임베딩 생성~~ (Dify API가 처리)
- ~~표 요약 임베딩 및 검색~~ (Dify API가 처리)
- 문맥 복원 로직 (manifest.json 활용)
- ~~벡터 DB 연동 (선택)~~ (Dify 내장 DB 사용)

### 체크리스트

#### 8.1 ~~벡터 임베딩 생성~~ (Dify API가 자동 처리)
- [x] ~~OpenAI Embeddings API 또는 Sentence Transformers 선택~~ (Dify가 처리)
- [x] ~~`create_embeddings_from_chunks()` 함수 구현~~ (불필요)
- [x] ~~각 청크에 대해 임베딩 생성~~ (Dify가 자동 처리)
- [x] ~~임베딩 결과 저장~~ (Dify 내장 벡터 DB에 저장)

**Note**: Phase 11의 Dify Dataset API 업로드로 대체됨

#### 8.2 ~~표 요약 임베딩~~ (Dify API가 자동 처리)
- [x] ~~표 요약 텍스트 추출~~ (Phase 8에서 처리)
- [x] ~~표 요약에 대해 임베딩 생성~~ (Dify가 처리)
- [x] ~~표 ID와 임베딩 매핑~~ (metadata로 전달)
- [x] ~~표 검색 함수 구현~~ (Dify API 사용)

**Note**: 표 요약은 청크에 포함되어 Dify로 업로드됨

#### 8.3 문맥 복원 로직
- [ ] `reconstruct_context(chunk_id, manifest, content)` 함수 구현
- [ ] manifest.json에서 청크 순서 정보 로드
- [ ] 현재 청크 인덱스 찾기
- [ ] 이전/다음 청크 포함 (윈도우 크기 설정)
- [ ] 청크 텍스트 추출 및 결합
- [ ] 구분자로 청크 분리 (`\n\n---\n\n`)

#### 8.4 ~~벡터 DB 연동~~ (Dify 내장 DB 사용)
- [x] ~~벡터 DB 선택~~ (Dify 내장 벡터 DB 사용)
- [x] ~~DB 클라이언트 초기화~~ (Dify API 클라이언트 사용)
- [x] ~~임베딩 업로드~~ (Phase 11에서 처리)
- [x] ~~메타데이터 포함~~ (Dify API payload에 포함)

**Note**: Phase 11의 Dify 업로드 시스템으로 대체됨

#### 8.5 통합 테스트 (Dify 기반)
- [ ] 문서 파싱 → Dify 업로드 → 검색 전체 플로우 테스트
- [ ] Dify API로 샘플 쿼리 검색 테스트
- [ ] 문맥 복원 테스트 (manifest.json 활용)
- [ ] 표 요약 포함 청크 검색 테스트
- [ ] Dify semantic_search + reranking 정확도 평가

### 성공 기준
- ✅ ~~모든 청크에 대해 임베딩 생성됨~~ (Dify가 자동 처리)
- ✅ ~~표 요약이 검색 가능함~~ (Dify API로 검색)
- ✅ 문맥 복원이 정상 작동함 (manifest.json 기반)
- ✅ ~~검색 결과가 관련성 높음~~ (Dify semantic_search + reranking)
- ✅ ~~벡터 DB 연동이 안정적임~~ (Dify 내장 DB 사용)
- ✅ Dify Dataset API 업로드가 정상 작동함 (Phase 11)

### 검증 방법
```powershell
# Phase 11: Dify 업로드 테스트
python app/upload_to_dify.py --manifest ../output/sample/manifest.json --content ../output/sample/content.md

# Dify API로 검색 테스트 (httpx 사용)
$body = @{
    query = "시스템 성능 메트릭"
    retrieval_model = @{
        search_method = "semantic_search"
        reranking_enable = $true
        top_k = 3
        score_threshold = 0.7
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost/v1/datasets/$env:DIFY_DATASET_ID/retrieve" -Method Post -Headers @{Authorization="Bearer $env:DIFY_API_KEY"} -ContentType "application/json" -Body $body

# 문맥 복원 테스트
python -c "from app.main import reconstruct_context; print(reconstruct_context('chunk_005', 'output/sample/manifest.json', 'output/sample/content.md'))"
```

---

## 🚀 Phase 10: 최적화 및 성능 테스트

### 목표
대용량 문서 처리 최적화, 메모리 사용량 개선, 다양한 문서 형식 테스트를 수행합니다.

### 구현 범위
- 성능 벤치마크
- 메모리 최적화
- 다양한 문서 형식 테스트
- 에러 리커버리 개선

### 체크리스트

#### 9.1 성능 벤치마크
- [ ] 소형 문서 (1-10 페이지) 처리 시간 측정
- [ ] 중형 문서 (10-50 페이지) 처리 시간 측정
- [ ] 대형 문서 (50-200 페이지) 처리 시간 측정
- [ ] 목표 시간 달성 여부 확인:
  - 소형: < 30초
  - 중형: < 2분
  - 대형: < 10분

#### 9.2 메모리 최적화
- [ ] 메모리 프로파일링 (`memory_profiler`)
- [ ] 대용량 파일 처리 시 메모리 사용량 확인
- [ ] 스트리밍 처리 구현 (필요 시)
- [ ] 청크 단위 처리로 메모리 절감
- [ ] 가비지 컬렉션 최적화

#### 9.3 다양한 문서 형식 테스트
- [ ] PDF (텍스트, 이미지, 하이브리드)
- [ ] DOCX
- [ ] PPTX
- [ ] HTML
- [ ] 스캔 이미지 (OCR)
- [ ] 다국어 문서 (한글, 영어, 일본어 등)

#### 9.4 에러 리커버리 개선
- [ ] 부분 파싱 실패 시 계속 진행
- [ ] 에러 로그 상세화
- [ ] 실패한 표/청크 건너뛰기
- [ ] 최종 요약 보고서 생성 (성공/실패 통계)

#### 9.5 청크 크기 검증
- [ ] 평균 청크 크기 확인 (200-500 단어 목표)
- [ ] 너무 큰 청크 분리 로직 추가 (선택)
- [ ] 너무 작은 청크 병합 로직 추가 (선택)
- [ ] 청크 크기 분포 분석

#### 9.6 최종 통합 테스트
- [ ] 실제 프로덕션 문서로 테스트 (10개 이상)
- [ ] 파싱 성공률 측정
- [ ] Markdown 품질 검증
- [ ] 표 추출 정확도 확인
- [ ] RAG 검색 정확도 평가

### 성공 기준
- ✅ 성능 목표 달성 (소형 < 30초, 중형 < 2분)
- ✅ 메모리 사용량이 합리적 범위 내
- ✅ 다양한 문서 형식 지원
- ✅ 파싱 성공률 95% 이상
- ✅ 에러 처리가 안정적

### 검증 방법
```bash
# 성능 테스트
time python backend/app/cli.py --input docu/large-document.pdf

# 메모리 프로파일링
mprof run python backend/app/cli.py --input docu/large-document.pdf
mprof plot

# 배치 테스트
for file in docu/*.pdf; do
    python backend/app/cli.py --input "$file"
done
```

---

## 🚀 Phase 11: Dify 지식베이스 자동 업로드

### 목표
Docling 파싱 결과를 셀프호스팅 Dify의 지식베이스(Dataset)에 자동 업로드하는 시스템을 구현합니다.

### 구현 범위
- Dify API 연동
- manifest.json 청크 단위 업로드
- 표 데이터 요약 통합 업로드
- 자동 재시도 및 진행 상황 로깅
- CLI 인터페이스 제공

### 체크리스트

#### 10.1 Dify API 환경 설정
- [ ] `.env` 파일에 Dify API 설정 추가:
  - `DIFY_API_BASE`: Dify API 베이스 URL
  - `DIFY_API_KEY`: Dataset API 키
  - `DIFY_DATASET_ID`: 업로드할 Dataset ID
- [ ] Dify API 옵션 설정:
  - `DIFY_INDEXING_TECHNIQUE`: 인덱싱 기법 (기본값: `high_quality`)
  - `DIFY_DOC_LANGUAGE`: 문서 언어 (기본값: `Korean`)
  - `DIFY_SEARCH_METHOD`: 검색 방법 (기본값: `semantic_search`)
  - `DIFY_TOP_K`: 검색 결과 개수 (기본값: `3`)
  - `DIFY_SCORE_THRESHOLD`: 유사도 임계값 (기본값: `0.7`)
  - `DIFY_RERANKING_ENABLE`: 재랭킹 활성화 (기본값: `true`)
- [ ] 재시도 설정:
  - `DIFY_MAX_RETRIES`: 최대 재시도 횟수 (기본값: `3`)
  - `DIFY_RETRY_DELAY`: 재시도 대기 시간(초) (기본값: `2`)

#### 10.2 DifyUploader 클래스 구현
- [ ] `backend/app/dify_uploader.py` 파일 생성
- [ ] `DifyUploader` 클래스 구현:
  - `__init__()`: manifest.json, content.md, tables/ 경로 로드
  - `_load_manifest()`: manifest.json 파일 로드
  - `_load_content()`: content.md 파일 로드
  - `_load_table_summary()`: 표 JSON에서 summary 로드
  - `_extract_chunk_content()`: content.md에서 청크 추출
  - `_create_payload()`: Dify API payload 생성
  - `_upload_chunk()`: 단일 청크 업로드 (재시도 포함)
  - `upload_all()`: 모든 청크 업로드
- [ ] httpx 라이브러리 사용 (비동기 HTTP 클라이언트)
- [ ] python-dotenv로 환경변수 로드

#### 10.3 청크 추출 및 payload 생성
- [ ] HTML 주석 파싱으로 chunk_id 추출
- [ ] 정규표현식으로 청크 콘텐츠 분리
- [ ] table_ref가 있는 경우 표 요약 추가:
  - tables/table_xxx.json 파일 읽기
  - summary 필드 추출
  - 청크 콘텐츠에 표 요약 추가
- [ ] Dify API payload 생성:
  - `name`: 청크 이름 (chunk_id + heading_text)
  - `text`: 청크 콘텐츠 + 표 요약
  - `metadata`: chunk_id, page, has_table, table_refs, heading_level 등
  - `retrieval_model`: 검색 설정 (semantic_search, reranking 등)

#### 10.4 Dify API 호출
- [ ] `POST /v1/datasets/{dataset_id}/documents/create_by_text` 엔드포인트 호출
- [ ] 요청 헤더 설정:
  - `Authorization: Bearer {api_key}`
  - `Content-Type: application/json`
- [ ] 응답 처리:
  - 성공 (200 OK): document_id 추출
  - 실패 (4xx/5xx): 에러 메시지 파싱
- [ ] 재시도 로직 구현:
  - 네트워크 타임아웃 시 재시도
  - 5xx 서버 에러 시 재시도
  - 429 Too Many Requests 시 재시도
  - 4xx 클라이언트 에러 시 재시도 안 함 (401, 400 등)
  - 지수 백오프 전략 (재시도 간격 증가)

#### 10.5 CLI 스크립트 구현
- [ ] `backend/app/upload_to_dify.py` 파일 생성
- [ ] argparse 기반 CLI 인터페이스:
  - `--manifest`: manifest.json 파일 경로 (필수)
  - `--content`: content.md 파일 경로 (필수)
  - `--tables`: tables/ 디렉토리 경로 (선택)
  - `--dry-run`: 실제 업로드 없이 테스트 (선택)
  - `--chunks`: 업로드할 청크 ID 목록 (선택)
  - `--batch-size`: 배치 업로드 크기 (선택, 기본값: 10)
  - `--verbose`: 상세 로그 출력 (선택)
- [ ] 파일 존재 확인
- [ ] DifyUploader 초기화 및 업로드 실행
- [ ] 종료 코드 처리 (성공: 0, 실패: 1)

#### 10.6 진행 상황 표시
- [ ] tqdm 라이브러리로 진행률 표시
- [ ] 실시간 업로드 상태 출력:
  - 현재 청크 ID
  - 생성된 document_id
  - 실패한 청크 표시
- [ ] 최종 요약 통계:
  - 총 청크 수
  - 성공 개수
  - 실패 개수
  - 실패한 청크 목록

#### 10.7 에러 처리 및 로깅
- [ ] 에러 타입별 처리:
  - 환경변수 미설정 에러
  - 파일 없음 에러
  - API 인증 에러
  - 네트워크 에러
  - 타임아웃 에러
- [ ] 로깅 시스템 구축:
  - `logging` 모듈 사용
  - 파일 로그 (`dify_upload.log`)
  - 콘솔 로그 (INFO, ERROR)
  - 상세 디버그 로그 (--verbose)

#### 10.8 의존성 추가
- [ ] `requirements.txt`에 추가:
  - `httpx==0.28.1`
  - `tqdm==4.67.1`
  - `python-dotenv==1.1.1`
- [ ] 의존성 설치: `pip install httpx tqdm python-dotenv`

#### 10.9 테스트
- [ ] 환경변수 설정 확인
- [ ] Dry-run 모드 테스트 (`--dry-run`)
- [ ] 소형 문서 (10 청크) 업로드 테스트
- [ ] 표 포함 문서 (25 청크) 업로드 테스트
- [ ] 특정 청크만 업로드 테스트 (`--chunks chunk_001 chunk_002`)
- [ ] 네트워크 에러 시뮬레이션 (잘못된 API URL)
- [ ] 재시도 로직 확인
- [ ] 실패한 청크 처리 확인

### 성공 기준
- ✅ Dify API 연동이 정상 작동함
- ✅ 모든 청크가 개별 문서로 업로드됨
- ✅ 표 요약이 청크에 통합됨
- ✅ 메타데이터가 Dify에 저장됨
- ✅ 재시도 로직이 안정적으로 작동함
- ✅ 진행 상황이 실시간으로 표시됨
- ✅ 실패한 청크가 명확히 표시됨

### 검증 방법

#### 기본 업로드
```powershell
# 환경변수 설정 (.env 파일 또는 직접 설정)
$env:DIFY_API_KEY="dataset-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:DIFY_DATASET_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# 업로드 실행
cd backend
python app/upload_to_dify.py --manifest ../output/sample/manifest.json --content ../output/sample/content.md
```

#### Dry-run 테스트
```powershell
python app/upload_to_dify.py `
  --manifest ../output/sample/manifest.json `
  --content ../output/sample/content.md `
  --dry-run
```

#### 특정 청크만 업로드
```powershell
python app/upload_to_dify.py `
  --manifest ../output/sample/manifest.json `
  --content ../output/sample/content.md `
  --chunks chunk_001 chunk_002 chunk_005
```

#### 상세 로그 출력
```powershell
python app/upload_to_dify.py `
  --manifest ../output/sample/manifest.json `
  --content ../output/sample/content.md `
  --verbose
```

### 예상 출력

```
============================================================
📤 Uploading 50 chunks to Dify...
============================================================

Uploading: 100%|████████████████████| 50/50 [00:45<00:00,  1.11chunk/s]

============================================================
📊 Upload Summary
============================================================
Total chunks: 50
Successful: 50
Failed: 0

✅ All chunks uploaded successfully!
```

### 플로우 다이어그램

```
manifest.json → chunk_order 배열 로드
     ↓
content.md → 전체 Markdown 로드
     ↓
각 청크 순회 (chunk_order)
     ↓
청크 추출 (HTML 주석 파싱)
     ↓
table_ref 확인
     ↓
┌────────┴────────┐
│                 │
있음            없음
│                 │
↓                 │
table JSON 로드   │
summary 추가      │
│                 │
└────────┬────────┘
         ↓
Dify API payload 생성
         ↓
POST /documents/create_by_text
         ↓
┌────────┴────────┐
│                 │
성공            실패
│                 │
↓                 ↓
로그 저장      재시도 (최대 3회)
                  ↓
            ┌─────┴─────┐
            │           │
          성공        실패
            │           │
            └─────┬─────┘
                  ↓
            에러 로그 저장
```

---

## 📊 전체 검증 기준

### 기능적 성공 기준
- ✅ PDF 문서가 RAG 최적화된 형태로 파싱됨
- ✅ 표의 복잡도에 따라 Markdown/JSON으로 자동 분리됨
- ✅ 헤딩 기반 청킹이 정상 작동함
- ✅ 메타데이터가 올바르게 주입됨
- ✅ manifest.json이 문서 구조를 보존함
- ✅ CLI 인터페이스가 사용자 친화적임
- ✅ AI 표 요약이 의미 있음 (선택)
- ✅ RAG 시스템 통합이 가능함 (선택)
- ✅ Dify 지식베이스 업로드가 정상 작동함 (Phase 10)

### 성능 성공 기준
- ✅ 소형 문서 (1-10 페이지): < 30초
- ✅ 중형 문서 (10-50 페이지): < 2분
- ✅ 대형 문서 (50-200 페이지): < 10분
- ✅ 평균 청크 크기: 200-500 단어
- ✅ 파싱 성공률: 95% 이상

### Markdown 품질 성공 기준
- ✅ 제목 계층 구조 보존 (#, ##, ###)
- ✅ 테이블이 Markdown 테이블 또는 JSON으로 변환됨
- ✅ HTML 태그가 포함되지 않음 (순수 Markdown)
- ✅ 특수 문자가 올바르게 처리됨
- ✅ AI가 쉽게 이해할 수 있는 구조적 텍스트

---

## 🛠️ 문제 해결 가이드

### 자주 발생하는 문제

#### 문제 1: Docling 모델 다운로드 시간
**증상**: 첫 번째 파싱 시 매우 오래 걸림

**해결**:
- 첫 실행 시 VLM 모델을 다운로드하므로 시간이 걸립니다
- 이후 실행은 빠름 (모델 캐싱)
- 사전 다운로드를 원하면 별도 스크립트 실행

#### 문제 2: 메모리 부족
**증상**: 대용량 PDF 처리 시 OOM 에러

**해결**:
- 페이지 범위 지정으로 분할 처리
- 스트리밍 파싱 구현 (선택)
- 청크 크기 줄이기
- 메모리 제한이 있는 환경에서는 배치 크기 축소

#### 문제 3: 표가 인식되지 않음
**증상**: 테이블이 일반 텍스트로 변환됨

**해결**:
- `table_mode: accurate` 사용
- `do_table_structure: true` 설정
- OCR 활성화 (`do_ocr: true`)
- PDF가 텍스트 기반인지 확인 (이미지 기반 표는 OCR 필요)

#### 문제 4: 청크 크기가 불균등
**증상**: 어떤 청크는 너무 크고 어떤 청크는 너무 작음

**해결**:
- 헤딩 구조가 불균등한 경우 발생
- 청크 크기 제한 로직 추가 (Phase 10)
- 또는 `--chunk-by token` 옵션 사용 (고정 크기)

#### 문제 5: AI 요약 비용
**증상**: AI API 비용이 과다함

**해결**:
- `--generate-summary` 플래그를 선택적으로 사용
- 복잡한 표만 요약 생성 (단순 표 제외)
- 로컬 모델 사용 (HuggingFace Transformers)
- 배치 처리로 API 호출 최소화

---

## 📚 참고 자료

### 공식 문서
- **Docling**: https://docling-project.github.io/docling/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings

### RAG 시스템
- **LangChain**: https://python.langchain.com/docs/get_started/introduction
- **LlamaIndex**: https://docs.llamaindex.ai/en/stable/
- **Pinecone (Vector DB)**: https://www.pinecone.io/

### 벡터 임베딩
- **Sentence Transformers**: https://www.sbert.net/
- **ChromaDB**: https://docs.trychroma.com/

### Dify (Phase 11)
- **Dify 공식 문서**: https://docs.dify.ai/
- **Dify API Reference**: https://docs.dify.ai/api-reference
- **Dify Dataset API**: https://docs.dify.ai/api-reference/dataset
- **httpx**: https://www.python-httpx.org/
- **tqdm**: https://tqdm.github.io/
- **python-dotenv**: https://pypi.org/project/python-dotenv/

---

## 📝 다음 단계

### 즉시 시작 (Phase 1)
1. Python 환경 설정
2. Docling 라이브러리 설치
3. FastAPI 프로젝트 구조 생성
4. 샘플 PDF 파일 준비

### 단기 목표 (2주 이내)
1. Phase 1-6 완료 (핵심 기능 + DB 통합)
2. 기본 CLI 인터페이스 구현
3. 테스트 문서로 검증

### 중기 목표 (1개월 이내)
1. Phase 7-9 완료 (CLI + AI 요약 + RAG 통합)
2. 다양한 문서 형식 테스트
3. 성능 최적화

### 장기 목표 (2개월 이내)
1. Phase 10-11 완료 (최적화 + Dify 업로드)
2. Dify 지식베이스와 완전 통합
3. 프로덕션 배포
4. 사용자 피드백 수집 및 개선

---

**작성일**: 2025-10-15
**최종 업데이트**: 2025-10-17
**버전**: 1.2 (SQLite 통합)
**상태**: 🚧 Phase 1-3 부분 완료, Phase 4-11 진행 중

**주요 특징**:
- ✅ 4개 문서 통합 (RAG 최적화 + FastAPI 구현 + 테스트 플랜 + Dify 업로드)
- ✅ **Docling 라이브러리 직접 호출** 방식 (docling-serve 불필요)
- ✅ **Markdown + HTML 혼합 출력**으로 문서 구조 보존
- ✅ **Dify Dataset API**를 통한 자동 임베딩 처리 (별도 벡터 DB 불필요)
- ✅ **AI 요약 기반** 표 검색 최적화 (OpenAI 실무 관행)
- ✅ 10개 Phase로 구조화된 순차적 구현 플랜
- ✅ 각 Phase마다 상세한 체크리스트 제공
- ✅ 명확한 성공 기준 및 검증 방법
- ✅ 문제 해결 가이드 포함
- ✅ 실용적인 타임라인 제시
- ✅ Windows PowerShell 환경 고려
- ✅ SQLite 데이터베이스 통합으로 메타데이터 관리 최적화 (Phase 4)
- ✅ Dify 지식베이스 자동 업로드 시스템 포함 (Phase 11)

**구현 현황** (2025-10-16):
- ✅ **Phase 1 완료**: Python 3.13 환경, Docling 라이브러리, FastAPI 구조 설정
- ✅ **Phase 2 완료**: PDF → Markdown/HTML/JSON 변환, 최적화 파라미터 지원
- ✅ **Phase 3 완료**: 표 추출, 복잡도 판단, JSON 분리, HTML 테이블 Serializer
- ⏸️ **Phase 4-11 대기**: SQLite DB 통합, 헤딩 기반 청킹, manifest.json, CLI, AI 요약, RAG 통합

**아키텍처 결정**:
- 🚫 **사용하지 않음**: docling-serve (별도 API 서버), 별도 벡터 DB (Pinecone, Weaviate 등)
- ✅ **사용함**:
  - Docling 라이브러리 직접 import 및 호출
  - SQLite 데이터베이스 (메타데이터 관리, 히스토리 추적)
  - Markdown + HTML 혼합 출력 (구조 보존)
  - Dify Dataset API (임베딩 자동 처리)
  - AI 요약 (복잡한 표 검색 최적화)
- ✅ **장점**:
  - 단순한 배포, 낮은 지연시간, 적은 의존성
  - SQLite 기반 빠른 메타데이터 검색 및 히스토리 추적
  - 별도 벡터 DB 관리 불필요 (Dify 내장)
  - OpenAI 실무 관행 준수 (구조 보존 + 임베딩 시 변환)
