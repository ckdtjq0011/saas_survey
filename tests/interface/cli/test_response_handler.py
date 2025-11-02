import pytest
from unittest.mock import Mock, patch
from domain.entities.user import User
from domain.entities.response import Response
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from interface.cli.handlers.response_handler import ResponseHandler
from interface.cli.commands import Commands
from interface.cli.ui_helper import ConsoleUI
from datetime import datetime


@pytest.fixture
def mock_commands():
    """Mock Commands fixture"""
    commands = Mock(spec=Commands)
    commands.response_service = Mock()
    commands.response_service.response_repository = Mock()
    return commands


@pytest.fixture
def mock_ui():
    """Mock ConsoleUI fixture"""
    ui = Mock(spec=ConsoleUI)
    ui.print_section = Mock()
    ui.print_success = Mock()
    ui.print_error = Mock()
    ui.print_info = Mock()
    ui.print_warning = Mock()
    ui.pause = Mock()
    ui.get_input = Mock()
    ui.get_validated_input = Mock()
    ui.get_int_input = Mock()
    ui.print_surveys_table = Mock()
    ui.print_results_table = Mock()
    ui.confirm = Mock()
    return ui


@pytest.fixture
def response_handler(mock_commands, mock_ui):
    """ResponseHandler fixture"""
    return ResponseHandler(mock_commands, mock_ui)


@pytest.fixture
def sample_user():
    """Sample user fixture"""
    return User(
        id="user123",
        tenant_id="tenant123",
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.RESPONDENT,
        created_at=datetime.now(),
        is_active=True
    )


class TestResponseHandlerSubmitResponse:
    """응답 제출 flow 테스트"""

    def test_submit_text_response_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """TEXT 응답 제출 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "description": "설명",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = True
        mock_commands.submit_response.return_value = (True, None)

        with patch.object(response_handler, '_collect_answers', return_value={"q1": "답변1"}):
            response_handler.submit_response_flow(sample_user)

        mock_commands.submit_response.assert_called_once()
        mock_ui.print_success.assert_called_once_with("응답이 제출되었습니다")

    def test_submit_multiple_choice_response_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """MULTIPLE_CHOICE 응답 제출 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "description": "설명",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "multiple_choice", "options": ["옵션1", "옵션2", "옵션3"]}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = True
        mock_commands.submit_response.return_value = (True, None)

        with patch.object(response_handler, '_collect_answers', return_value={"q1": "옵션2"}):
            response_handler.submit_response_flow(sample_user)

        mock_ui.print_success.assert_called_once()

    def test_submit_rating_response_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """RATING 응답 제출 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "description": "설명",
            "questions": [
                {"id": "q1", "text": "평점", "type": "rating", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = True
        mock_commands.submit_response.return_value = (True, None)

        with patch.object(response_handler, '_collect_answers', return_value={"q1": "5"}):
            response_handler.submit_response_flow(sample_user)

        mock_ui.print_success.assert_called_once()

    def test_submit_response_no_survey(self, response_handler, mock_ui, mock_commands, sample_user):
        """설문이 없을 때 응답 제출 시도"""
        mock_commands.list_surveys.return_value = []

        response_handler.submit_response_flow(sample_user)

        mock_ui.print_info.assert_called_once_with("설문이 없습니다")
        mock_commands.submit_response.assert_not_called()

    def test_submit_response_cancelled(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 제출 취소"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "description": "설명",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.get_input.return_value = "답변1"
        mock_ui.confirm.return_value = False

        response_handler.submit_response_flow(sample_user)

        mock_commands.submit_response.assert_not_called()

    def test_submit_response_invalid_choice(self, response_handler, mock_ui, mock_commands, sample_user):
        """잘못된 선택지 입력"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 99]

        survey_data = {
            "title": "테스트 설문",
            "description": "설명",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "multiple_choice", "options": ["옵션1", "옵션2"]}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        response_handler.submit_response_flow(sample_user)

        mock_ui.print_warning.assert_called()


class TestResponseHandlerViewResults:
    """결과 조회 flow 테스트"""

    def test_view_results_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """결과 조회 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        results_data = {
            "results": [
                {
                    "question": "질문1",
                    "answer_distribution": {"답변1": 5, "답변2": 3}
                }
            ]
        }
        mock_commands.get_results.return_value = (True, None, results_data)

        response_handler.view_results_flow(sample_user)

        mock_ui.print_results_table.assert_called_once()

    def test_view_results_permission_denied(self, response_handler, mock_ui, mock_commands, sample_user):
        """결과 조회 권한 없음"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_commands.get_results.return_value = (False, "결과 조회 권한이 없습니다", None)

        response_handler.view_results_flow(sample_user)

        mock_ui.print_error.assert_called()
        assert "권한이 없습니다" in str(mock_ui.print_error.call_args)

    def test_view_results_no_survey(self, response_handler, mock_ui, mock_commands, sample_user):
        """설문이 없을 때 결과 조회 시도"""
        mock_commands.list_surveys.return_value = []

        response_handler.view_results_flow(sample_user)

        mock_ui.print_info.assert_called_once_with("설문이 없습니다")
        mock_commands.get_results.assert_not_called()


class TestResponseHandlerUpdateResponse:
    """응답 수정 flow 테스트"""

    def test_update_response_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 수정 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        mock_response = Response(
            id="resp123",
            survey_id="survey123",
            question_id="q1",
            answer="원래 답변",
            respondent_id=sample_user.id,
            created_at=datetime.now()
        )
        mock_commands.response_service.response_repository.find_by_question_id.return_value = [mock_response]

        mock_ui.get_input.return_value = "수정된 답변"
        mock_ui.confirm.return_value = True
        mock_commands.update_response.return_value = (True, None)

        response_handler.update_response_flow(sample_user)

        mock_commands.update_response.assert_called_once_with(sample_user, "resp123", "수정된 답변")
        mock_ui.print_success.assert_called_once()

    def test_update_response_no_responses(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답이 없을 때 수정 시도"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_commands.response_service.response_repository.find_by_question_id.return_value = []

        response_handler.update_response_flow(sample_user)

        mock_ui.print_info.assert_called_with("제출한 응답이 없습니다")
        mock_commands.update_response.assert_not_called()

    def test_update_response_cancelled(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 수정 취소"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        mock_response = Response(
            id="resp123",
            survey_id="survey123",
            question_id="q1",
            answer="원래 답변",
            respondent_id=sample_user.id,
            created_at=datetime.now()
        )
        mock_commands.response_service.response_repository.find_by_question_id.return_value = [mock_response]

        mock_ui.get_input.return_value = "수정된 답변"
        mock_ui.confirm.return_value = False

        response_handler.update_response_flow(sample_user)

        mock_commands.update_response.assert_not_called()


class TestResponseHandlerDeleteResponse:
    """응답 삭제 flow 테스트"""

    def test_delete_response_success(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 삭제 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        mock_response = Response(
            id="resp123",
            survey_id="survey123",
            question_id="q1",
            answer="삭제할 답변",
            respondent_id=sample_user.id,
            created_at=datetime.now()
        )
        mock_commands.response_service.response_repository.find_by_question_id.return_value = [mock_response]

        mock_ui.confirm.return_value = True
        mock_commands.delete_response.return_value = (True, None)

        response_handler.delete_response_flow(sample_user)

        mock_commands.delete_response.assert_called_once_with(sample_user, "resp123")
        mock_ui.print_success.assert_called_once()

    def test_delete_response_cancelled(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 삭제 취소"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        mock_response = Response(
            id="resp123",
            survey_id="survey123",
            question_id="q1",
            answer="삭제할 답변",
            respondent_id=sample_user.id,
            created_at=datetime.now()
        )
        mock_commands.response_service.response_repository.find_by_question_id.return_value = [mock_response]

        mock_ui.confirm.return_value = False

        response_handler.delete_response_flow(sample_user)

        mock_commands.delete_response.assert_not_called()

    def test_delete_response_failed(self, response_handler, mock_ui, mock_commands, sample_user):
        """응답 삭제 실패"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        mock_response = Response(
            id="resp123",
            survey_id="survey123",
            question_id="q1",
            answer="삭제할 답변",
            respondent_id=sample_user.id,
            created_at=datetime.now()
        )
        mock_commands.response_service.response_repository.find_by_question_id.return_value = [mock_response]

        mock_ui.confirm.return_value = True
        mock_commands.delete_response.return_value = (False, "응답 삭제 권한이 없습니다")

        response_handler.delete_response_flow(sample_user)

        mock_ui.print_error.assert_called()
        assert "권한이 없습니다" in str(mock_ui.print_error.call_args)
