# Logging Standardization Checklist

**목표**: 4개 파싱 전략(Docling, Dolphin Remote, Remote OCR, MinerU)의 로그를 표준화하여 일관성과 유지보수성 향상

**예상 소요 시간**: 약 2시간 20분

---

## 📋 Phase 1: Logging Utility Module Creation (30분)

### Tasks
- [ ] `backend/app/utils/` 폴더 생성 (없는 경우)
- [ ] `backend/app/utils/__init__.py` 파일 생성
- [ ] `backend/app/utils/logging_utils.py` 파일 생성
  - [ ] `ParserLogger` 클래스 구현
    - [ ] `__init__()` - 초기화 메서드
    - [ ] `start()` - 파서 시작 로그
    - [ ] `step()` - 단계별 진행 로그
    - [ ] `sub_step()` - 하위 단계 로그
    - [ ] `detail()` - 상세 정보 로그
    - [ ] `page()` - 페이지 처리 로그
    - [ ] `remote_call()` - 원격 API 호출 로그
    - [ ] `success()` - 성공 완료 로그
    - [ ] `warning()` - 경고 로그
    - [ ] `error()` - 에러 로그
    - [ ] `resource_check()` - 리소스 확인 로그
  - [ ] 편의 함수 구현
    - [ ] `log_resource_available()`
    - [ ] `log_resource_unavailable()`

### Verification
- [ ] 모듈 import 테스트
- [ ] 각 메서드 기본 동작 확인

---

## 📋 Phase 2: Docling Parser Application (20분)

**파일**: `backend/app/services/docling.py`

### Changes Required

#### 1. Import 추가 (line 31 이후)
- [ ] `from app.utils.logging_utils import ParserLogger` 추가

#### 2. Function: `parse_document_with_docling()` (line 37)
- [ ] `parser_logger = ParserLogger("Docling", logger)` 초기화
- [ ] 파서 시작 로그 (line 37-51)
  - [ ] `parser_logger.start()` 호출
  - [ ] 설정 정보 전달 (output_format, do_ocr, ocr_engine, table_mode 등)

#### 3. OCR 설정 로그 교체 (line 62-83)
- [ ] Warning 로그 표준화 (line 62-63)
  - [ ] `parser_logger.warning()` 사용
- [ ] Info 로그 표준화 (line 70, 73, 80, 83)
  - [ ] 설정 정보는 `start()` 메서드에서 처리

#### 4. Smart Image Analysis 로그 교체 (line 96-127)
- [ ] Line 97: `parser_logger.sub_step()` 사용
- [ ] Line 124-126: 하위 설정은 `detail()` 사용

#### 5. Picture Description 로그 교체 (line 129-156)
- [ ] Line 130, 150: `parser_logger.sub_step()` 또는 `warning()` 사용

#### 6. 최종 처리 완료 로그 (line 230)
- [ ] `parser_logger.success()` 호출
- [ ] 메트릭 전달: 문자 수, 테이블 수 등

### Verification
- [ ] `parse_document_with_docling()` 테스트 실행
- [ ] 로그 출력 형식 확인
- [ ] 기존 기능 정상 동작 확인

---

## 📋 Phase 3: Dolphin Remote Parser Application (25분)

**파일**: `backend/app/services/dolphin_remote.py`

### Changes Required

#### 1. Import 추가 (line 18 이후)
- [ ] `from app.utils.logging_utils import ParserLogger` 추가

#### 2. Module-level 리소스 체크 (line 27-36)
- [ ] `log_resource_available()` / `log_resource_unavailable()` 사용
- [ ] Line 32, 34, 36 교체

#### 3. Function: `call_dolphin_gpu()` (line 39)
- [ ] Line 59-60: Remote API 호출 로그 표준화
  - [ ] `parser_logger.remote_call()` 사용 고려 (또는 유지)
- [ ] Line 75: 응답 로그 표준화

#### 4. Function: `parse_with_dolphin_remote()` (line 87)
- [ ] `parser_logger = ParserLogger("Dolphin Remote", logger)` 초기화
- [ ] 파서 시작 로그 (line 130-131)
  - [ ] `parser_logger.start()` 호출
  - [ ] 설정: gpu_server, parsing_level 등

#### 5. 단계별 로그 교체 (line 136-261)
- [ ] Line 142-143: GPU 서버 체크 → `step(1, 4, ...)`
- [ ] Line 147-156: PDF 변환 → `step(2, 4, ...)`
- [ ] Line 164-234: 페이지 처리 → `page()`, `step(3, 4, ...)` 사용
  - [ ] Line 170-176: Stage 1 로그 → `sub_step()`
  - [ ] Line 184: 요소 감지 → `detail()`
  - [ ] Line 193-223: Stage 2 로그 → `sub_step()`, `detail()`
- [ ] Line 238-241: 페이지 병합 → `step(4, 4, ...)`
- [ ] Line 254-261: 완료 로그 → `success()` with metrics

#### 6. 저장 로그 (line 264-270)
- [ ] Line 270: `parser_logger.sub_step()` 사용 고려

#### 7. Error 처리 (line 286-288)
- [ ] `parser_logger.error()` 사용

### Verification
- [ ] `parse_with_dolphin_remote()` 테스트 실행
- [ ] 2단계 파이프라인 로그 확인
- [ ] 페이지별 로그 형식 확인

---

## 📋 Phase 4: Remote OCR Parser Application (20분)

**파일**: `backend/app/services/remote_ocr_parser.py`

### Changes Required

#### 1. Import 추가 (line 23 이후)
- [ ] `from app.utils.logging_utils import ParserLogger` 추가

#### 2. Function: `parse_with_remote_ocr()` (line 29)
- [ ] `parser_logger = ParserLogger("Remote OCR", logger)` 초기화
- [ ] 파서 시작 로그 (line 63-65)
  - [ ] `parser_logger.start()` 호출
  - [ ] 설정: engine, languages 등

#### 3. 완료 로그 교체 (line 93-98)
- [ ] `parser_logger.success()` 사용
- [ ] 메트릭: pages, characters 등

#### 4. Error 처리 (line 102-104)
- [ ] `parser_logger.error()` 사용 (exc_info=True)

#### 5. Function: `_parse_pdf_with_remote_ocr()` (line 107)
- [ ] Line 124: PDF 변환 로그 → `parser_logger.step()` 고려
- [ ] Line 130: Pages 정보 → `parser_logger.detail()`
- [ ] Line 139-170: 페이지별 처리 → `parser_logger.page()`
  - [ ] Line 158-164: OCR 호출 및 결과 → `remote_call()`, `detail()`

#### 6. Function: `_parse_image_with_remote_ocr()` (line 191)
- [ ] Line 208-222: 처리 로그 표준화

### Verification
- [ ] PDF 파싱 테스트
- [ ] 이미지 파싱 테스트
- [ ] 페이지별 로그 확인

---

## 📋 Phase 5: MinerU Parser Application (20분)

**파일**: `backend/app/services/mineru_parser.py`

### Changes Required

#### 1. Import 추가 (line 26 이후)
- [ ] `from app.utils.logging_utils import ParserLogger` 추가

#### 2. Module-level 리소스 체크 (line 32-45)
- [ ] Line 41: Available 메시지 표준화
- [ ] Line 43-44: Unavailable 메시지 표준화

#### 3. Function: `parse_with_mineru()` (line 48)
- [ ] `parser_logger = ParserLogger("MinerU", logger)` 초기화
- [ ] 파서 시작 로그 (line 81)
  - [ ] `parser_logger.start()` 호출
  - [ ] 설정: version, lang, use_ocr 등

#### 4. 단계별 로그 교체 (line 107-155)
- [ ] Line 109: Step 1/4 → `parser_logger.step(1, 4, ...)`
- [ ] Line 119: Step 2/4 → `parser_logger.step(2, 4, ...)`
- [ ] Line 135: Step 3/4 → `parser_logger.step(3, 4, ...)`
- [ ] Line 151: Step 4/4 → `parser_logger.step(4, 4, ...)`

#### 5. 완료 로그 교체 (line 181-184)
- [ ] `parser_logger.success()` 사용
- [ ] 메트릭: tables, images, formulas 등

#### 6. Error 처리 (line 197-222)
- [ ] Line 201-208: Model weights 에러 → `parser_logger.error()` 사용
- [ ] Line 217-218, 221: 일반 에러 → `parser_logger.error()` 사용

### Verification
- [ ] MinerU 파싱 테스트
- [ ] 4단계 프로세스 로그 확인
- [ ] 에러 메시지 형식 확인

---

## 📋 Phase 6: Integration Testing (15분)

### Test Cases

#### Test 1: Docling Parser
- [ ] PDF 파일 파싱 실행
- [ ] 로그 출력 확인
  - [ ] 🎯 시작 로그 있음
  - [ ] 📋 설정 로그 있음
  - [ ] ⚙️ 단계 로그 있음
  - [ ] ✅ 완료 로그 있음
- [ ] 들여쓰기 일관성 확인
- [ ] 기존 기능 정상 동작 확인

#### Test 2: Dolphin Remote Parser
- [ ] GPU 서버 연결 가능 시 테스트
- [ ] 로그 출력 확인
  - [ ] 페이지별 로그 형식 확인
  - [ ] Stage 1/2 로그 계층 확인
  - [ ] 🌐 원격 API 호출 로그 확인
- [ ] 진행률 표시 확인

#### Test 3: Remote OCR Parser
- [ ] OCR 서버 연결 가능 시 테스트
- [ ] 페이지별 처리 로그 확인
- [ ] 로그 일관성 확인

#### Test 4: MinerU Parser
- [ ] MinerU 설치되어 있으면 테스트
- [ ] 4단계 로그 확인
- [ ] 메트릭 출력 확인

### Cross-Parser Verification
- [ ] 모든 파서의 로그 형식 일관성 확인
- [ ] 이모지 사용 일관성 확인
- [ ] 들여쓰기 일관성 확인
- [ ] 로그 레벨 적절성 확인

### Performance Check
- [ ] 로깅 오버헤드 측정 (무시할 수준이어야 함)
- [ ] 파싱 속도 영향 없음 확인

---

## 📋 Phase 7: Documentation Update (10분)

**파일**: `CLAUDE.md`

### Updates Required

#### 1. New Section: "Logging Standards"
- [ ] 로깅 표준 섹션 추가 (Architecture 섹션 이후)
- [ ] 내용:
  - [ ] 로그 계층 구조 설명
  - [ ] 표준 이모지 목록
  - [ ] 들여쓰기 규칙
  - [ ] 로그 레벨 가이드라인
  - [ ] `ParserLogger` 사용 예시

#### 2. Update: "Backend Architecture" Section
- [ ] `backend/app/utils/logging_utils.py` 추가
- [ ] Key Services 섹션에 logging utility 언급

#### 3. Update: "Common Development Tasks" Section
- [ ] "Adding a new parsing strategy" 항목 업데이트
  - [ ] ParserLogger 사용 가이드 추가
  - [ ] 표준 로그 형식 준수 언급

### Example Documentation

````markdown
## Logging Standards

All parsing strategies use a standardized logging format via the `ParserLogger` class for consistency and maintainability.

### Log Structure

```
🎯 [Parser Name] Parsing: filename.pdf
    📋 Config Key: value
    ⚙️ Step 1/4: Description...
        ├─ Sub-action: details
        └─ Result: outcome
    ✅ Complete: summary
```

### Standard Emojis

| Emoji | Purpose | Example |
|-------|---------|---------|
| 🎯 | Parser Start | `🎯 [Docling] Parsing: doc.pdf` |
| 📋 | Configuration | `📋 OCR Engine: easyocr` |
| ⚙️ | Processing Step | `⚙️ Step 1/4: Creating dataset...` |
| 📖 | Page Processing | `📖 Processing Page 1/10` |
| 🌐 | Remote API Call | `🌐 Calling remote GPU server...` |
| ✅ | Success | `✅ Complete: 10 pages processed` |
| ⚠️ | Warning/Fallback | `⚠️ Fallback to local OCR` |
| ❌ | Error | `❌ Failed: Connection timeout` |

### Indentation Rules

- Level 0: Parser Start (no indent)
- Level 1: Configuration & Main Steps (4 spaces)
- Level 2: Sub-steps (8 spaces)
- Level 3: Details (12 spaces)

### Usage Example

```python
from app.utils.logging_utils import ParserLogger

parser_logger = ParserLogger("MyParser", logger)
parser_logger.start(filename, config_key="value")
parser_logger.step(1, 3, "Processing document...")
parser_logger.detail("Extracted 100 elements")
parser_logger.success("Parsing complete", pages=10, tables=5)
```

### Log Levels

- **DEBUG**: Detailed internal operations (development only)
- **INFO**: Normal processing steps and progress
- **WARNING**: Fallback methods, partial failures
- **ERROR**: Parsing failures, exceptions
````

### Verification
- [ ] CLAUDE.md 문법 확인
- [ ] 예시 코드 정확성 확인
- [ ] 링크 및 참조 확인

---

## ✅ Final Checklist

- [ ] 모든 Phase 완료
- [ ] 모든 파서 테스트 통과
- [ ] 로그 일관성 확인
- [ ] 문서화 완료
- [ ] Git commit 준비
  - [ ] 변경 사항 검토
  - [ ] 커밋 메시지 작성
  - [ ] (선택) PR 생성

---

## 📊 Progress Tracking

**Total Tasks**: 150개 체크리스트 항목

**Completed**: ___ / 150

**Progress**: ____%

**Time Spent**: ___ / 140분

---

## 🔄 Rollback Plan (문제 발생 시)

만약 표준화 적용 중 문제가 발생하면:

1. **즉시 중단**: 현재 Phase에서 작업 중단
2. **Git Revert**: `git checkout -- <file>` 로 파일 복구
3. **문제 분석**: 로그 출력 확인 및 에러 메시지 검토
4. **수정 후 재시도**: logging_utils.py 수정 후 다시 적용

---

## 📝 Notes

- 각 Phase는 독립적으로 테스트 가능
- Phase 순서는 변경 가능 (의존성 없음)
- 리소스 체크 로그는 선택적 (기존 동작 유지 가능)
- 프로덕션 배포 전 충분한 테스트 필요
