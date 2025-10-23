# Dolphin Document Parser Integration Plan

**목표**: MinerU의 OCR 정확도 문제 해결을 위한 4번째 파싱 옵션 추가

## 개요

- **모델**: ByteDance Dolphin 1.5 (0.3B, 경량)
- **특징**: 멀티모달, 고정밀도 (OmniDocBench 83.21), ACL 2025
- **장점**: 영문 약어 정확, 괄호 보존, 날짜 형식 유지
- **예상 시간**: 11-16시간

## Phase 1: 환경 설정 (1-2시간)

### 체크리스트
- [ ] Dolphin 레포 클론: `git clone https://github.com/ByteDance/Dolphin.git dolphin_lib`
- [ ] 의존성 설치: `pip install transformers>=4.40.0 torch>=2.0.0 pdf2image>=1.16.0`
- [ ] 모델 다운로드 (~2GB): `huggingface-cli download ByteDance/Dolphin-1.5 --local-dir ./dolphin_models/Dolphin-1.5`
- [ ] 디렉토리 구조 확인: `dolphin_lib/`, `dolphin_models/`, `app/services/`

## Phase 2: Dolphin Parser 구현 (3-4시간)

### 파일: `backend/app/services/dolphin_parser.py`

**핵심 함수**:
```python
async def parse_with_dolphin(
    file_path: Path,
    output_dir: Optional[Path] = None,
    output_format: str = "markdown",
    parsing_level: str = "page",
    max_batch_size: int = 8,
    device: str = "cuda"
) -> Tuple[str, Dict[str, Any]]:
    """Dolphin으로 문서 파싱"""
    # 1. PDF → 이미지 변환
    images = convert_from_path(file_path, dpi=150) if file_path.suffix == '.pdf' else [Image.open(file_path)]

    # 2. 모델 로드 (GPU/CPU 자동 감지)
    model = AutoModel.from_pretrained(
        "./dolphin_models/Dolphin-1.5",
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained("./dolphin_models/Dolphin-1.5", trust_remote_code=True)

    # 3. 배치 파싱 (torch.no_grad() 사용)
    results = []
    for i in range(0, len(images), max_batch_size):
        with torch.no_grad():
            batch_results = model.parse_page(images[i:i+max_batch_size], tokenizer, output_format="markdown")
        results.extend(batch_results)

    # 4. 메타데이터 추출
    content = "\n\n".join(results)
    metadata = extract_metadata(content, len(images))
    return content, metadata
```

### 체크리스트
- [ ] PDF → 이미지 변환 (`pdf2image`)
- [ ] 모델 로드 (GPU/CPU 자동 폴백)
- [ ] 배치 파싱 구현 (`torch.no_grad()`, `torch.cuda.empty_cache()`)
- [ ] 메타데이터 추출 (표, 수식, 이미지 개수)
- [ ] `check_dolphin_installation()` 함수 작성
- [ ] 에러 핸들링 (`ImportError`, `torch.cuda.OutOfMemoryError`)

## Phase 3: API 통합 (2-3시간)

### 파일: `backend/app/models.py`
```python
class ParseOptions(BaseModel):
    use_dolphin: bool = False
    dolphin_parsing_level: Literal["page", "element", "layout"] = "page"
    dolphin_max_batch_size: int = 8
    dolphin_device: Literal["cuda", "cpu"] = "cuda"
```

### 파일: `backend/app/main.py`
```python
@app.post("/parse", response_model=ParseResponse)
async def parse_document(request: ParseRequest, background_tasks: BackgroundTasks):
    if options.use_dolphin:
        try:
            content, metadata = await parse_with_dolphin(
                file_path, output_dir,
                parsing_level=options.dolphin_parsing_level,
                max_batch_size=options.dolphin_max_batch_size,
                device=options.dolphin_device
            )
        except torch.cuda.OutOfMemoryError:
            raise HTTPException(507, "GPU out of memory. Try CPU or reduce batch_size.")
    # ... 기존 로직
```

### 체크리스트
- [ ] `ParseOptions`에 Dolphin 옵션 4개 추가
- [ ] `main.py`에 `use_dolphin` 분기 추가
- [ ] `GET /` 엔드포인트에 Dolphin 상태 추가
- [ ] HTTPException 에러 핸들링 (404, 500, 507)
- [ ] BackgroundTasks로 정리 작업 예약

## Phase 4: 프론트엔드 UI 통합 (2-3시간)

### 파일: `lib/types.ts`
```typescript
use_dolphin?: boolean;
dolphin_parsing_level?: 'page' | 'element' | 'layout';
dolphin_max_batch_size?: number;
dolphin_device?: 'cuda' | 'cpu';
```

### 파일: `components/upload/ParsingOptions.tsx`
```tsx
type ParsingStrategy = 'dolphin' | 'mineru' | 'camelot' | 'docling';

<SelectItem value="dolphin">
  <Zap className="h-4 w-4" />
  <span>Dolphin (AI-Powered)</span>
  <Badge variant="secondary">New</Badge>
</SelectItem>

{currentStrategy === 'dolphin' && (
  <>
    <Select value={options.dolphin_parsing_level} ...>
      <SelectItem value="page">Page-level (Recommended)</SelectItem>
      <SelectItem value="element">Element-level (Detailed)</SelectItem>
    </Select>
    <Switch checked={options.dolphin_device === 'cuda'} ...>GPU Acceleration</Switch>
  </>
)}
```

### 체크리스트
- [ ] `types.ts`에 Dolphin 타입 4개 추가
- [ ] `ParsingOptions.tsx`에 Dolphin 전략 추가
- [ ] Parsing Level 셀렉트 (page/element/layout)
- [ ] Batch Size 셀렉트 (4/8/16)
- [ ] GPU/CPU 스위치
- [ ] `MetadataPanel.tsx`에 Dolphin 메타데이터 표시

## Phase 5: 테스트 및 검증 (2-3시간)

### 테스트 스크립트: `backend/test_dolphin.ps1`
```powershell
# 1. 설치 확인
python -c "from app.services.dolphin_parser import check_dolphin_installation; import json; print(json.dumps(check_dolphin_installation(), indent=2))"

# 2. 단일 PDF 테스트
python -c "import asyncio; from pathlib import Path; from app.services.dolphin_parser import parse_with_dolphin; asyncio.run(parse_with_dolphin(Path('../docu/sample.pdf')))"

# 3. 다중 페이지 테스트 (정확도 비교)
python -c "import asyncio; from pathlib import Path; from app.services.dolphin_parser import parse_with_dolphin; asyncio.run(parse_with_dolphin(Path('../docu/3-1. (출제기준) 정보통신기술사 출제기준.pdf')))"
```

### 정확도 비교 목표
| 항목 | MinerU | Dolphin 목표 |
|------|--------|--------------|
| 영문 약어 (LAN, AI) | ❌ 0% | ✅ 90%+ |
| 괄호 내용 | ❌ 10% | ✅ 95%+ |
| 날짜 형식 | ❌ 30% | ✅ 95%+ |
| 표 구조 | ⚠️ 60% | ✅ 85%+ |
| 처리 속도 | ~30초 | ~20초 |

### 체크리스트
- [ ] `test_dolphin.ps1` 작성
- [ ] 설치 확인 테스트
- [ ] 단일/다중 페이지 테스트
- [ ] MinerU vs Dolphin 정확도 비교
- [ ] GPU OOM 에러 테스트 (CPU 폴백 확인)
- [ ] 프론트엔드 E2E 테스트

## Phase 6: 문서화 (1시간, 선택적)

### 체크리스트
- [ ] `CLAUDE.md`에 Dolphin 섹션 추가
- [ ] API 버전 2.2.0 → 2.3.0 업데이트
- [ ] 주석 및 docstring 추가

## 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| 모델 다운로드 실패 | 수동 다운로드 가이드 제공 |
| GPU 메모리 부족 | CPU 폴백 + batch_size 줄이기 (8→4→2) |
| 한국어 정확도 부족 | 테스트 후 MinerU 앙상블 전략 고려 |

## 성공 기준

### 필수
- [ ] Dolphin 파서가 PDF → Markdown 변환 성공
- [ ] API 엔드포인트 `use_dolphin=True` 동작
- [ ] 프론트엔드에서 Dolphin 선택 가능
- [ ] MinerU보다 높은 정확도 (한국어 기술 문서)

### 우수
- [ ] 처리 속도 30초 이내 (8페이지)
- [ ] GPU/CPU 자동 폴백
- [ ] 배치 처리 최적화

## Context7 MCP 활용 팁

**구현 시 참고**:
- Transformers: `/huggingface/transformers` → `trust_remote_code`, `device_map`
- PyTorch: `/pytorch/pytorch` → `torch.no_grad()`, CUDA 관리
- FastAPI: `/fastapi/fastapi` → `BackgroundTasks`, async 패턴

---

**작성**: 2025-10-23 | **버전**: 1.1 (Context7 MCP 반영)
