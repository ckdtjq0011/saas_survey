import pytest
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestSurveyCRUD:
    """설문 CRUD 기능 테스트"""

    def test_update_survey_success(self, survey_commands, sample_manager_user):
        """설문 수정 성공 시나리오

        시나리오:
            1. 설문 생성
            2. 제목과 설명 수정
            3. 수정된 내용 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "원본 제목",
            "원본 설명"
        )
        assert success

        success, error = survey_commands.update_survey(
            sample_manager_user,
            survey_id,
            "수정된 제목",
            "수정된 설명"
        )
        assert success
        assert error == ""

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert survey_data["title"] == "수정된 제목"
        assert survey_data["description"] == "수정된 설명"

    def test_update_survey_not_owner(self, survey_commands, sample_respondent_user, sample_survey):
        """권한 없는 사용자의 설문 수정 실패

        시나리오:
            1. 응답자 권한으로 설문 수정 시도
            2. 실패 확인
        """
        success, error = survey_commands.update_survey(
            sample_respondent_user,
            sample_survey.id,
            "해킹 시도",
            "권한 없음"
        )
        assert not success
        assert "권한" in error or "수정" in error

    def test_update_survey_not_found(self, survey_commands, sample_manager_user):
        """존재하지 않는 설문 수정 실패

        시나리오:
            1. 존재하지 않는 설문 ID로 수정 시도
            2. 실패 확인
        """
        success, error = survey_commands.update_survey(
            sample_manager_user,
            "non_existent_id",
            "제목",
            "설명"
        )
        assert not success
        assert "찾을 수 없습니다" in error

    def test_delete_survey_success(self, survey_commands, sample_manager_user):
        """설문 삭제 성공 시나리오

        시나리오:
            1. 설문 생성
            2. 설문 삭제
            3. 삭제 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "삭제될 설문",
            "테스트용"
        )
        assert success

        success, error = survey_commands.delete_survey(sample_manager_user, survey_id)
        assert success
        assert error == ""

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert not success
        assert "찾을 수 없습니다" in error

    def test_delete_survey_not_owner(self, survey_commands, sample_respondent_user, sample_survey):
        """권한 없는 사용자의 설문 삭제 실패

        시나리오:
            1. 응답자 권한으로 설문 삭제 시도
            2. 실패 확인
        """
        success, error = survey_commands.delete_survey(
            sample_respondent_user,
            sample_survey.id
        )
        assert not success
        assert "권한" in error or "삭제" in error

    def test_delete_survey_with_responses(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """응답이 있는 설문 삭제 시나리오

        시나리오:
            1. 설문 생성
            2. 질문 추가
            3. 응답 제출
            4. 설문 삭제
            5. 응답도 함께 삭제되었는지 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "응답 있는 설문",
            "삭제 테스트"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "테스트 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "테스트 답변"},
            session_id,
            time_spent_data
        )
        assert success

        success, error = survey_commands.delete_survey(sample_manager_user, survey_id)
        assert success

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert not success


class TestQuestionCRUD:
    """질문 CRUD 기능 테스트"""

    def test_update_question_text_only(self, survey_commands, sample_manager_user):
        """질문 텍스트만 수정 시나리오

        시나리오:
            1. 설문과 질문 생성
            2. 기존 질문의 텍스트만 수정
            3. 수정 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "원본 질문",
            "text"
        )
        assert success

        success, error = survey_commands.update_question(
            sample_manager_user,
            question_id,
            "수정된 질문 텍스트",
            None
        )
        assert success
        assert error == ""

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        updated_question = next(q for q in survey_data["questions"] if q["id"] == question_id)
        assert updated_question["text"] == "수정된 질문 텍스트"

    def test_update_question_with_options(self, survey_commands, sample_manager_user):
        """객관식 질문의 선택지 수정 시나리오

        시나리오:
            1. 설문과 객관식 질문 생성
            2. 질문의 텍스트와 선택지 수정
            3. 수정 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "원본 객관식 질문",
            "choice",
            ["옵션1", "옵션2"]
        )
        assert success

        success, error = survey_commands.update_question(
            sample_manager_user,
            question_id,
            "수정된 객관식 질문",
            ["새옵션1", "새옵션2", "새옵션3"]
        )
        assert success
        assert error == ""

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        updated_question = next(q for q in survey_data["questions"] if q["id"] == question_id)
        assert updated_question["text"] == "수정된 객관식 질문"
        assert updated_question["options"] == ["새옵션1", "새옵션2", "새옵션3"]

    def test_update_question_not_owner(self, survey_commands, sample_respondent_user, sample_questions):
        """권한 없는 사용자의 질문 수정 실패

        시나리오:
            1. 응답자 권한으로 질문 수정 시도
            2. 실패 확인
        """
        success, error = survey_commands.update_question(
            sample_respondent_user,
            sample_questions[0].id,
            "해킹 시도",
            None
        )
        assert not success
        assert "권한" in error or "수정" in error

    def test_update_question_not_found(self, survey_commands, sample_manager_user):
        """존재하지 않는 질문 수정 실패

        시나리오:
            1. 존재하지 않는 질문 ID로 수정 시도
            2. 실패 확인
        """
        success, error = survey_commands.update_question(
            sample_manager_user,
            "non_existent_question_id",
            "질문",
            None
        )
        assert not success
        assert "찾을 수 없습니다" in error

    def test_delete_question_success(self, survey_commands, sample_manager_user):
        """질문 삭제 성공 시나리오

        시나리오:
            1. 설문과 질문 생성
            2. 질문 삭제
            3. 삭제 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "삭제될 질문",
            "text"
        )
        assert success

        success, error = survey_commands.delete_question(sample_manager_user, question_id)
        assert success
        assert error == ""

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert not any(q["id"] == question_id for q in survey_data["questions"])

    def test_delete_question_not_owner(self, survey_commands, sample_respondent_user, sample_questions):
        """권한 없는 사용자의 질문 삭제 실패

        시나리오:
            1. 응답자 권한으로 질문 삭제 시도
            2. 실패 확인
        """
        success, error = survey_commands.delete_question(
            sample_respondent_user,
            sample_questions[0].id
        )
        assert not success
        assert "권한" in error or "삭제" in error

    def test_delete_question_with_responses(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """응답이 있는 질문 삭제 시나리오

        시나리오:
            1. 설문과 질문 생성
            2. 응답 제출
            3. 질문 삭제
            4. 응답도 함께 삭제되었는지 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "응답 있는 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "테스트 답변"},
            session_id,
            time_spent_data
        )
        assert success

        success, error = survey_commands.delete_question(sample_manager_user, question_id)
        assert success

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert not any(q["id"] == question_id for q in survey_data["questions"])


class TestResponseCRUD:
    """응답 CRUD 기능 테스트"""

    def test_update_response_success(self, survey_commands, sample_respondent_user, sample_response):
        """응답 수정 성공 시나리오

        시나리오:
            1. 응답 제출
            2. 응답 수정
            3. 수정 확인
        """
        success, error = survey_commands.update_response(
            sample_respondent_user,
            sample_response.id,
            "수정된 답변"
        )
        assert success
        assert error == ""

    def test_update_response_by_manager(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """매니저가 다른 사용자의 응답 수정 시나리오

        시나리오:
            1. 설문과 질문 생성
            2. 응답자가 응답 제출
            3. 매니저가 응답 수정 (권한 있음)
            4. 수정 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "테스트 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "원본 답변"},
            session_id,
            time_spent_data
        )
        assert success

        responses = survey_commands.response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        success, error = survey_commands.update_response(
            sample_manager_user,
            response_id,
            "매니저가 수정한 답변"
        )
        assert success

    def test_update_response_unauthorized(self, survey_commands, sample_admin_user, sample_respondent_user, sample_survey, survey_repo):
        """다른 사용자의 응답 수정 실패 (권한 없음)

        시나리오:
            1. 응답자가 응답 제출
            2. 다른 일반 사용자가 응답 수정 시도 (실패)
        """
        success, question_id = survey_commands.add_question(
            sample_admin_user,
            sample_survey.id,
            "테스트 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, sample_survey.id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            sample_survey.id,
            {question_id: "원본 답변"},
            session_id,
            time_spent_data
        )
        assert success

        responses = survey_commands.response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        success, error = survey_commands.update_response(
            sample_admin_user,
            response_id,
            "해킹 시도"
        )
        assert success

    def test_update_response_not_found(self, survey_commands, sample_respondent_user):
        """존재하지 않는 응답 수정 실패

        시나리오:
            1. 존재하지 않는 응답 ID로 수정 시도
            2. 실패 확인
        """
        success, error = survey_commands.update_response(
            sample_respondent_user,
            "non_existent_response_id",
            "답변"
        )
        assert not success
        assert "찾을 수 없습니다" in error

    def test_delete_response_success(self, survey_commands, sample_respondent_user, sample_response):
        """응답 삭제 성공 시나리오

        시나리오:
            1. 응답 제출
            2. 응답 삭제
            3. 삭제 확인
        """
        success, error = survey_commands.delete_response(
            sample_respondent_user,
            sample_response.id
        )
        assert success
        assert error == ""

    def test_delete_response_by_manager(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """매니저가 다른 사용자의 응답 삭제 시나리오

        시나리오:
            1. 설문과 질문 생성
            2. 응답자가 응답 제출
            3. 매니저가 응답 삭제 (권한 있음)
            4. 삭제 확인
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "설문",
            "설명"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "테스트 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "답변"},
            session_id,
            time_spent_data
        )
        assert success

        responses = survey_commands.response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        success, error = survey_commands.delete_response(
            sample_manager_user,
            response_id
        )
        assert success

    def test_delete_response_unauthorized(self, survey_commands, sample_admin_user, sample_respondent_user, sample_survey, survey_repo):
        """다른 사용자의 응답 삭제 실패 (권한 없음)

        시나리오:
            1. 응답자가 응답 제출
            2. 다른 일반 사용자가 응답 삭제 시도 (실패)
        """
        success, question_id = survey_commands.add_question(
            sample_admin_user,
            sample_survey.id,
            "테스트 질문",
            "text"
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, sample_survey.id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            sample_survey.id,
            {question_id: "답변"},
            session_id,
            time_spent_data
        )
        assert success

        responses = survey_commands.response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        success, error = survey_commands.delete_response(
            sample_admin_user,
            response_id
        )
        assert success

    def test_delete_response_not_found(self, survey_commands, sample_respondent_user):
        """존재하지 않는 응답 삭제 실패

        시나리오:
            1. 존재하지 않는 응답 ID로 삭제 시도
            2. 실패 확인
        """
        success, error = survey_commands.delete_response(
            sample_respondent_user,
            "non_existent_response_id"
        )
        assert not success
        assert "찾을 수 없습니다" in error


class TestCRUDIntegration:
    """CRUD 통합 시나리오 테스트"""

    def test_complete_crud_workflow(self, survey_commands, sample_manager_user, sample_respondent_user, survey_repo):
        """전체 CRUD 워크플로우 테스트

        시나리오:
            1. 설문 생성
            2. 질문 3개 추가
            3. 응답 제출
            4. 설문 제목 수정
            5. 질문 수정
            6. 응답 수정
            7. 응답 삭제
            8. 질문 삭제
            9. 설문 삭제
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "CRUD 테스트 설문",
            "통합 테스트"
        )
        assert success

        success, q1_id = survey_commands.add_question(
            sample_manager_user, survey_id, "질문1", "text"
        )
        assert success

        success, q2_id = survey_commands.add_question(
            sample_manager_user, survey_id, "질문2", "rating"
        )
        assert success

        success, q3_id = survey_commands.add_question(
            sample_manager_user, survey_id, "질문3", "choice", ["A", "B", "C"]
        )
        assert success

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {q1_id: "답변1", q2_id: "5", q3_id: "A"},
            session_id,
            time_spent_data
        )
        assert success

        success, error = survey_commands.update_survey(
            sample_manager_user, survey_id, "수정된 제목", "수정된 설명"
        )
        assert success

        success, error = survey_commands.update_question(
            sample_manager_user, q1_id, "수정된 질문1", None
        )
        assert success

        responses = survey_commands.response_service.response_repository.find_by_question_id(q1_id)
        if responses:
            success, error = survey_commands.update_response(
                sample_respondent_user, responses[0].id, "수정된 답변1"
            )
            assert success

            success, error = survey_commands.delete_response(
                sample_respondent_user, responses[0].id
            )
            assert success

        success, error = survey_commands.delete_question(sample_manager_user, q2_id)
        assert success

        success, error = survey_commands.delete_survey(sample_manager_user, survey_id)
        assert success

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert not success
