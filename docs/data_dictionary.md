# Data Dictionary - SaaS Survey System

## 1. 엔티티별 속성 정의

### TENANT (테넌트)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 테넌트 고유 식별자 (PK) |
| name | string | Y | - | 테넌트명 |
| created_at | datetime | Y | now() | 생성 일시 |
| is_active | boolean | Y | True | 활성화 상태 |

### USER (사용자)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 사용자 고유 식별자 (PK) |
| tenant_id | string | Y | - | 소속 테넌트 ID (FK) |
| username | string | Y | - | 사용자명 (3-50자, 공백 불가, UK) |
| email | string | Y | - | 이메일 주소 |
| password_hash | string | Y | - | 암호화된 비밀번호 (bcrypt) |
| role | enum | Y | - | 사용자 역할 (TENANT_ADMIN/SURVEY_MANAGER/RESPONDENT) |
| created_at | datetime | Y | now() | 생성 일시 |
| is_active | boolean | Y | True | 활성화 상태 |

### SESSION (사용자 세션)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 세션 고유 식별자 (PK) |
| user_id | string | Y | - | 사용자 ID (FK) |
| tenant_id | string | Y | - | 테넌트 ID (FK) |
| api_key | string | Y | - | API 인증 키 (UK) |
| expires_at | datetime | Y | - | 만료 일시 |
| created_at | datetime | Y | now() | 생성 일시 |

### SURVEY (설문)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 설문 고유 식별자 (PK) |
| tenant_id | string | Y | - | 소속 테넌트 ID (FK) |
| owner_id | string | Y | - | 설문 소유자 ID (FK to USER) |
| title | string | Y | - | 설문 제목 |
| description | string | Y | - | 설문 설명 |
| created_at | datetime | Y | now() | 생성 일시 |

### QUESTION (질문)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 질문 고유 식별자 (PK) |
| survey_id | string | Y | - | 소속 설문 ID (FK) |
| text | string | Y | - | 질문 내용 |
| question_type | enum | Y | - | 질문 유형 (TEXT/RATING/MULTIPLE_CHOICE 등 9가지) |
| order | integer | Y | 0 | 질문 순서 (0부터 시작) |
| is_required | boolean | Y | True | 필수 응답 여부 |
| options | string | N | None | 선택지 목록 (ASCII 31로 구분) |
| category_id | string | N | None | 소속 범주 ID (FK, Optional) |

### CATEGORY (범주)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 범주 고유 식별자 (PK) |
| tenant_id | string | Y | - | 소속 테넌트 ID (FK) |
| name | string | Y | - | 범주명 |
| description | string | Y | - | 범주 설명 |
| parent_id | string | N | None | 상위 범주 ID (FK, 자기참조) |
| order | integer | Y | 0 | 표시 순서 |
| is_active | boolean | Y | True | 활성화 상태 |
| created_at | datetime | Y | now() | 생성 일시 |

### SURVEY_SESSION (설문 응답 세션)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 세션 고유 식별자 (PK) |
| survey_id | string | Y | - | 설문 ID (FK) |
| respondent_id | string | Y | - | 응답자 식별자 |
| started_at | datetime | Y | now() | 설문 시작 시각 |
| submitted_at | datetime | N | None | 설문 제출 시각 |
| completed | boolean | Y | False | 완료 여부 |
| completion_percentage | integer | Y | 0 | 진행률 (0-100) |
| user_agent | string | Y | - | 브라우저/디바이스 정보 |
| total_time_spent_seconds | integer | Y | 0 | 총 소요 시간 (초) |

### RESPONSE (응답)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 응답 고유 식별자 (PK) |
| survey_id | string | Y | - | 설문 ID (FK) |
| question_id | string | Y | - | 질문 ID (FK) |
| answer | string | Y | - | 답변 내용 |
| respondent_id | string | Y | - | 응답자 식별자 |
| answered_at | datetime | Y | now() | 답변 작성 일시 |
| session_id | string | Y | - | 세션 ID (FK to SURVEY_SESSION) |
| time_spent_seconds | integer | Y | 0 | 질문당 소요 시간 (초) |

### RESPONSE_HISTORY (응답 수정 이력)
| 속성명 | 데이터 타입 | 필수 | 기본값 | 설명 |
|--------|------------|------|--------|------|
| id | string | Y | UUID | 이력 고유 식별자 (PK) |
| response_id | string | Y | - | 응답 ID (FK) |
| old_answer | string | Y | - | 수정 전 답변 |
| new_answer | string | Y | - | 수정 후 답변 |
| updated_at | datetime | Y | now() | 수정 일시 |
| updated_by | string | Y | - | 수정한 사용자 ID |

## 2. Enum 타입 정의

### QuestionType (질문 유형)
| 값 | 표시명 | 설명 |
|----|--------|------|
| TEXT | 텍스트 답변 | 자유 텍스트 입력 |
| RATING | 평점 선택 | 1-5 점 평점 선택 |
| MULTIPLE_CHOICE | 객관식 (단일 선택) | 여러 옵션 중 하나 선택 |
| DATE | 날짜 입력 | YYYY-MM-DD 형식 날짜 |
| NUMBER | 숫자 입력 | 정수 또는 소수 입력 |
| EMAIL | 이메일 입력 | 이메일 주소 입력 |
| YES_NO | 예/아니오 선택 | 예 또는 아니오 선택 |
| SCALE_10 | 10점 척도 | 1-10 점 선택 |
| MULTI_SELECT | 다중 선택 | 여러 옵션 중 복수 선택 가능 |

### Role (사용자 역할)
| 값 | 설명 | 권한 |
|----|------|------|
| TENANT_ADMIN | 테넌트 관리자 | 모든 권한 (사용자 관리, 설문 관리, 결과 조회) |
| SURVEY_MANAGER | 설문 관리자 | 설문 CRUD, 결과 조회 |
| RESPONDENT | 응답자 | 설문 응답 제출만 가능 |

## 3. 제약 조건

### Unique 제약 (UK)
- USER.username: 테넌트 내에서 고유해야 함
- SESSION.api_key: 시스템 전체에서 고유해야 함

### Foreign Key 제약 (FK)
- 모든 엔티티의 tenant_id → TENANT.id
- USER.tenant_id → TENANT.id
- SESSION.user_id → USER.id
- SESSION.tenant_id → TENANT.id
- SURVEY.tenant_id → TENANT.id
- SURVEY.owner_id → USER.id
- QUESTION.survey_id → SURVEY.id
- QUESTION.category_id → CATEGORY.id (Optional)
- CATEGORY.tenant_id → TENANT.id
- CATEGORY.parent_id → CATEGORY.id (Self-reference, Optional)
- SURVEY_SESSION.survey_id → SURVEY.id
- RESPONSE.survey_id → SURVEY.id
- RESPONSE.question_id → QUESTION.id
- RESPONSE.session_id → SURVEY_SESSION.id
- RESPONSE_HISTORY.response_id → RESPONSE.id

### Check 제약
- QUESTION.order >= 0
- SURVEY_SESSION.completion_percentage BETWEEN 0 AND 100
- SURVEY_SESSION.total_time_spent_seconds >= 0
- RESPONSE.time_spent_seconds >= 0
- USER.username: 3-50자, 공백 불가
- USER.email: RFC 5322 표준 준수

## 4. 인덱스 설계

### Primary Index (자동 생성)
- 모든 테이블의 id 필드

### Secondary Index (성능 최적화용)
| 테이블 | 인덱스 필드 | 용도 |
|--------|------------|------|
| USER | tenant_id, username | 테넌트별 사용자 조회 |
| SURVEY | tenant_id, owner_id | 테넌트/소유자별 설문 조회 |
| QUESTION | survey_id, order | 설문별 질문 정렬 조회 |
| CATEGORY | tenant_id, parent_id | 계층 구조 탐색 |
| SURVEY_SESSION | survey_id, respondent_id | 설문별 응답자 세션 조회 |
| RESPONSE | session_id, question_id | 세션별 응답 조회 |
| RESPONSE | respondent_id, answered_at | 응답자별 시계열 조회 |
| RESPONSE_HISTORY | response_id, updated_at | 응답별 수정 이력 조회 |

## 5. 데이터 직렬화 규칙

### CSV 파일 저장 시
- 날짜/시간: ISO 8601 형식 (YYYY-MM-DDTHH:MM:SS)
- Boolean: true/false (소문자)
- 리스트 (options): ASCII 31 (Unit Separator) 구분자 사용
  - 하위호환성: 파이프(|) 구분자도 읽기 지원
- NULL 값: 빈 문자열로 저장
- UUID: 하이픈 포함 36자 형식

### 특수 필드 처리
- password_hash: bcrypt 해시 (60자)
- api_key: 32자 랜덤 문자열
- user_agent: 최대 255자로 제한
- options: 최소 2개 이상 필수 (객관식/다중선택 질문)