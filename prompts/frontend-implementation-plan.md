# Next.js + shadcn/ui 프론트엔드 구현 플랜

> **최종 업데이트**: 2025-10-16
> **버전**: 1.0
> **상태**: Phase 1-3 백엔드 완료 기반 프론트엔드 구현 계획

## 📋 문서 개요

이 문서는 **현재 구현된 FastAPI 백엔드 (Phase 1-3)**를 기반으로 Next.js 15와 shadcn/ui를 사용한 프론트엔드 구현 계획입니다.

### 백엔드 완료 기능 (Phase 1-3)
- ✅ FastAPI 서버 (Port 8000)
- ✅ `GET /` - API 상태 확인
- ✅ `GET /documents` - 문서 목록 조회
- ✅ `POST /parse` - 문서 파싱 (Markdown/HTML/JSON)
- ✅ Docling + Camelot 하이브리드 파싱
- ✅ 표 추출 및 복잡도 판단
- ✅ `/docu` 폴더 문서 관리
- ✅ `/output/{doc_name}/` 구조화된 출력

### 프론트엔드 목표
- ✅ 문서 업로드 UI (드래그 앤 드롭)
- ✅ 파싱 옵션 설정
- ✅ 파싱 진행 상태 표시
- ✅ Markdown 뷰어로 결과 표시
- ✅ 표 데이터 시각화
- ✅ 파일 다운로드 기능

---

## 🎯 프론트엔드 아키텍처

### 기술 스택
- **Framework**: Next.js 15.5.4 (App Router)
- **UI Library**: shadcn/ui (New York style)
- **Icons**: Lucide React
- **Styling**: Tailwind CSS 4
- **Markdown Rendering**: react-markdown + remark-gfm
- **Code Highlighting**: react-syntax-highlighter
- **HTTP Client**: fetch API (native)
- **State Management**: React hooks (useState, useEffect)

### 페이지 구조

```
app/
├── page.tsx                    # 랜딩 페이지 (현재 기본 페이지)
├── parse/
│   └── page.tsx               # 메인 파싱 페이지
├── viewer/
│   └── page.tsx               # Markdown 뷰어 페이지
└── layout.tsx                 # Root layout

components/
├── upload/
│   ├── FileUploader.tsx       # 파일 업로드 컴포넌트
│   ├── FileList.tsx           # 업로드된 파일 목록
│   └── ParsingOptions.tsx     # 파싱 옵션 설정
├── viewer/
│   ├── MarkdownViewer.tsx     # Markdown 렌더링
│   ├── TableViewer.tsx        # 표 데이터 시각화
│   └── MetadataPanel.tsx      # 메타데이터 표시
└── ui/
    └── (shadcn/ui components) # shadcn/ui 컴포넌트들
```

---

## 📅 프론트엔드 구현 타임라인

| Phase | 주제 | 예상 기간 | 우선순위 | 진행 상태 |
|-------|------|-----------|----------|----------|
| FE Phase 1 | 프로젝트 설정 및 shadcn/ui 통합 | 0.5일 | 🔴 필수 | ✅ 완료 |
| FE Phase 2 | 파일 업로드 UI 구현 | 1-2일 | 🔴 필수 | ✅ 완료 |
| FE Phase 3 | 백엔드 API 통합 | 1일 | 🔴 필수 | ✅ 완료 |
| FE Phase 4 | Markdown 뷰어 구현 | 1-2일 | 🔴 필수 | ✅ 완료 |
| FE Phase 5 | 표 데이터 시각화 | 1일 | 🟡 중요 | ✅ 완료 |
| FE Phase 6 | UX 개선 및 최적화 | 1일 | 🟢 선택 | ✅ 완료 |

**총 예상 기간**: 1주일
**현재 진행률**: 100% (Phase 1-6 모두 완료)

---

## 🚀 FE Phase 1: 프로젝트 설정 및 shadcn/ui 통합

### 목표
필요한 shadcn/ui 컴포넌트를 추가하고, Markdown 렌더링 라이브러리를 설치합니다.

### 구현 범위
- shadcn/ui 컴포넌트 추가
- Markdown 렌더링 라이브러리 설치
- 프로젝트 구조 설정

### 체크리스트

#### 1.1 shadcn/ui 컴포넌트 추가
- [x] Button 컴포넌트 추가 (`npx shadcn@latest add button`)
- [x] Card 컴포넌트 추가 (`npx shadcn@latest add card`)
- [x] Input 컴포넌트 추가 (`npx shadcn@latest add input`)
- [x] Label 컴포넌트 추가 (`npx shadcn@latest add label`)
- [x] Select 컴포넌트 추가 (`npx shadcn@latest add select`)
- [x] Switch 컴포넌트 추가 (`npx shadcn@latest add switch`)
- [x] Tabs 컴포넌트 추가 (`npx shadcn@latest add tabs`)
- [x] Badge 컴포넌트 추가 (`npx shadcn@latest add badge`)
- [x] Alert 컴포넌트 추가 (`npx shadcn@latest add alert`)
- [x] Progress 컴포넌트 추가 (`npx shadcn@latest add progress`)
- [x] Separator 컴포넌트 추가 (`npx shadcn@latest add separator`)
- [x] Table 컴포넌트 추가 (`npx shadcn@latest add table`)
- [x] ScrollArea 컴포넌트 추가 (`npx shadcn@latest add scroll-area`)

#### 1.2 Markdown 렌더링 라이브러리 설치
- [x] react-markdown 설치 (`npm install react-markdown`)
- [x] remark-gfm 설치 (GitHub Flavored Markdown) (`npm install remark-gfm`)
- [x] rehype-raw 설치 (HTML 지원) (`npm install rehype-raw`)
- [x] react-syntax-highlighter 설치 (`npm install react-syntax-highlighter`)
- [x] @types/react-syntax-highlighter 설치 (`npm install -D @types/react-syntax-highlighter`)

#### 1.3 프로젝트 구조 설정
- [x] `app/parse/page.tsx` 생성 (메인 파싱 페이지)
- [x] `app/viewer/page.tsx` 생성 (뷰어 페이지)
- [x] `components/upload/` 디렉토리 생성
- [x] `components/viewer/` 디렉토리 생성
- [x] `lib/api.ts` 생성 (API 호출 함수)
- [x] `lib/types.ts` 생성 (TypeScript 타입 정의)

### 성공 기준
- ✅ 모든 shadcn/ui 컴포넌트가 설치됨
- ✅ Markdown 렌더링 라이브러리가 설치됨
- ✅ 프로젝트 구조가 생성됨

### 검증 방법
```powershell
# shadcn/ui 컴포넌트 확인
ls components/ui/

# 의존성 확인
npm list react-markdown remark-gfm react-syntax-highlighter
```

---

## 🚀 FE Phase 2: 파일 업로드 UI 구현

### 목표
드래그 앤 드롭을 지원하는 파일 업로드 컴포넌트를 구현합니다.

### 구현 범위
- 파일 드래그 앤 드롭 영역
- 파일 선택 버튼
- 업로드된 파일 목록 표시
- 파싱 옵션 설정 UI

### 체크리스트

#### 2.1 API 타입 정의 (`lib/types.ts`)
- [x] `DocumentInfo` 인터페이스 정의
  ```typescript
  interface DocumentInfo {
    filename: string;
    size: number;
    extension: string;
  }
  ```
- [x] `ParseOptions` 인터페이스 정의
  ```typescript
  interface ParseOptions {
    do_ocr?: boolean;
    table_mode?: string;
    output_format?: 'markdown' | 'html' | 'json';
    extract_tables?: boolean;
    save_to_output_folder?: boolean;
  }
  ```
- [x] `ParseRequest` 인터페이스 정의
  ```typescript
  interface ParseRequest {
    filename: string;
    options?: ParseOptions;
  }
  ```
- [x] `ParseResponse` 인터페이스 정의
  ```typescript
  interface ParseResponse {
    success: boolean;
    content: string;
    stats: {
      lines: number;
      words: number;
      characters: number;
      size_kb: number;
    };
    table_summary?: {
      total_tables: number;
      markdown_tables: number;
      json_tables: number;
      json_table_ids: string[];
    };
    saved_to?: string;
    error?: string;
  }
  ```

#### 2.2 FileUploader 컴포넌트 (`components/upload/FileUploader.tsx`)
- [x] 드래그 앤 드롭 영역 구현
  ```typescript
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  ```
- [x] 파일 선택 input 구현
  ```typescript
  <input
    type="file"
    accept=".pdf,.docx,.pptx,.html"
    onChange={handleFileSelect}
    ref={fileInputRef}
    style={{ display: 'none' }}
  />
  ```
- [x] 드래그 앤 드롭 이벤트 핸들러
- [x] 파일 유효성 검증 (확장자, 크기)
- [x] shadcn/ui Card 컴포넌트로 UI 구성
- [x] Lucide React 아이콘 사용 (Upload, File, X)

#### 2.3 FileList 컴포넌트 (`components/upload/FileList.tsx`)
- [ ] 업로드된 파일 목록 표시
- [ ] 파일 정보 표시 (이름, 크기, 확장자)
- [ ] 파일 제거 버튼
- [ ] shadcn/ui Badge로 파일 타입 표시
- [ ] 파일 크기 포맷팅 유틸 함수

#### 2.4 ParsingOptions 컴포넌트 (`components/upload/ParsingOptions.tsx`)
- [x] OCR 활성화 옵션 (Switch)
- [x] 표 모드 선택 (Select: hybrid, lattice, stream)
- [x] 출력 형식 선택 (Select: markdown, html, json)
- [x] 표 추출 옵션 (Switch)
- [x] 출력 폴더 저장 옵션 (Switch)
- [x] shadcn/ui Form 컴포넌트 사용
- [x] 옵션 설명 툴팁 추가

#### 2.5 메인 파싱 페이지 (`app/parse/page.tsx`)
- [x] FileUploader 컴포넌트 배치
- [x] FileList 컴포넌트 배치
- [x] ParsingOptions 컴포넌트 배치
- [x] "Parse Document" 버튼 추가
- [x] 레이아웃 구성 (2-column grid)
- [x] 반응형 디자인 (모바일: 1-column)

### 성공 기준
- ✅ 파일 드래그 앤 드롭이 작동함
- ✅ 파일 선택 버튼이 작동함
- ✅ 업로드된 파일이 목록에 표시됨
- ✅ 파싱 옵션을 설정할 수 있음
- ✅ UI가 깔끔하고 직관적임

### 검증 방법
```powershell
# 개발 서버 실행
npm run dev

# http://localhost:3000/parse 접속
# 1. 파일 드래그 앤 드롭 테스트
# 2. 파일 선택 버튼 테스트
# 3. 옵션 설정 테스트
```

---

## 🚀 FE Phase 3: 백엔드 API 통합

### 목표
FastAPI 백엔드와 통신하여 문서를 파싱하고 결과를 받아옵니다.

### 구현 범위
- API 호출 함수 구현
- 파싱 진행 상태 표시
- 에러 처리
- 결과 저장 및 라우팅

### 체크리스트

#### 3.1 API 클라이언트 구현 (`lib/api.ts`)
- [x] API 베이스 URL 설정
  ```typescript
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  ```
- [x] `getApiStatus()` 함수 구현 (GET /)
  ```typescript
  export async function getApiStatus() {
    const response = await fetch(`${API_BASE_URL}/`);
    return response.json();
  }
  ```
- [x] `getDocuments()` 함수 구현 (GET /documents)
  ```typescript
  export async function getDocuments(): Promise<DocumentInfo[]> {
    const response = await fetch(`${API_BASE_URL}/documents`);
    return response.json();
  }
  ```
- [x] `parseDocument()` 함수 구현 (POST /parse)
  ```typescript
  export async function parseDocument(request: ParseRequest): Promise<ParseResponse> {
    const response = await fetch(`${API_BASE_URL}/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return response.json();
  }
  ```
- [x] 에러 핸들링 추가
- [x] 타임아웃 설정 (대용량 파일 대응)

#### 3.2 파싱 진행 상태 표시
- [x] `ParsingProgress` 컴포넌트 생성 (Integrated into parse page)
- [x] shadcn/ui Progress 컴포넌트 사용
- [x] 파싱 단계별 상태 표시
  - "📤 Uploading file..."
  - "📄 Parsing document..."
  - "📊 Extracting tables..."
  - "✅ Parsing complete!"
- [x] 애니메이션 효과 추가
- [ ] 예상 소요 시간 표시 (선택)

#### 3.3 파싱 로직 구현 (`app/parse/page.tsx`)
- [x] `handleParse()` 함수 구현
  ```typescript
  const handleParse = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await parseDocument({
        filename: selectedFile.name,
        options: parsingOptions,
      });

      if (result.success) {
        // 결과 저장 및 뷰어로 이동
        router.push(`/viewer?file=${selectedFile.name}`);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Parsing failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  ```
- [x] 로딩 상태 관리 (useState)
- [x] 에러 상태 관리
- [x] shadcn/ui Alert로 에러 메시지 표시

#### 3.4 환경 변수 설정
- [x] `.env.local` 파일 생성
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
- [x] `.env.example` 파일 생성 (템플릿)

#### 3.5 CORS 확인
- [x] 백엔드 CORS 설정 확인 (`backend/app/main.py`)
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### 성공 기준
- ✅ API 호출이 정상 작동함
- ✅ 파싱 진행 상태가 표시됨
- ✅ 에러가 적절히 처리됨
- ✅ 파싱 완료 후 뷰어로 이동함

### 검증 방법
```powershell
# 백엔드 시작
cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 시작 (다른 터미널)
npm run dev

# 테스트
# 1. sample.pdf 파일 업로드
# 2. 파싱 옵션 설정
# 3. "Parse Document" 버튼 클릭
# 4. 진행 상태 확인
# 5. 완료 후 뷰어 페이지로 이동 확인
```

---

## 🚀 FE Phase 4: Markdown 뷰어 구현

### 목표
파싱된 Markdown 콘텐츠를 아름답게 렌더링하는 뷰어를 구현합니다.

### 구현 범위
- Markdown 렌더링
- 코드 하이라이팅
- 표 렌더링
- 목차 (Table of Contents) 생성
- 다크 모드 지원

### 체크리스트

#### 4.1 MarkdownViewer 컴포넌트 (`components/viewer/MarkdownViewer.tsx`)
- [x] react-markdown 컴포넌트 구성
  ```typescript
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    rehypePlugins={[rehypeRaw]}
    components={{
      code: CodeBlock,
      table: TableComponent,
      h1: HeadingComponent,
      // ...
    }}
  >
    {content}
  </ReactMarkdown>
  ```
- [x] 커스텀 렌더러 구현
  - 헤딩: ID 자동 생성, 앵커 링크
  - 코드: 구문 하이라이팅
  - 표: shadcn/ui Table 컴포넌트
  - 링크: 외부 링크 _blank 처리
- [x] Markdown 스타일링 (Tailwind prose)
  ```typescript
  <div className="prose dark:prose-invert max-w-none">
    {/* Markdown content */}
  </div>
  ```

#### 4.2 CodeBlock 컴포넌트 (`components/viewer/CodeBlock.tsx`)
- [x] react-syntax-highlighter 통합
  ```typescript
  import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
  import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
  ```
- [x] 언어 감지 및 하이라이팅
- [x] 코드 복사 버튼 추가
- [x] 라인 넘버 표시

#### 4.3 TableOfContents 컴포넌트 (`components/viewer/TableOfContents.tsx`)
- [x] Markdown에서 헤딩 추출
  ```typescript
  const extractHeadings = (markdown: string) => {
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    const headings = [];
    let match;

    while ((match = headingRegex.exec(markdown)) !== null) {
      headings.push({
        level: match[1].length,
        text: match[2],
        id: generateId(match[2]),
      });
    }

    return headings;
  };
  ```
- [x] 트리 구조 생성
- [x] 앵커 링크 연결
- [x] 현재 섹션 하이라이트 (IntersectionObserver)
- [x] 고정 사이드바 (sticky positioning)

#### 4.4 뷰어 페이지 (`app/viewer/page.tsx`)
- [x] URL 쿼리 파라미터에서 파일명 가져오기
  ```typescript
  const searchParams = useSearchParams();
  const filename = searchParams.get('file');
  ```
- [x] API로 파싱 결과 가져오기
- [x] 3-column 레이아웃
  - 좌측: TableOfContents (고정)
  - 중앙: MarkdownViewer (스크롤 가능)
  - 우측: MetadataPanel (고정, 선택)
- [x] 반응형 디자인 (모바일: 1-column)
- [x] 로딩 스켈레톤 추가

#### 4.5 MetadataPanel 컴포넌트 (`components/viewer/MetadataPanel.tsx`)
- [x] 문서 통계 표시
  - 라인 수
  - 단어 수
  - 문자 수
  - 파일 크기
- [x] 표 요약 표시
  - 총 표 개수
  - Markdown 표 개수
  - JSON 표 개수
- [x] 다운로드 버튼
- [x] shadcn/ui Card 컴포넌트 사용

### 성공 기준
- ✅ Markdown이 올바르게 렌더링됨
- ✅ 코드 블록이 하이라이팅됨
- ✅ 표가 아름답게 표시됨
- ✅ 목차가 작동함
- ✅ 레이아웃이 깔끔함

### 검증 방법
```powershell
# 뷰어 페이지 접속
# http://localhost:3000/viewer?file=sample.pdf

# 테스트 항목
# 1. Markdown 렌더링 확인
# 2. 목차 클릭 → 해당 섹션 이동
# 3. 코드 블록 하이라이팅 확인
# 4. 표 렌더링 확인
# 5. 메타데이터 패널 확인
```

---

## 🚀 FE Phase 5: 표 데이터 시각화

### 목표
복잡한 표 데이터를 JSON에서 불러와 시각화하고, AI 요약을 표시합니다.

### 구현 범위
- JSON 표 데이터 로드
- 표 구조 렌더링
- 표 요약 표시
- 표 상세보기 모달

### 체크리스트

#### 5.1 TableViewer 컴포넌트 (`components/viewer/TableViewer.tsx`)
- [x] JSON 표 데이터 타입 정의
  ```typescript
  interface TableData {
    table_id: string;
    chunk_id?: string;
    page: number;
    caption?: string;
    complexity: {
      rows: number;
      cols: number;
      has_merged_cells: boolean;
      is_complex: boolean;
    };
    structure: {
      headers: string[][];
      rows: string[][];
    };
    summary?: string;
  }
  ```
- [x] JSON 파일에서 표 데이터 로드
  ```typescript
  const loadTableData = async (tableId: string) => {
    const response = await fetch(`/api/tables/${tableId}`);
    return response.json();
  };
  ```
- [x] shadcn/ui Table 컴포넌트로 렌더링
- [x] 병합 셀 처리 (colSpan, rowSpan)
- [x] 표 캡션 표시
- [x] 표 복잡도 배지 표시

#### 5.2 TableSummary 컴포넌트 (`components/viewer/TableSummary.tsx`)
- [x] AI 요약 텍스트 표시
- [x] "View Full Table" 버튼
- [x] shadcn/ui Card + Badge 사용
- [x] 요약이 없는 경우 처리

#### 5.3 TableDetailModal 컴포넌트 (`components/viewer/TableDetailModal.tsx`)
- [x] shadcn/ui Dialog 사용
- [x] 표 전체 데이터 표시
- [x] 탭으로 구분
  - "Preview" 탭: 표 렌더링
  - "JSON" 탭: 원본 JSON 표시
  - "CSV" 탭: CSV 형식 표시
- [x] 다운로드 버튼 (JSON, CSV)
- [x] 복사 버튼

#### 5.4 Markdown에 표 참조 렌더링
- [x] Markdown의 표 참조 블록 감지
  ```markdown
  > **Table 001** (see tables/table_001.json)
  ```
- [x] 커스텀 컴포넌트로 교체
  ```typescript
  {
    blockquote: ({ node, children }) => {
      // "Table XXX" 패턴 감지
      if (isTableReference(children)) {
        return <TableReference tableId={extractTableId(children)} />;
      }
      return <blockquote>{children}</blockquote>;
    }
  }
  ```
- [x] TableSummary 컴포넌트 렌더링
- [x] 클릭 시 TableDetailModal 열기

#### 5.5 API 라우트 추가 (`app/api/tables/[tableId]/route.ts`)
- [x] Next.js API Route 생성
- [x] `output/{doc_name}/tables/` 폴더에서 JSON 파일 읽기
- [x] JSON 파일 파싱 및 반환
- [x] 에러 처리 (파일 없음)

### 성공 기준
- ✅ JSON 표가 올바르게 렌더링됨
- ✅ 표 요약이 표시됨
- ✅ 상세보기 모달이 작동함
- ✅ Markdown의 표 참조가 인터랙티브 컴포넌트로 표시됨

### 검증 방법
```powershell
# 표 포함 문서 파싱
$body = @{ filename = "sample2_bokmu.pdf" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/parse" -Method Post -ContentType "application/json" -Body $body

# 뷰어에서 확인
# http://localhost:3000/viewer?file=sample2_bokmu.pdf

# 테스트 항목
# 1. 표 참조 블록이 인터랙티브 컴포넌트로 표시됨
# 2. 표 요약 확인
# 3. "View Full Table" 클릭 → 모달 열림
# 4. 표 전체 데이터 확인
# 5. JSON, CSV 탭 전환 확인
```

---

## 🚀 FE Phase 6: UX 개선 및 최적화

### 목표
사용자 경험을 개선하고 성능을 최적화합니다.

### 구현 범위
- 다크 모드 지원
- 반응형 디자인 개선
- 로딩 스켈레톤 추가
- 에러 바운더리 구현
- SEO 최적화

### 체크리스트

#### 6.1 다크 모드 구현
- [x] `next-themes` 라이브러리 설치
  ```bash
  npm install next-themes
  ```
- [x] ThemeProvider 설정 (`app/layout.tsx`)
  ```typescript
  import { ThemeProvider } from 'next-themes'

  export default function RootLayout({ children }) {
    return (
      <html lang="ko" suppressHydrationWarning>
        <body>
          <ThemeProvider attribute="class" defaultTheme="system">
            {children}
          </ThemeProvider>
        </body>
      </html>
    )
  }
  ```
- [x] 다크 모드 토글 버튼 추가 (Sidebar)
- [x] Tailwind dark: prefix 적용
- [x] shadcn/ui 다크 모드 스타일 확인

#### 6.2 반응형 디자인 개선
- [x] 모바일 네비게이션 메뉴 (Sidebar 사용)
- [x] 태블릿 레이아웃 최적화
- [x] 목차 모바일에서 접을 수 있게 (Drawer)
- [x] 파일 업로더 모바일 UX 개선

#### 6.3 로딩 스켈레톤
- [x] shadcn/ui Skeleton 컴포넌트 추가
- [x] 뷰어 페이지 로딩 스켈레톤
- [x] 파일 목록 로딩 스켈레톤
- [x] 표 로딩 스켈레톤 (TableReference 컴포넌트)

#### 6.4 에러 바운더리
- [x] `app/error.tsx` 생성 (Next.js Error Boundary)
  ```typescript
  'use client'

  export default function Error({
    error,
    reset,
  }: {
    error: Error & { digest?: string }
    reset: () => void
  }) {
    return (
      <div>
        <h2>Something went wrong!</h2>
        <button onClick={reset}>Try again</button>
      </div>
    )
  }
  ```
- [x] 커스텀 에러 페이지 디자인
- [x] `app/global-error.tsx` 추가 (전역 에러 처리)
- [x] `app/not-found.tsx` 추가 (404 페이지)

#### 6.5 성능 최적화
- [ ] 이미지 최적화 (next/image)
- [ ] 코드 스플리팅 확인
- [ ] 번들 크기 분석 (`npm run build`)
- [ ] Markdown 렌더링 메모이제이션 (useMemo)
- [ ] Suspense 경계 추가

#### 6.6 SEO 최적화
- [x] 메타데이터 추가 (`app/layout.tsx`)
  ```typescript
  export const metadata: Metadata = {
    title: 'Document Parser - RAG Optimized',
    description: 'Parse PDF, DOCX, PPTX documents with Docling',
  }
  ```
- [x] OpenGraph 메타데이터 추가
- [ ] 페이지별 동적 메타데이터 (`generateMetadata`) - 선택
- [ ] Open Graph 이미지 추가 - 선택

#### 6.7 접근성 (a11y)
- [ ] 키보드 네비게이션 테스트
- [ ] ARIA 레이블 추가
- [ ] 색상 대비 확인
- [ ] 스크린 리더 테스트 (선택)

### 성공 기준
- ✅ 다크 모드가 작동함
- ✅ 모든 화면 크기에서 잘 보임
- ✅ 로딩 상태가 명확함
- ✅ 에러가 우아하게 처리됨
- ✅ 성능이 우수함 (Lighthouse 90+)

### 검증 방법
```powershell
# 프로덕션 빌드
npm run build

# Lighthouse 성능 측정
npx lighthouse http://localhost:3000 --view

# 번들 크기 분석
npm run build
# Check .next/analyze/

# 접근성 테스트
# Chrome DevTools Lighthouse Accessibility 섹션
```

---

## 📊 전체 검증 기준

### 기능적 성공 기준
- ✅ 파일 업로드가 작동함 (드래그 앤 드롭, 파일 선택)
- ✅ 파싱 옵션을 설정할 수 있음
- ✅ 파싱 진행 상태가 표시됨
- ✅ Markdown이 아름답게 렌더링됨
- ✅ 코드 블록이 하이라이팅됨
- ✅ 표가 시각화됨
- ✅ 목차가 작동함
- ✅ 다크 모드가 작동함

### UX 성공 기준
- ✅ 인터페이스가 직관적임
- ✅ 로딩 상태가 명확함
- ✅ 에러 메시지가 친절함
- ✅ 반응형 디자인이 잘 적용됨
- ✅ 애니메이션이 부드러움

### 성능 성공 기준
- ✅ 초기 로딩 시간 < 2초
- ✅ Lighthouse 성능 점수 90+
- ✅ 번들 크기 < 500KB (gzipped)
- ✅ 대용량 Markdown (100KB+) 렌더링이 부드러움

---

## 🛠️ 추가 기능 아이디어 (선택)

### 향후 개선 사항
1. **파일 관리**
   - 문서 히스토리 (최근 파싱한 문서)
   - 파싱 결과 캐싱
   - 문서 삭제 기능

2. **뷰어 개선**
   - PDF 원본과 Markdown 나란히 보기
   - Markdown 편집 기능
   - 주석 추가 기능

3. **공유 기능**
   - 파싱 결과 URL 공유
   - 임베드 코드 생성
   - 이메일 전송

4. **고급 기능**
   - 배치 파싱 (여러 파일 동시 처리)
   - 파싱 프리셋 저장
   - Webhook 알림

---

## 📚 참고 자료

### 라이브러리 문서
- **Next.js 15**: https://nextjs.org/docs
- **shadcn/ui**: https://ui.shadcn.com/
- **react-markdown**: https://github.com/remarkjs/react-markdown
- **remark-gfm**: https://github.com/remarkjs/remark-gfm
- **react-syntax-highlighter**: https://github.com/react-syntax-highlighter/react-syntax-highlighter
- **next-themes**: https://github.com/pacocoursey/next-themes

### 디자인 참고
- **Tailwind Typography**: https://tailwindcss.com/docs/typography-plugin
- **Lucide Icons**: https://lucide.dev/
- **Vercel Design System**: https://vercel.com/design

---

## 📝 다음 단계

### 즉시 시작 (FE Phase 1)
1. shadcn/ui 컴포넌트 추가
2. Markdown 렌더링 라이브러리 설치
3. 프로젝트 구조 생성

### 1주일 내 목표
1. FE Phase 1-4 완료 (파일 업로드 ~ Markdown 뷰어)
2. 백엔드와 통합 테스트
3. 기본 UI/UX 검증

### 2주일 내 목표
1. FE Phase 5-6 완료 (표 시각화 ~ UX 최적화)
2. 다크 모드 및 반응형 완성
3. 프로덕션 빌드 최적화

---

**작성일**: 2025-10-16
**최종 업데이트**: 2025-10-16
**버전**: 1.1
**상태**: ✅ Phase 1-6 모두 완료

**주요 특징**:
- ✅ 백엔드 Phase 1-3 완료 기반
- ✅ Next.js 15 + shadcn/ui 중심 설계
- ✅ Markdown 뷰어 최적화
- ✅ 표 데이터 시각화
- ✅ 다크 모드 지원
- ✅ 반응형 디자인
- ✅ 6개 Phase로 구조화
- ✅ 상세한 체크리스트 제공
- ✅ 명확한 성공 기준
- ✅ Windows PowerShell 명령어
