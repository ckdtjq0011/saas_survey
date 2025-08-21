# SaaS Survey Platform - Google Forms 클론 프로젝트

## 📋 프로젝트 개요

Google Forms와 유사한 기능을 제공하는 설문조사 플랫폼입니다. 사용자가 설문을 생성하고, 공유하며, 응답을 수집하고 분석할 수 있는 풀스택 웹 애플리케이션입니다.

## 🏗️ 현재 구현 상태

### ✅ 백엔드 (FastAPI) - 완료된 작업

#### 1. 아키텍처 리팩토링 (3계층 구조)
- **Repository Layer**: 데이터베이스 접근 로직 (`app/repositories/`)
  - `BaseRepository`: 공통 CRUD 작업
  - `SurveyRepository`: 설문 관련 DB 작업
  - `ResponseRepository`: 응답 관련 DB 작업
  - `UserRepository`: 사용자 관련 DB 작업

- **Service Layer**: 비즈니스 로직 (`app/services/`)
  - `SurveyService`: 설문 비즈니스 로직
  - `ResponseService`: 응답 비즈니스 로직
  - `AuthService`: 인증 비즈니스 로직
  - `ExportService`: 데이터 내보내기 로직

- **API Layer**: HTTP 요청/응답 처리 (`app/api/v1/`)
  - `/auth/*`: 인증 관련 엔드포인트
  - `/surveys/*`: 설문 CRUD
  - `/responses/*`: 응답 처리
  - `/exports/*`: CSV/JSON 내보내기

#### 2. 데이터 모델 (SQLAlchemy)
```python
# app/models/
- User: 사용자 정보 (email, username, full_name, hashed_password)
- Form: 설문 정보 (title, description, settings, share_token)
- Question: 질문 정보 (type, title, options, validation)
- FormResponse: 응답 정보 (respondent, submitted_at)
- Answer: 개별 답변 (text, number, json, file)
```

#### 3. 구현된 기능
- **인증 시스템**: JWT 토큰 기반, 회원가입/로그인
- **설문 관리**: CRUD, 복사, 공유 링크, 통계
- **응답 시스템**: 제출, 조회, 수정, 삭제, 중복 방지
- **데이터 내보내기**: CSV, JSON 형식
- **권한 관리**: 소유자만 수정/삭제 가능

#### 4. 질문 타입 지원
- `short_text`: 단답형
- `long_text`: 장문형
- `multiple_choice`: 객관식
- `checkbox`: 체크박스 (다중 선택)
- `dropdown`: 드롭다운
- `scale`: 척도 (1-5점 등)
- `date`: 날짜
- `time`: 시간
- `file_upload`: 파일 업로드
- `email`: 이메일
- `number`: 숫자

### ✅ 프론트엔드 (Next.js 14) - 완료된 작업

#### 1. 프로젝트 설정
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS
- Shadcn UI 컴포넌트
- Axios for API 통신

#### 2. 구현된 페이지
- **홈페이지** (`/`): 랜딩 페이지
- **로그인** (`/login`): JWT 인증
- **회원가입** (`/register`): 사용자 등록
- **설문 목록** (`/forms`): 내 설문 관리
- **설문 생성** (`/forms/create`): 새 설문 만들기

#### 3. UI 컴포넌트
- `Button`, `Input`, `Card`: Shadcn UI 기본 컴포넌트
- 질문 카드 컴포넌트
- 옵션 추가/삭제 기능

#### 4. API 클라이언트 (`lib/api.ts`)
```typescript
- authApi: 인증 관련 (register, login, me)
- surveyApi: 설문 관련 (list, create, get, update, delete)
- responseApi: 응답 관련 (submit, get, update)
- exportApi: 내보내기 (csv, json)
```

## 🚀 프로젝트 실행 방법

### 백엔드 서버 시작
```bash
cd C:\Dev\Python\saas_survey
uv run uvicorn app.main:app --reload --port 8000

# API 문서 확인
http://localhost:8000/docs
```

### 프론트엔드 서버 시작
```bash
cd C:\Dev\Python\saas_survey\frontend
npm run dev

# 브라우저에서 접속
http://localhost:3000
```

### 테스트 계정
```
# 새로 회원가입하거나
Email: test@example.com
Username: testuser
Password: password123
```

## 📝 추가 개발이 필요한 기능들

### 1. 핵심 기능 (우선순위 높음)

#### 설문 응답 페이지 (`/s/[token]`)
```typescript
// frontend/app/s/[token]/page.tsx
- 공유 링크로 접근
- 로그인 없이 응답 가능
- 질문별 유효성 검증
- 진행률 표시
- 응답 제출
```

#### 설문 편집 페이지 (`/forms/[id]/edit`)
```typescript
// frontend/app/forms/[id]/edit/page.tsx
- 기존 설문 불러오기
- 질문 추가/수정/삭제
- 드래그앤드롭으로 순서 변경
- 실시간 자동 저장
- 미리보기 기능
```

#### 응답 통계 페이지 (`/forms/[id]/responses`)
```typescript
// frontend/app/forms/[id]/responses/page.tsx
- 응답 목록 테이블
- 질문별 통계 차트 (recharts 사용)
- 개별 응답 상세 보기
- CSV/JSON 다운로드 버튼
```

### 2. 고급 기능 (중간 우선순위)

#### 조건부 로직
```typescript
// 특정 답변에 따라 다음 질문 표시/숨김
interface ConditionalLogic {
  questionId: number;
  condition: 'equals' | 'contains' | 'greater_than';
  value: any;
  targetQuestionId: number;
  action: 'show' | 'hide' | 'skip_to';
}
```

#### 섹션 구분
```typescript
// 설문을 여러 섹션으로 나누기
interface Section {
  id: number;
  title: string;
  description?: string;
  questions: Question[];
}
```

#### 실시간 협업
```typescript
// WebSocket을 사용한 실시간 편집
- 여러 사용자가 동시에 설문 편집
- 실시간 응답 업데이트
- 충돌 해결 메커니즘
```

### 3. UI/UX 개선사항

#### 반응형 디자인 개선
```css
/* 모바일 최적화 */
- 터치 친화적 인터페이스
- 스와이프 제스처
- 모바일 미리보기
```

#### 다크 모드
```typescript
// 시스템 설정 연동
- 자동/수동 테마 전환
- 사용자 선호도 저장
```

#### 접근성 개선
```html
<!-- ARIA labels, 키보드 네비게이션 -->
- 스크린 리더 지원
- 키보드 단축키
- 고대비 모드
```

### 4. 백엔드 개선사항

#### 성능 최적화
```python
# Redis 캐싱
- 설문 데이터 캐싱
- 응답 통계 캐싱
- 세션 관리

# 데이터베이스 최적화
- 인덱스 추가
- 쿼리 최적화
- 연결 풀링
```

#### 보안 강화
```python
# Rate limiting
- API 요청 제한
- DDoS 방어

# 입력 검증 강화
- XSS 방지
- SQL Injection 방지
- CSRF 토큰
```

#### 파일 업로드
```python
# S3 또는 로컬 스토리지
- 이미지 업로드
- 파일 크기 제한
- 바이러스 스캔
```

## 🐛 알려진 이슈 및 해결 방법

### 1. 공개 설문 인증 오류
```typescript
// 문제: 공개 설문도 인증을 요구함
// 해결: API 엔드포인트에서 선택적 인증 구현
const current_user = Depends(get_current_user_optional)
```

### 2. CORS 오류
```python
# 백엔드 CORS 설정 확인
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 타입 에러
```typescript
// TypeScript strict mode 설정
// tsconfig.json에서 strict: true 확인
```

## 💻 개발 환경 설정

### 필수 도구
- Python 3.10+
- Node.js 18+
- Git
- VS Code (권장)

### VS Code 확장 프로그램
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense

### 환경 변수 설정
```bash
# .env (백엔드)
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./survey.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# .env.local (프론트엔드)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📚 참고 자료

### 프로젝트 구조
```
saas_survey/
├── app/                    # FastAPI 백엔드
│   ├── api/               # API 라우트
│   │   └── v1/           # v1 버전 API
│   ├── core/             # 핵심 설정
│   ├── db/               # 데이터베이스
│   ├── models/           # SQLAlchemy 모델
│   ├── repositories/     # 데이터 액세스 레이어
│   ├── schemas/          # Pydantic 스키마
│   └── services/         # 비즈니스 로직 레이어
│
├── frontend/              # Next.js 프론트엔드
│   ├── app/              # App Router 페이지
│   ├── components/       # React 컴포넌트
│   │   ├── ui/          # Shadcn UI 컴포넌트
│   │   └── forms/       # 설문 관련 컴포넌트
│   ├── lib/             # 유틸리티 함수
│   ├── types/           # TypeScript 타입 정의
│   └── public/          # 정적 파일
│
├── tests/                # 테스트 파일
├── .env                  # 환경 변수
├── .gitignore           # Git 제외 파일
├── docker-compose.yml   # Docker 설정
├── pyproject.toml       # Python 의존성
├── package.json         # Node.js 의존성
└── README.md           # 프로젝트 문서
```

### API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 주요 명령어
```bash
# 백엔드 테스트
uv run pytest

# 프론트엔드 빌드
npm run build

# Docker 실행
docker-compose up -d

# 데이터베이스 마이그레이션
alembic upgrade head
```

## 🎯 다음 단계 권장 사항

1. **설문 응답 페이지 구현** - 가장 중요한 기능
2. **응답 통계 대시보드** - 데이터 시각화
3. **설문 편집 기능** - 사용성 향상
4. **모바일 반응형 개선** - 모바일 사용자 경험
5. **테스트 코드 작성** - 안정성 확보

## 📞 문의 및 지원

이 프로젝트를 계속 개발할 때 이 문서를 참조하세요. 
새로운 대화에서 "CLAUDE.md 파일을 참고하여 [원하는 기능]을 구현해주세요"라고 요청하면 됩니다.