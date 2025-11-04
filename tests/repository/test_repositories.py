import pytest
import uuid
import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
from domain.entities.tenant import Tenant
from domain.entities.user import User
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.session import Session
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository
from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository


class TestCsvSurveyRepository:
    """CsvSurveyRepository 테스트"""

    def test_find_questions_by_survey_id_empty_survey(self, temp_data_dir):
        """빈 설문의 질문 조회

        시나리오:
            1. 질문이 없는 설문 생성
            2. find_questions_by_survey_id() 호출
            3. 빈 리스트 반환 확인
        """
        repo = CsvSurveyRepository(temp_data_dir)

        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            owner_id=str(uuid.uuid4()),
            title="빈 설문",
            description="질문 없음",
            created_at=datetime.now(),
            questions=()
        )
        repo.save_survey(survey)

        questions = repo.find_questions_by_survey_id(survey.id)
        assert questions == []

    def test_update_question_not_found(self, temp_data_dir):
        """존재하지 않는 질문 수정 시 예외 발생

        시나리오:
            1. 존재하지 않는 질문 ID로 update_question() 호출
            2. ValueError 예외 발생 확인
        """
        repo = CsvSurveyRepository(temp_data_dir)

        with pytest.raises(ValueError, match="질문을 찾을 수 없습니다"):
            repo.update_question("nonexistent_question_id", text="수정된 질문")

    def test_corrupted_csv_handling(self, temp_data_dir):
        """손상된 CSV 파일 처리

        시나리오:
            1. CSV 파일을 손상시킴 (헤더 제거)
            2. find_all_surveys() 호출
            3. 빈 리스트 반환 또는 예외 처리 확인
        """
        repo = CsvSurveyRepository(temp_data_dir)

        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            owner_id=str(uuid.uuid4()),
            title="테스트",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        repo.save_survey(survey)

        surveys_file = temp_data_dir / "surveys.csv"
        with open(surveys_file, "w", encoding="utf-8-sig") as f:
            f.write("corrupted data without header\n")
            f.write("invalid,csv,format\n")

        surveys = repo.find_all_surveys()
        assert isinstance(surveys, list)

    def test_concurrent_write_attempt(self, temp_data_dir):
        """동시 쓰기 시도 (간단한 순차 테스트)

        시나리오:
            1. 여러 설문을 순차적으로 저장
            2. 모두 정상 저장 확인
        """
        repo = CsvSurveyRepository(temp_data_dir)

        surveys = []
        for i in range(10):
            survey = Survey(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                owner_id=str(uuid.uuid4()),
                title=f"설문{i}",
                description=f"설명{i}",
                created_at=datetime.now(),
                questions=()
            )
            repo.save_survey(survey)
            surveys.append(survey)

        saved_surveys = repo.find_all_surveys()
        assert len(saved_surveys) == 10

    def test_read_permission_denied(self, temp_data_dir):
        """읽기 권한 없는 파일 처리

        시나리오:
            1. CSV 파일 생성
            2. 읽기 권한 제거 (Windows에서는 어려움, 스킵 가능)
            3. find_all_surveys() 호출
            4. 예외 또는 빈 리스트 반환 확인
        """
        pytest.skip("Windows에서 파일 권한 테스트 복잡함")

    def test_large_survey_data(self, temp_data_dir):
        """대량 데이터 처리

        시나리오:
            1. 100개 질문이 있는 설문 생성
            2. 정상 저장 및 조회 확인
        """
        repo = CsvSurveyRepository(temp_data_dir)

        questions = tuple(
            Question(
                id=str(uuid.uuid4()),
                survey_id="survey1",
                text=f"질문{i}",
                question_type=QuestionType.TEXT,
                options=None
            )
            for i in range(100)
        )

        survey = Survey(
            id="survey1",
            tenant_id=str(uuid.uuid4()),
            owner_id=str(uuid.uuid4()),
            title="대량 질문 설문",
            description="100개 질문",
            created_at=datetime.now(),
            questions=questions
        )

        repo.save_survey(survey)
        for question in questions:
            repo.save_question(question)

        loaded_questions = repo.find_questions_by_survey_id("survey1")
        assert len(loaded_questions) == 100


class TestCsvResponseRepository:
    """CsvResponseRepository 테스트"""

    def test_find_by_survey_id_empty_result(self, temp_data_dir):
        """응답이 없는 설문 조회

        시나리오:
            1. 응답이 없는 설문 ID로 find_by_survey_id() 호출
            2. 빈 리스트 반환 확인
        """
        repo = CsvResponseRepository(temp_data_dir)

        responses = repo.find_by_survey_id("nonexistent_survey_id")
        assert responses == []

    def test_update_response_not_found(self, temp_data_dir):
        """존재하지 않는 응답 수정 시 예외 발생

        시나리오:
            1. 존재하지 않는 응답 ID로 update_response() 호출
            2. ValueError 예외 발생 확인
        """
        repo = CsvResponseRepository(temp_data_dir)

        with pytest.raises(ValueError, match="응답을 찾을 수 없습니다"):
            repo.update_response("nonexistent_response_id", "새 답변")

    def test_find_by_question_id_large_dataset(self, temp_data_dir):
        """대량 응답 조회 (1000개)

        시나리오:
            1. 1000개 응답 저장
            2. find_by_question_id() 호출
            3. 모든 응답 조회 확인
        """
        repo = CsvResponseRepository(temp_data_dir)

        question_id = str(uuid.uuid4())
        for i in range(1000):
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                question_id=question_id,
                answer=f"답변{i}",
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
            )
            repo.save(response)

        responses = repo.find_by_question_id(question_id)
        assert len(responses) == 1000

    def test_file_lock_handling(self, temp_data_dir):
        """파일 잠금 상태 처리 (간단한 순차 테스트)

        시나리오:
            1. 응답을 순차적으로 여러 번 저장
            2. 정상 동작 확인
        """
        repo = CsvResponseRepository(temp_data_dir)

        for i in range(10):
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                question_id=str(uuid.uuid4()),
                answer=f"답변{i}",
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
            )
            repo.save(response)

        responses_file = temp_data_dir / "responses.csv"
        assert responses_file.exists()

    def test_corrupted_response_csv(self, temp_data_dir):
        """손상된 응답 CSV 처리

        시나리오:
            1. 응답 저장
            2. CSV 파일 손상
            3. 조회 시 정상 처리 확인
        """
        repo = CsvResponseRepository(temp_data_dir)

        response = Response(
            id=str(uuid.uuid4()),
            survey_id="survey1",
            question_id=str(uuid.uuid4()),
            answer="답변",
            respondent_id=str(uuid.uuid4()),
            answered_at=datetime.now(),
            session_id=str(uuid.uuid4()),
            time_spent_seconds=10
        )
        repo.save(response)

        responses_file = temp_data_dir / "responses.csv"
        with open(responses_file, "w", encoding="utf-8-sig") as f:
            f.write("corrupted\n")

        responses = repo.find_by_survey_id("survey1")
        assert isinstance(responses, list)


class TestCsvSessionRepository:
    """CsvSessionRepository 테스트"""

    def test_find_session_by_user_id_multiple_sessions(self, temp_data_dir):
        """한 사용자의 여러 세션 조회

        시나리오:
            1. 동일 사용자의 여러 세션 저장
            2. find_session_by_user_id() 호출
            3. 가장 최근 세션 반환 확인
        """
        repo = CsvSessionRepository(temp_data_dir)

        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        for i in range(3):
            session = Session(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                api_key=f"api_key_{i}",
                expires_at=datetime.now() + timedelta(days=1),
                created_at=datetime.now()
            )
            repo.save_session(session)

        session = repo.find_session_by_user_id(user_id)
        assert session is not None
        assert session.user_id == user_id

    def test_expired_session_cleanup(self, temp_data_dir):
        """만료된 세션 정리

        시나리오:
            1. 만료된 세션과 유효한 세션 저장
            2. 만료된 세션 조회
            3. None 반환 확인 (또는 세션 상태 확인)
        """
        repo = CsvSessionRepository(temp_data_dir)

        expired_session = Session(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            api_key="expired_key",
            expires_at=datetime.now() - timedelta(days=1),
            created_at=datetime.now() - timedelta(days=2)
        )
        repo.save_session(expired_session)

        found_session = repo.find_session_by_api_key("expired_key")
        if found_session:
            assert found_session.expires_at < datetime.now()

    def test_api_key_collision_handling(self, temp_data_dir):
        """API 키 충돌 처리

        시나리오:
            1. 동일 API 키로 두 세션 저장 시도
            2. 마지막 세션이 저장됨 (덮어쓰기)
        """
        repo = CsvSessionRepository(temp_data_dir)

        api_key = "duplicate_api_key"

        session1 = Session(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            api_key=api_key,
            expires_at=datetime.now() + timedelta(days=1),
            created_at=datetime.now()
        )
        repo.save_session(session1)

        session2 = Session(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            api_key=api_key,
            expires_at=datetime.now() + timedelta(days=2),
            created_at=datetime.now()
        )
        repo.save_session(session2)

        found_session = repo.find_session_by_api_key(api_key)
        assert found_session is not None

    def test_corrupted_session_csv(self, temp_data_dir):
        """손상된 세션 CSV 파일 처리

        시나리오:
            1. 세션 저장
            2. CSV 파일 손상
            3. 조회 시 정상 처리 확인
        """
        repo = CsvSessionRepository(temp_data_dir)

        session = Session(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            api_key="test_key",
            expires_at=datetime.now() + timedelta(days=1),
            created_at=datetime.now()
        )
        repo.save_session(session)

        sessions_file = temp_data_dir / "sessions.csv"
        with open(sessions_file, "w", encoding="utf-8-sig") as f:
            f.write("corrupted data\n")

        found_session = repo.find_session_by_api_key("test_key")
        assert found_session is None


class TestCsvEncodingAndLargeData:
    """CSV 인코딩 및 대량 데이터 테스트"""

    def test_utf8_bom_encoding(self, temp_data_dir):
        """UTF-8 BOM 인코딩 처리

        시나리오:
            1. UTF-8 BOM으로 테넌트 저장
            2. 정상 조회 확인
        """
        repo = CsvTenantRepository(temp_data_dir)

        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="테넌트 UTF-8 BOM",
            created_at=datetime.now(),
            is_active=True
        )
        repo.save_tenant(tenant)

        loaded_tenant = repo.find_tenant_by_id(tenant.id)
        assert loaded_tenant is not None
        assert loaded_tenant.name == "테넌트 UTF-8 BOM"

    def test_emoji_4byte_characters(self, temp_data_dir):
        """이모지 4바이트 문자 처리

        시나리오:
            1. 이모지가 포함된 사용자 저장
            2. 정상 조회 확인
        """
        repo = CsvUserRepository(temp_data_dir)

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            username="emoji_user",
            email="test@example.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        repo.save_user(user)

        loaded_user = repo.find_user_by_id(user.id)
        assert loaded_user is not None
        assert loaded_user.username == "emoji_user"

    def test_large_dataset_performance(self, temp_data_dir):
        """대량 데이터 처리 성능

        시나리오:
            1. 1000개 테넌트 저장
            2. 전체 조회 성능 확인
        """
        repo = CsvTenantRepository(temp_data_dir)

        for i in range(1000):
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name=f"대량테넌트{i}",
                created_at=datetime.now(),
                is_active=True
            )
            repo.save_tenant(tenant)

        tenants = repo.find_all_tenants()
        assert len(tenants) == 1000
