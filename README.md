# SaaS 병원 만족도 설문조사 플랫폼 MVP

병원 만족도 조사를 위한 DDD 기반 설문조사 플랫폼입니다.

## 프로젝트 구조

```
saas_survey/
├── domain/                          # 도메인 계층 (핵심 비즈니스 로직)
│   ├── entities/                    # 엔티티
│   │   ├── survey.py               # 설문 엔티티
│   │   ├── question.py             # 질문 엔티티
│   │   └── response.py             # 응답 엔티티
│   ├── value_objects/               # 값 객체
│   │   └── types.py                # QuestionType enum
│   └── repositories/                # 저장소 인터페이스
│       ├── survey_repository.py
│       └── response_repository.py
├── application/                     # 애플리케이션 계층 (유스케이스)
│   ├── survey_service.py           # 설문 서비스
│   └── response_service.py         # 응답 서비스
├── infrastructure/                  # 인프라스트럭처 계층
│   └── persistence/                # 영속성 구현
│       ├── csv_survey_repository.py
│       └── csv_response_repository.py
├── interface/                       # 인터페이스 계층
│   └── cli/
│       └── commands.py             # CLI 명령어 핸들러
├── tests/                          # 시나리오 테스트
│   ├── conftest.py                # pytest 픽스처
│   ├── test_scenarios.py          # 통합 테스트
│   └── README.md                  # 테스트 가이드
├── data/                           # CSV 데이터 저장소
│   ├── surveys.csv
│   ├── questions.csv
│   └── responses.csv
├── main.py                         # 진입점 및 데모
└── run_tests.py                    # 테스트 실행 스크립트
```

## 아키텍처

DDD 4계층 구조로 설계되었습니다:

1. **Domain** - 비즈니스 로직, 엔티티, 저장소 인터페이스
2. **Application** - 유스케이스, 서비스
3. **Infrastructure** - CSV 기반 저장소 구현
4. **Interface** - CLI 명령어 핸들러

## 핵심 기능

- 설문 생성 및 질문 추가 (평점형, 객관식, 텍스트형)
- 응답 제출
- 결과 조회 및 통계 (평균 평점, 분포 등)
- CSV 기반 영속화

## 실행 방법

### MVP 데모 실행

```bash
python main.py
```

### 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/test_scenarios.py -v

# 또는 테스트 스크립트 사용
python run_tests.py

# 특정 시나리오만 실행
pytest tests/test_scenarios.py::TestScenario01 -v
```

## 테스트 시나리오

총 8개의 시나리오 테스트가 구현되어 있습니다:

1. **전체 워크플로우** (test_complete_survey_workflow)
   - 설문 생성부터 결과 조회까지 전체 흐름 검증

2. **질문 유형 테스트** (test_all_question_types)
   - TEXT, RATING, MULTIPLE_CHOICE 모든 유형 검증

3. **다중 응답자** (test_multiple_respondents)
   - 10명의 응답자 통계 집계 검증

4. **에러 케이스** (3개 테스트)
   - 존재하지 않는 설문 조회
   - 잘못된 질문 유형
   - 기타 에러 처리

5. **CSV 영속성** (2개 테스트)
   - 데이터 저장 및 조회 검증
   - 다중 설문 영속성 검증

자세한 테스트 가이드는 `tests/README.md` 참조

## 설계 특징

- **dataclass 사용**: 모든 엔티티는 frozen=True, slots=True
- **타입힌트 필수**: 모든 함수에 타입힌트 적용
- **예외 처리**: 도메인/애플리케이션은 예외 발생만, CLI에서 처리
- **CSV 영속화**: UTF-8 인코딩, 자동 생성
- **KISS, YAGNI, DRY** 원칙 준수

## 질문 유형

- **TEXT**: 텍스트 답변
- **RATING**: 평점 답변 (1-5)
- **MULTIPLE_CHOICE**: 객관식

## 데이터 저장

모든 데이터는 `data/` 디렉토리의 CSV 파일에 저장됩니다:
- `surveys.csv`: 설문 기본 정보
- `questions.csv`: 질문 정보
- `responses.csv`: 응답 정보

## CLI 명령어 사용 예시

```python
from pathlib import Path
from interface.cli.commands import SurveyCommands

commands = SurveyCommands(Path("data"))

# 설문 생성
survey_id = commands.create_survey(
    title="병원 만족도 조사",
    description="설문 설명"
)

# 질문 추가
question_id = commands.add_question(
    survey_id=survey_id,
    text="전반적인 병원 서비스에 만족하십니까?",
    question_type="rating"
)

# 응답 제출
commands.submit_response(
    survey_id=survey_id,
    respondent_id="patient_001",
    answers={question_id: "5"}
)

# 결과 조회
results = commands.get_results(survey_id)
```

## 코드 통계

```
domain/          275 lines (엔티티, Value Object, Repository 인터페이스)
application/     200 lines (SurveyService, ResponseService)
infrastructure/  188 lines (CSV 저장소 구현)
interface/       171 lines (CLI 명령어 핸들러)
tests/           330 lines (시나리오 테스트)
---------------------------------------------------------
총 구현 코드:    1164 lines
```

## 향후 확장 계획

- 사용자 인증/권한 관리
- 데이터베이스 연동 (PostgreSQL)
- REST API (FastAPI)
- 웹 프론트엔드
- 고급 통계 분석
- 파일 내보내기 (PDF, Excel)
