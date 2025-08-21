# SaaS Survey Platform - Project Status

## 현재 구현 상태

### ✅ 백엔드 (FastAPI)
- **아키텍처**: Repository/Service/API 3계층 구조
- **인증**: JWT 기반 인증 시스템
- **API 엔드포인트**: 
  - Auth: 회원가입, 로그인
  - Surveys: CRUD, 복사, 통계
  - Responses: 응답 제출/조회/수정
  - Export: CSV/JSON 내보내기
- **데이터베이스**: SQLite (개발) / PostgreSQL (운영)

### ✅ 프론트엔드 (Next.js 14)
- **페이지 구현**:
  - `/` - 홈페이지
  - `/login` - 로그인
  - `/register` - 회원가입  
  - `/forms` - 설문 목록
  - `/forms/create` - 설문 생성
  - `/s/[token]` - 설문 응답 페이지 ✅ **NEW!**
- **UI**: Shadcn UI + Tailwind CSS + Radix UI
- **상태관리**: React Hooks
- **API 통신**: Axios

## 🚀 실행 방법

### 백엔드
```bash
cd C:\Dev\Python\saas_survey
uv run uvicorn app.main:app --reload --port 8000
```

### 프론트엔드
```bash
cd C:\Dev\Python\saas_survey\frontend
npm run dev
```

## 📝 다음 작업 예정

### 우선순위 높음
1. ~~설문 응답 페이지 (`/s/[token]`)~~ ✅ **완료!**
2. 응답 통계 대시보드
3. 설문 편집 페이지
4. 실시간 자동 저장

### 추가 기능
- 조건부 로직 (특정 답변에 따른 질문 표시)
- 섹션 나누기
- 이미지/비디오 질문
- 이메일 알림
- 팀 협업 기능

## 🔧 기술 스택

### 백엔드
- FastAPI
- SQLAlchemy
- Pydantic
- JWT (python-jose)
- pytest

### 프론트엔드  
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Shadcn UI
- Axios
- React Hook Form

## 📁 프로젝트 구조

```
saas_survey/
├── app/                    # 백엔드
│   ├── api/               # API 엔드포인트
│   │   └── v1/           # v1 API
│   ├── repositories/      # 데이터 액세스
│   ├── services/         # 비즈니스 로직
│   ├── models/           # DB 모델
│   └── schemas/          # Pydantic 스키마
│
└── frontend/              # 프론트엔드
    ├── app/              # Next.js 페이지
    ├── components/       # React 컴포넌트
    ├── lib/             # 유틸리티
    └── types/           # TypeScript 타입
```

## 🐛 알려진 이슈
- ~~공개 설문 접근 시 인증 오류~~ ✅ **해결!**
- ~~share_token이 API 응답에 포함되지 않음~~ ✅ **해결!**
- 설문 편집 페이지 미구현
- 응답 통계 페이지 미구현
- 파일 업로드 실제 구현 필요 (현재 모의 구현)

## 💡 개선 아이디어
- Redis 캐싱 추가
- WebSocket으로 실시간 응답 업데이트
- 다국어 지원
- 테마 커스터마이징
- AI 기반 설문 제안