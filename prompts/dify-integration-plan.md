# Dify Knowledge Base Integration Plan

## Overview

파싱된 문서를 Dify Knowledge Base에 업로드하는 기능을 구현합니다. 사용자가 웹 UI를 통해 Dataset을 선택하고 파싱된 문서를 Dify에 업로드할 수 있습니다.

## Progress Summary

- ✅ **Phase 1-3 완료**: Frontend UI with mock data
- 🔄 **Phase 4-6 진행 중**: Backend API integration
- ⏳ **Phase 7-8 대기**: Testing & Documentation

## Reference Implementation

기존 CLI 스크립트 `dify_upload_document.py`를 참고하여 웹 기반 솔루션으로 확장합니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js)                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app/dify/page.tsx                                   │   │
│  │  - Dataset 목록 조회 UI                             │   │
│  │  - Dataset 선택 드롭다운                             │   │
│  │  - 파싱된 문서 선택 (output 폴더 기반)               │   │
│  │  - 업로드 실행 버튼                                  │   │
│  │  - 업로드 진행 상태 표시 (indexing status)           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  components/dify/                                    │   │
│  │  - DatasetSelector.tsx                               │   │
│  │  - ParsedDocumentSelector.tsx                        │   │
│  │  - UploadProgress.tsx                                │   │
│  │  - DifySettings.tsx                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  backend/app/api/dify.py                            │   │
│  │  - GET /dify/datasets (dataset 목록 조회)          │   │
│  │  - GET /dify/parsed-documents (output 폴더 스캔)   │   │
│  │  - POST /dify/upload (문서 업로드)                 │   │
│  │  - GET /dify/status/{batch_id} (indexing 상태)     │   │
│  │  - GET /dify/config (설정 조회)                    │   │
│  │  - POST /dify/config (설정 저장)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  backend/app/services/dify_service.py               │   │
│  │  - DifyClient 클래스                                │   │
│  │    * list_datasets()                                │   │
│  │    * upload_document(dataset_id, content, name)     │   │
│  │    * check_indexing_status(batch_id)                │   │
│  │    * list_documents(dataset_id)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  backend/app/schemas.py (ORM 추가)                  │   │
│  │  - DifyConfig 모델 (API key, base URL 저장)        │   │
│  │  - DifyUploadLog 모델 (업로드 히스토리)            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP
┌─────────────────────────────────────────────────────────────┐
│                    Dify API (External)                       │
│  - GET /v1/datasets (목록)                                  │
│  - POST /v1/datasets/{id}/document/create_by_text          │
│  - GET /v1/datasets/{id}/documents/{batch}/indexing-status │
└─────────────────────────────────────────────────────────────┘
```

## Dify API Endpoints (from official docs)

### Core Endpoints
1. **GET /v1/datasets?page=1&limit=20** - Dataset 목록 조회
2. **POST /v1/datasets/{dataset_id}/document/create_by_text** - 텍스트로 문서 생성
3. **POST /v1/datasets/{dataset_id}/document/create-by-file** - 파일로 문서 생성
4. **GET /v1/datasets/{dataset_id}/documents/{batch}/indexing-status** - 인덱싱 상태 확인
5. **GET /v1/datasets/{dataset_id}/documents** - 문서 목록 조회

### Authentication
```
Authorization: Bearer {api_key}
```

## Implementation Plan

> **Frontend-First Approach**: UI와 사용자 경험을 먼저 구현하고, 백엔드는 나중에 연결합니다.

### Phase 1: Frontend - Type Definitions & Mock Data ✅ COMPLETED

**Checklist:**
- ✅ TypeScript 타입 정의 완료 (`lib/types.ts`)
  - ✅ DifyConfig, DifyDataset, ParsedDocument
  - ✅ UploadRequest, UploadResponse, IndexingStatus
  - ✅ DocumentUploadStatus (배치 업로드용)
- ✅ Mock data 생성 완료 (`lib/mock-data.ts`)
  - ✅ MOCK_CONFIG, MOCK_DATASETS, MOCK_PARSED_DOCUMENTS

### Phase 2: Frontend - UI Components ✅ COMPLETED

**Checklist:**
- ✅ DifyConfiguration.tsx (설정 + Dataset 선택 통합)
- ✅ DatasetSelector.tsx (Dataset 선택 드롭다운)
- ✅ ParsedDocumentSelector.tsx (체크박스로 다중 선택 가능)
- ✅ DifyUploadProgress.tsx (업로드 진행상황 표시)
- ✅ UploadProgress.tsx (개별 문서 진행바)
- ✅ DifySettings.tsx (설정 모달용, 현재 미사용)

**Key Features:**
- ✅ API Key 및 Base URL 설정
- ✅ 연결 테스트 버튼
- ✅ Dataset 선택 드롭다운 (문서 개수, 단어 수 표시)
- ✅ 파싱된 문서 다중 선택 (체크박스)
- ✅ 배치 업로드 진행상황 실시간 표시
- ✅ 문서별 에러 처리

### Phase 3: Frontend - Main Page ✅ COMPLETED

**Checklist:**
- ✅ `app/dify/page.tsx` 구현 완료
- ✅ Mock data 기반 동작 확인
- ✅ 배치 업로드 시뮬레이션 구현
- ✅ 순차 업로드 로직 구현 (문서 하나씩 처리)
- ✅ 업로드 상태별 UI 처리 (waiting/uploading/completed/error)
- ✅ Cancel 버튼 추가
- ✅ 반응형 레이아웃 적용

**Navigation:**
- ✅ Sidebar에 "Dify Upload" 링크 추가됨

### Phase 4: Frontend - API Integration Layer ❌ TODO

**Files to modify:**
- `lib/api.ts` - Dify API 함수 추가

**Checklist:**
- ❌ `getDifyConfig()` - 저장된 설정 조회
- ❌ `saveDifyConfig(config)` - 설정 저장
- ❌ `testDifyConnection(config)` - 연결 테스트
- ❌ `listDatasets(config, page, limit)` - Dataset 목록 조회
- ❌ `listParsedDocuments()` - output 폴더의 파싱된 문서 목록
- ❌ `uploadToDify(request)` - 문서 업로드
- ❌ `getIndexingStatus(config, dataset_id, batch_id)` - 인덱싱 상태 확인

**Note:** Phase 4는 Phase 5-6 (Backend) 완료 후 진행

### Phase 5: Backend - Dify Service Layer ❌ TODO

**Files to create:**
- `backend/app/services/dify_service.py` - Dify API 클라이언트
- `backend/app/models.py` - Pydantic 모델 추가
- `backend/app/schemas.py` - ORM 모델 추가

**Checklist:**

**1. DifyClient 클래스** (`dify_service.py`)
- ❌ `__init__(api_key, base_url)` - 클라이언트 초기화
- ❌ `list_datasets(page, limit)` - GET /v1/datasets
- ❌ `create_document_by_text(dataset_id, name, text, indexing_technique)` - POST /v1/datasets/{id}/document/create_by_text
- ❌ `check_indexing_status(dataset_id, batch_id)` - GET /v1/datasets/{id}/documents/{batch}/indexing-status
- ❌ `test_connection()` - 연결 테스트 (datasets API 호출)
- ❌ Error handling (HTTPException 래핑)
- ❌ Request timeout 설정
- ❌ Logging (모든 API 호출 로그)

**2. Pydantic Models** (`models.py`)
- ❌ `DifyConfigModel` - API key, base_url
- ❌ `DifyDataset` - id, name, description, document_count, word_count, created_at
- ❌ `DifyUploadRequest` - dataset_id, document_path, document_name, indexing_technique
- ❌ `DifyUploadResponse` - document_id, batch_id, indexing_status, success
- ❌ `ParsedDocumentInfo` - path, name, size, created_at
- ❌ `IndexingStatusResponse` - id, indexing_status, completed_segments, total_segments

**3. ORM Models** (`schemas.py`)
- ❌ `DifyConfig` 테이블 - id, api_key, base_url, created_at, updated_at
- ❌ `DifyUploadLog` 테이블 - id, dataset_id, dataset_name, document_path, document_name, dify_document_id, batch_id, indexing_status, uploaded_at, completed_at

### Phase 6: Backend - API Endpoints ❌ TODO

**Files to create:**
- `backend/app/api/dify.py` - FastAPI router
- `backend/app/crud.py` - DB operations 추가
- `backend/app/main.py` - Router 등록

**Checklist:**

**API Endpoints** (`backend/app/api/dify.py`)
- ❌ `GET /dify/config` - 저장된 Dify 설정 조회
- ❌ `POST /dify/config` - Dify API 설정 저장/업데이트
- ❌ `POST /dify/test-connection` - 연결 테스트
- ❌ `GET /dify/datasets` - Dataset 목록 조회 (Dify API 호출)
- ❌ `GET /dify/parsed-documents` - output 폴더 스캔하여 파싱된 문서 목록
- ❌ `POST /dify/upload` - 파싱된 문서를 Dify에 업로드
- ❌ `GET /dify/status/{dataset_id}/{batch_id}` - 벡터화 진행 상태 확인
- ❌ `GET /dify/upload-history` - 업로드 히스토리 조회

**CRUD Functions** (`backend/app/crud.py`)
- ❌ `get_dify_config(db)` - 설정 조회
- ❌ `create_or_update_dify_config(db, config)` - 설정 저장/업데이트
- ❌ `create_upload_log(db, log_data)` - 업로드 로그 생성
- ❌ `update_upload_log(db, log_id, status, completed_at)` - 업로드 로그 업데이트
- ❌ `get_upload_history(db, limit)` - 업로드 히스토리 조회

**Router Registration** (`backend/app/main.py`)
- ❌ Import dify router
- ❌ Register router: `app.include_router(dify.router)`

**output 폴더 스캔 로직:**
- ❌ `output/` 폴더의 모든 하위 디렉토리 스캔
- ❌ 각 디렉토리에서 `.md` 파일 찾기
- ❌ 파일 메타데이터 추출 (size, created_at)
- ❌ ParsedDocumentInfo 리스트 반환

### Phase 7: Integration & Testing ❌ TODO

**Checklist:**

**Frontend Integration:**
- ❌ `lib/api.ts`에 Dify API 함수 추가
- ❌ `app/dify/page.tsx`에서 mock data 제거
- ❌ 실제 API 호출로 교체
- ❌ Error handling 추가 (try/catch)
- ❌ Loading states 추가
- ❌ Toast notifications 추가 (shadcn/ui)
- ❌ Status polling 구현 (인덱싱 진행률)

**End-to-End Testing:**
- ❌ 설정 저장/로드 테스트
- ❌ 연결 테스트 버튼 동작 확인
- ❌ Dataset 목록 불러오기
- ❌ 파싱된 문서 목록 불러오기
- ❌ 단일 문서 업로드
- ❌ 배치 업로드 (여러 문서)
- ❌ 인덱싱 상태 폴링
- ❌ 에러 처리 (잘못된 API key, 네트워크 오류 등)

**Database Migration:**
- ❌ alembic migration 생성 (DifyConfig, DifyUploadLog 테이블)
- ❌ migration 실행

### Phase 8: Documentation & Polish ❌ TODO

**Checklist:**

**Documentation:**
- ❌ `CLAUDE.md` 업데이트 (Dify 통합 설명)
- ❌ `backend/DIFY_INTEGRATION.md` 생성
  - ❌ Setup instructions
  - ❌ API key 발급 방법
  - ❌ 환경 변수 설정
  - ❌ Troubleshooting guide
- ❌ API endpoint 문서화 (FastAPI docs에 description 추가)

**UI Polish:**
- ❌ Loading skeleton screens
- ❌ Empty states (no datasets, no documents)
- ❌ Success/Error toast notifications
- ❌ 업로드 취소 기능 구현
- ❌ 반응형 디자인 검증
- ❌ Accessibility (a11y) 개선

**Performance:**
- ❌ API 호출 최적화 (불필요한 재요청 방지)
- ❌ 큰 문서 처리 시간 테스트
- ❌ 배치 업로드 성능 검증

---

## Quick Reference

### Phase Summary

| Phase | Status | Files | Estimated Time |
|-------|--------|-------|----------------|
| 1. Frontend Types | ✅ | lib/types.ts, lib/mock-data.ts | ~30min |
| 2. Frontend UI | ✅ | components/dify/*.tsx | ~3-4h |
| 3. Frontend Page | ✅ | app/dify/page.tsx | ~1-2h |
| 4. Frontend API | ❌ | lib/api.ts | ~1h |
| 5. Backend Service | ❌ | backend/app/services/dify_service.py | ~2-3h |
| 6. Backend API | ❌ | backend/app/api/dify.py | ~2-3h |
| 7. Integration | ❌ | Multiple files | ~1-2h |
| 8. Documentation | ❌ | *.md files | ~1h |

**Total Estimated: 11-16 hours** | **Completed: ~4-7 hours** | **Remaining: ~7-9 hours**

### Key Dify API Endpoints

```
GET    /v1/datasets?page=1&limit=20
POST   /v1/datasets/{id}/document/create_by_text
POST   /v1/datasets/{id}/document/create-by-file
GET    /v1/datasets/{id}/documents/{batch}/indexing-status
```

### Backend API Endpoints to Implement

```
GET    /dify/config
POST   /dify/config
POST   /dify/test-connection
GET    /dify/datasets
GET    /dify/parsed-documents
POST   /dify/upload
GET    /dify/status/{dataset_id}/{batch_id}
GET    /dify/upload-history
```

### Database Tables

```sql
-- Dify 설정
dify_config (id, api_key, base_url, created_at, updated_at)

-- 업로드 로그
dify_upload_logs (
  id, dataset_id, dataset_name, document_path, document_name,
  dify_document_id, batch_id, indexing_status,
  uploaded_at, completed_at
)
```

---

## Next Steps (Priority Order)

1. **Phase 5**: Backend Service Layer 구현
   - `dify_service.py` 생성
   - Pydantic 모델 추가
   - ORM 모델 추가

2. **Phase 6**: Backend API Endpoints 구현
   - `/dify/*` 엔드포인트 생성
   - CRUD 함수 추가
   - Router 등록

3. **Phase 4**: Frontend API Integration
   - `lib/api.ts`에 Dify 함수 추가
   - Frontend와 Backend 연결

4. **Phase 7**: Integration & Testing
   - E2E 테스트
   - 에러 처리 검증

5. **Phase 8**: Documentation & Polish
   - 문서 작성
   - UI 개선

---

## Success Criteria

✅ User can configure Dify API key via UI
✅ User can view list of available datasets
✅ User can select a parsed document from output folder
✅ User can upload document to selected dataset
✅ User can monitor vectorization progress
❌ Upload history is logged in database
❌ Proper error handling for all failure scenarios
✅ Responsive UI with loading/error states

---

## Future Enhancements (Out of Scope)

- File-based upload (현재는 text-based만 지원)
- Dataset creation from UI
- Document preview before upload
- Upload scheduling/automation
- Webhook integration for indexing completion
- Retry logic for failed uploads

---

**Last Updated:** 2025-01-29
**Current Phase:** Phase 4-6 (Backend Implementation)
