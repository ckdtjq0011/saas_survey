import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from pathlib import Path
from interface.api.main import app
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.types import QuestionType


@pytest.fixture
def test_data_dir(tmp_path):
    """임시 데이터 디렉토리"""
    return tmp_path / "test_data"


@pytest.fixture
def client(test_data_dir, monkeypatch):
    """TestClient with temporary data directory"""
    monkeypatch.setattr("interface.api.dependencies.DATA_DIR", test_data_dir)
    return TestClient(app)


@pytest.fixture
def survey_repo(test_data_dir):
    """Survey repository fixture"""
    return CsvSurveyRepository(test_data_dir)


@pytest.fixture
def response_repo(test_data_dir):
    """Response repository fixture"""
    return CsvResponseRepository(test_data_dir)


class TestHealthEndpoints:
    """헬스 체크 엔드포인트 테스트"""

    def test_root_health_check(self, client):
        """루트 헬스 체크"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "API가 정상 작동 중입니다" in data["message"]

    def test_health_endpoint(self, client):
        """/health 엔드포인트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSurveyEndpoints:
    """설문 엔드포인트 테스트"""

    def test_create_survey_success(self, client):
        """설문 생성 성공"""
        request_data = {
            "title": "만족도 조사",
            "description": "병원 서비스 만족도 조사"
        }

        response = client.post("/api/v1/surveys", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "survey_id" in data
        assert data["message"] == "설문이 생성되었습니다"

    def test_create_survey_validation_error(self, client):
        """설문 생성 검증 실패 - 빈 제목"""
        request_data = {
            "title": "",
            "description": "설명"
        }

        response = client.post("/api/v1/surveys", json=request_data)

        assert response.status_code == 422

    def test_list_surveys_empty(self, client):
        """설문 목록 조회 - 빈 목록"""
        response = client.get("/api/v1/surveys")

        assert response.status_code == 200
        data = response.json()
        assert data["surveys"] == []
        assert data["total"] == 0

    def test_list_surveys_with_data(self, client, survey_repo):
        """설문 목록 조회 - 데이터 있음"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        response = client.get("/api/v1/surveys")

        assert response.status_code == 200
        data = response.json()
        assert len(data["surveys"]) == 1
        assert data["total"] == 1
        assert data["surveys"][0]["title"] == "테스트 설문"

    def test_get_survey_success(self, client, survey_repo):
        """설문 상세 조회 성공"""
        survey_id = str(uuid.uuid4())
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=survey_id,
            text="질문1",
            question_type=QuestionType.TEXT,
            options=None
        )
        survey = Survey(
            id=survey_id,
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        response = client.get(f"/api/v1/surveys/{survey_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == survey_id
        assert data["title"] == "테스트 설문"
        assert len(data["questions"]) == 1
        assert data["questions"][0]["text"] == "질문1"

    def test_get_survey_not_found(self, client):
        """설문 상세 조회 - 존재하지 않음"""
        survey_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/surveys/{survey_id}")

        assert response.status_code == 404

    def test_add_text_question_success(self, client, survey_repo):
        """TEXT 질문 추가 성공"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        request_data = {
            "text": "의견을 작성해주세요",
            "question_type": "text"
        }

        response = client.post(f"/api/v1/surveys/{survey.id}/questions", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "question_id" in data
        assert data["message"] == "질문이 추가되었습니다"

    def test_add_rating_question_success(self, client, survey_repo):
        """RATING 질문 추가 성공"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        request_data = {
            "text": "만족도를 평가해주세요",
            "question_type": "rating"
        }

        response = client.post(f"/api/v1/surveys/{survey.id}/questions", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "question_id" in data

    def test_add_choice_question_success(self, client, survey_repo):
        """CHOICE 질문 추가 성공"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        request_data = {
            "text": "가장 좋았던 점은?",
            "question_type": "choice",
            "options": ["의료진", "시설", "대기시간"]
        }

        response = client.post(f"/api/v1/surveys/{survey.id}/questions", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "question_id" in data

    def test_add_question_invalid_type(self, client, survey_repo):
        """잘못된 질문 유형"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            owner_id=str(uuid.uuid4()),
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        request_data = {
            "text": "질문",
            "question_type": "invalid_type"
        }

        response = client.post(f"/api/v1/surveys/{survey.id}/questions", json=request_data)

        assert response.status_code == 422

    def test_add_question_to_nonexistent_survey(self, client):
        """존재하지 않는 설문에 질문 추가"""
        survey_id = str(uuid.uuid4())

        request_data = {
            "text": "질문",
            "question_type": "text"
        }

        response = client.post(f"/api/v1/surveys/{survey_id}/questions", json=request_data)

        assert response.status_code == 404


class TestResponseEndpoints:
    """응답 엔드포인트 테스트"""

    def test_submit_response_success(self, client, survey_repo):
        """응답 제출 성공"""
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문1",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )

        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        request_data = {
            "respondent_id": "respondent_001",
            "answers": {
                question_id: "답변입니다"
            },
            "session_id": str(uuid.uuid4()),
            "time_spent_data": {
                question_id: 5
            }
        }

        response = client.post(f"/api/v1/surveys/{survey_id}/responses", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "응답이 제출되었습니다"
        assert data["respondent_id"] == "respondent_001"

    def test_submit_response_to_nonexistent_survey(self, client):
        """존재하지 않는 설문에 응답 제출"""
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        request_data = {
            "respondent_id": "respondent_001",
            "answers": {
                question_id: "답변"
            },
            "session_id": str(uuid.uuid4()),
            "time_spent_data": {
                question_id: 5
            }
        }

        response = client.post(f"/api/v1/surveys/{survey_id}/responses", json=request_data)

        assert response.status_code == 404

    def test_submit_response_validation_error(self, client, survey_repo):
        """응답 제출 검증 실패"""
        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            owner_id=str(uuid.uuid4()),
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        request_data = {
            "respondent_id": "",
            "answers": {}
        }

        response = client.post(f"/api/v1/surveys/{survey.id}/responses", json=request_data)

        assert response.status_code == 422

    def test_get_survey_results_empty(self, client, survey_repo):
        """설문 결과 조회 - 응답 없음"""
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문1",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id="api_tenant",
            owner_id="api_anonymous",
            title="테스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )

        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        response = client.get(f"/api/v1/surveys/{survey_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["survey_id"] == survey_id
        assert question_id in data["results"]

    def test_get_survey_results_not_found(self, client):
        """설문 결과 조회 - 존재하지 않는 설문"""
        survey_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/surveys/{survey_id}/results")

        assert response.status_code == 404


class TestAPIIntegration:
    """API 통합 테스트"""

    def test_complete_survey_workflow(self, client):
        """설문 생성부터 결과 조회까지 전체 흐름"""
        create_response = client.post("/api/v1/surveys", json={
            "title": "병원 만족도 조사",
            "description": "환자 경험 개선을 위한 설문"
        })
        assert create_response.status_code == 201
        survey_id = create_response.json()["survey_id"]

        add_question_response = client.post(
            f"/api/v1/surveys/{survey_id}/questions",
            json={
                "text": "만족도를 평가해주세요",
                "question_type": "rating"
            }
        )
        assert add_question_response.status_code == 201
        question_id = add_question_response.json()["question_id"]

        get_survey_response = client.get(f"/api/v1/surveys/{survey_id}")
        assert get_survey_response.status_code == 200
        assert len(get_survey_response.json()["questions"]) == 1

        submit_response = client.post(
            f"/api/v1/surveys/{survey_id}/responses",
            json={
                "respondent_id": "patient_001",
                "answers": {
                    question_id: "5"
                },
                "session_id": str(uuid.uuid4()),
                "time_spent_data": {
                    question_id: 5
                }
            }
        )
        assert submit_response.status_code == 201

        results_response = client.get(f"/api/v1/surveys/{survey_id}/results")
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert question_id in results_data["results"]
        assert results_data["results"][question_id]["count"] == 1

    def test_multiple_question_types_workflow(self, client):
        """다양한 질문 유형 테스트"""
        create_response = client.post("/api/v1/surveys", json={
            "title": "종합 설문",
            "description": "다양한 질문 유형"
        })
        survey_id = create_response.json()["survey_id"]

        text_response = client.post(
            f"/api/v1/surveys/{survey_id}/questions",
            json={"text": "의견을 작성해주세요", "question_type": "text"}
        )
        assert text_response.status_code == 201

        rating_response = client.post(
            f"/api/v1/surveys/{survey_id}/questions",
            json={"text": "평점을 매겨주세요", "question_type": "rating"}
        )
        assert rating_response.status_code == 201

        choice_response = client.post(
            f"/api/v1/surveys/{survey_id}/questions",
            json={
                "text": "선택해주세요",
                "question_type": "choice",
                "options": ["옵션1", "옵션2"]
            }
        )
        assert choice_response.status_code == 201

        get_response = client.get(f"/api/v1/surveys/{survey_id}")
        assert get_response.status_code == 200
        assert len(get_response.json()["questions"]) == 3
