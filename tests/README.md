# 시나리오 테스트 가이드

## 개요

실제 사용 흐름을 테스트하는 통합 테스트 시나리오입니다.

## 테스트 실행 방법

### 방법 1: pytest 직접 실행

```bash
pytest tests/test_scenarios.py -v
```

### 방법 2: 테스트 스크립트 실행

```bash
python run_tests.py
```

## 테스트 시나리오

### 시나리오 1: 전체 워크플로우 테스트
**파일**: `test_scenarios.py::TestScenario01::test_complete_survey_workflow`

**목적**: 병원 관리자가 설문을 생성하고 환자가 응답하는 전체 흐름 검증

**단계**:
1. 병원 관리자가 만족도 설문 생성
2. 3가지 유형의 질문 추가 (평점형, 객관식, 텍스트형)
3. 환자 1명이 응답 제출
4. 설문 조회 및 데이터 검증
5. 결과 조회 및 통계 검증

**검증 항목**:
- 설문 ID 생성 확인
- 질문 ID 생성 확인
- 설문 데이터 정확성
- 응답 제출 성공
- 결과 집계 정확성 (평균, 분포, 텍스트 답변)

---

### 시나리오 2: 질문 유형 테스트
**파일**: `test_scenarios.py::TestScenario02::test_all_question_types`

**목적**: 모든 질문 유형이 올바르게 작동하는지 검증

**질문 유형**:
- TEXT: 자유 텍스트 입력
- RATING: 평점 (1-5)
- MULTIPLE_CHOICE: 객관식 선택

**검증 항목**:
- 각 질문 유형별 생성 성공
- 각 질문 유형별 응답 저장
- 각 질문 유형별 결과 집계

---

### 시나리오 3: 다중 응답자 테스트
**파일**: `test_scenarios.py::TestScenario03::test_multiple_respondents`

**목적**: 여러 응답자의 응답이 올바르게 집계되는지 검증

**테스트 데이터**:
- 응답자 수: 10명
- 평점 질문: 평균 계산 검증
- 객관식 질문: 분포 집계 검증

**검증 항목**:
- 응답 수 정확성 (10개)
- 평균 평점 계산 정확성
- 선택지별 분포 정확성
  - 오전: 5명
  - 오후: 3명
  - 저녁: 2명

---

### 시나리오 4: 에러 케이스 테스트
**파일**: `test_scenarios.py::TestScenario04`

**목적**: 잘못된 입력에 대한 에러 처리 검증

**테스트 케이스**:
1. `test_invalid_survey_id`: 존재하지 않는 설문 ID 조회 시 ValueError 발생
2. `test_add_question_to_nonexistent_survey`: 존재하지 않는 설문에 질문 추가 시 ValueError 발생
3. `test_invalid_question_type`: 잘못된 질문 유형으로 질문 추가 시 ValueError 발생

**검증 항목**:
- 적절한 예외 타입 발생 (ValueError)
- 에러 메시지 정확성

---

### 시나리오 5: CSV 영속성 테스트
**파일**: `test_scenarios.py::TestScenario05`

**목적**: 데이터가 CSV 파일에 올바르게 저장되고 조회되는지 검증

**테스트 케이스**:
1. `test_data_persistence`: 단일 설문의 CSV 저장/조회
2. `test_multiple_surveys_persistence`: 다중 설문의 CSV 저장/조회

**검증 항목**:
- CSV 파일 생성 확인
  - surveys.csv
  - questions.csv
  - responses.csv
- CSV 파일 내용 정확성
- 데이터 인코딩 (UTF-8 with BOM)
- 설문 목록 조회 정확성

---

## 픽스처

### `temp_data_dir`
임시 데이터 디렉토리를 생성하고 테스트 종료 후 자동 삭제합니다.

**위치**: `conftest.py:4`

**용도**: 테스트 간 데이터 격리, CSV 파일 저장 위치 제공

### `survey_commands`
테스트용 SurveyCommands 인스턴스를 생성합니다.

**위치**: `conftest.py:20`

**용도**: CLI 명령어 인터페이스 제공

---

## 테스트 결과 예시

```
============================= test session starts =============================
collected 8 items

tests/test_scenarios.py::TestScenario01::test_complete_survey_workflow PASSED
tests/test_scenarios.py::TestScenario02::test_all_question_types PASSED
tests/test_scenarios.py::TestScenario03::test_multiple_respondents PASSED
tests/test_scenarios.py::TestScenario04::test_invalid_survey_id PASSED
tests/test_scenarios.py::TestScenario04::test_add_question_to_nonexistent_survey PASSED
tests/test_scenarios.py::TestScenario04::test_invalid_question_type PASSED
tests/test_scenarios.py::TestScenario05::test_data_persistence PASSED
tests/test_scenarios.py::TestScenario05::test_multiple_surveys_persistence PASSED

============================== 8 passed in 0.36s ==============================
```

## 테스트 추가 가이드

새로운 시나리오를 추가하려면:

1. `test_scenarios.py`에 새로운 테스트 클래스 생성
2. 클래스명은 `TestScenarioXX` 형식으로 지정
3. 테스트 메서드는 `test_` 접두사 사용
4. Docstring에 시나리오 설명 작성
5. 픽스처를 활용하여 테스트 격리 보장

### 예시

```python
class TestScenario06:
    """시나리오 6: 새로운 기능 테스트"""

    def test_new_feature(self, survey_commands):
        """새로운 기능이 올바르게 작동하는지 테스트합니다.

        Args:
            survey_commands: SurveyCommands 픽스처

        시나리오:
            1. 단계 1 설명
            2. 단계 2 설명
            3. 검증
        """
        # 테스트 코드 작성
        pass
```

## 문제 해결

### 테스트가 실패하는 경우

1. 에러 메시지 확인
2. `pytest tests/test_scenarios.py -v -s` 로 상세 출력 확인
3. 특정 테스트만 실행: `pytest tests/test_scenarios.py::TestScenario01 -v`
4. 디버깅: `pytest tests/test_scenarios.py --pdb`

### CSV 파일 확인

테스트 중 CSV 파일을 확인하려면 `temp_data_dir` 픽스처를 수정하여 자동 삭제를 비활성화하세요.
