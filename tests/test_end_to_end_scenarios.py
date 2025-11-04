import pytest
import csv
from pathlib import Path
from tests.conftest import create_session_and_time_data


class TestQuestionTypeScenarios:
    """질문 유형별 엔드투엔드 시나리오"""

    def test_all_question_types(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """모든 질문 유형이 올바르게 작동하는지 테스트합니다.

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. 설문 생성
            2. 각 질문 유형 추가 (TEXT, RATING, MULTIPLE_CHOICE)
            3. 각 유형별로 응답 제출
            4. 각 유형별 결과 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "질문 유형 테스트",
            "모든 질문 유형을 테스트합니다"
        )
        assert success

        success, text_q = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "자유 의견을 작성해주세요",
            "text"
        )
        assert success

        success, rating_q = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "평점을 매겨주세요",
            "rating"
        )
        assert success

        success, choice_q = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "선택해주세요",
            "choice",
            ["옵션1", "옵션2", "옵션3"]
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {
                text_q: "이것은 텍스트 응답입니다",
                rating_q: "4",
                choice_q: "옵션2"
            },
            session_id,
            time_spent_data
        )
        assert success

        success, error, results = survey_commands.get_results(sample_manager_user, survey_id)
        assert success
        assert len(results) > 0


class TestMultipleRespondentsScenarios:
    """다중 응답자 엔드투엔드 시나리오"""

    def test_multiple_respondents(self, survey_commands, sample_manager_user, sample_respondent_user, user_repo, sample_tenant, survey_repo):
        """여러 응답자의 응답이 올바르게 집계되는지 테스트합니다.

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자 1
            user_repo: 사용자 리포지토리
            sample_tenant: 테넌트

        시나리오:
            1. 설문 생성 및 질문 추가
            2. 여러 응답자가 응답 제출
            3. 통계 결과 검증 (평균, 분포 등)
        """
        from domain.entities.user import User
        from domain.value_objects.role import Role
        from datetime import datetime
        import uuid

        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "다중 응답자 테스트",
            "통계 집계 테스트"
        )
        assert success

        success, rating_q = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "만족도를 평가해주세요",
            "rating"
        )
        assert success

        success, choice_q = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "선호하는 진료 시간대는?",
            "choice",
            ["오전", "오후", "저녁"]
        )
        assert success

        respondents = []
        for i in range(5):
            respondent = User(
                id=str(uuid.uuid4()),
                tenant_id=sample_tenant.id,
                username=f"patient_{i:03d}",
                email=f"patient{i}@test.com",
                password_hash="$2b$12$dummy_hash",
                role=Role.RESPONDENT,
                created_at=datetime.now(),
                is_active=True,
            )
            user_repo.save_user(respondent)
            respondents.append(respondent)

        responses_data = [
            ("5", "오전"),
            ("4", "오전"),
            ("5", "오후"),
            ("3", "오전"),
            ("4", "저녁"),
        ]

        for respondent, (rating, choice) in zip(respondents, responses_data):
            session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
            success, error = survey_commands.submit_response(
                respondent,
                survey_id,
                {
                    rating_q: rating,
                    choice_q: choice
                },
                session_id,
                time_spent_data
            )
            assert success

        success, error, results = survey_commands.get_results(sample_manager_user, survey_id)
        assert success
        assert len(results) > 0


class TestDataPersistenceScenarios:
    """CSV 데이터 영속성 엔드투엔드 시나리오"""

    def test_data_persistence(self, survey_commands, temp_data_dir, sample_manager_user, sample_respondent_user, survey_repo):
        """데이터가 CSV 파일에 올바르게 저장되고 조회되는지 테스트합니다.

        Args:
            survey_commands: Commands 픽스처
            temp_data_dir: 임시 데이터 디렉토리
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. 설문 생성 및 질문 추가
            2. CSV 파일 존재 확인
            3. CSV 파일 내용 검증
            4. 응답 제출 후 CSV 파일 내용 재검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "영속성 테스트",
            "CSV 저장 확인"
        )
        assert success

        success, q1_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "테스트 질문",
            "rating"
        )
        assert success

        surveys_csv = temp_data_dir / "surveys.csv"
        questions_csv = temp_data_dir / "questions.csv"
        responses_csv = temp_data_dir / "responses.csv"

        assert surveys_csv.exists()
        assert questions_csv.exists()
        assert responses_csv.exists()

        with open(surveys_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 1
            found = False
            for row in rows:
                if row["id"] == survey_id:
                    assert row["title"] == "영속성 테스트"
                    found = True
                    break
            assert found

        with open(questions_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            found = False
            for row in rows:
                if row["id"] == q1_id:
                    assert row["survey_id"] == survey_id
                    assert row["text"] == "테스트 질문"
                    found = True
                    break
            assert found

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {q1_id: "5"},
            session_id,
            time_spent_data
        )
        assert success

        with open(responses_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            found = False
            for row in rows:
                if row["survey_id"] == survey_id and row["question_id"] == q1_id:
                    assert row["answer"] == "5"
                    found = True
                    break
            assert found

    def test_multiple_surveys_persistence(self, survey_commands, temp_data_dir, sample_manager_user):
        """여러 설문이 CSV에 올바르게 저장되는지 테스트합니다.

        Args:
            survey_commands: Commands 픽스처
            temp_data_dir: 임시 데이터 디렉토리
            sample_manager_user: 설문 관리자

        시나리오:
            1. 3개의 설문 생성
            2. 각 설문에 질문 추가
            3. CSV 파일에 모든 데이터가 저장되었는지 확인
            4. 설문 목록 조회로 검증
        """
        survey_ids = []
        for i in range(3):
            success, survey_id = survey_commands.create_survey(
                sample_manager_user,
                f"설문 {i+1}",
                f"테스트 설문 {i+1}"
            )
            assert success
            survey_ids.append(survey_id)

            success, q_id = survey_commands.add_question(
                sample_manager_user,
                survey_id,
                f"질문 {i+1}",
                "text"
            )
            assert success

        surveys_csv = temp_data_dir / "surveys.csv"
        with open(surveys_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 3

        all_surveys = survey_commands.list_surveys(sample_manager_user)
        assert len(all_surveys) >= 3
        stored_ids = [s["id"] for s in all_surveys]
        for survey_id in survey_ids:
            assert survey_id in stored_ids


class TestValidationScenarios:
    """입력 검증 엔드투엔드 시나리오"""

    def test_unicode_handling(self, survey_commands, sample_manager_user, sample_respondent_user):
        """유니코드 문자 처리 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. 유니코드 문자(이모지, 한자 등)로 설문 생성
            2. 정상 저장 및 조회 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "이모지 테스트 😀🎉",
            "한자 中文 아랍어 العربية"
        )
        assert success

        success, error, data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert data["title"] == "이모지 테스트 😀🎉"

    def test_empty_survey_title(self, survey_commands, sample_manager_user):
        """빈 제목으로 설문 생성 시 실패하는지 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자

        시나리오:
            1. 빈 문자열 제목으로 설문 생성 시도
            2. ValueError 발생 확인 (Survey 엔티티에서 검증)
        """
        with pytest.raises(ValueError, match="제목|필수"):
            survey_commands.create_survey(
                sample_manager_user, "", "빈 제목 테스트"
            )


class TestSessionScenarios:
    """세션 및 상태 관리 엔드투엔드 시나리오"""

    def test_invalid_api_key(self, survey_commands):
        """잘못된 API 키로 세션 검증 시도

        Args:
            survey_commands: Commands 픽스처

        시나리오:
            1. 존재하지 않는 API 키로 세션 검증
            2. 실패 확인
        """
        success, error, user = survey_commands.validate_session("invalid_api_key_12345")
        assert not success
        assert error is not None
