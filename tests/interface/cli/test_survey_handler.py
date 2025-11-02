import pytest
from unittest.mock import Mock
from domain.entities.user import User
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from interface.cli.handlers.survey_handler import SurveyHandler
from interface.cli.commands import Commands
from interface.cli.ui_helper import ConsoleUI
from datetime import datetime


@pytest.fixture
def mock_commands():
    """Mock Commands fixture"""
    return Mock(spec=Commands)


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
    ui.get_choice = Mock()
    ui.get_int_input = Mock()
    ui.print_surveys_table = Mock()
    ui.print_questions_tree = Mock()
    ui.confirm = Mock()
    return ui


@pytest.fixture
def survey_handler(mock_commands, mock_ui):
    """SurveyHandler fixture"""
    return SurveyHandler(mock_commands, mock_ui)


@pytest.fixture
def sample_user():
    """Sample user fixture"""
    return User(
        id="user123",
        tenant_id="tenant123",
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.SURVEY_MANAGER,
        created_at=datetime.now(),
        is_active=True
    )


class TestSurveyHandlerCreateSurvey:
    """설문 생성 flow 테스트"""

    def test_create_survey_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 생성 성공"""
        mock_ui.get_validated_input.return_value = "테스트 설문"
        mock_ui.get_input.return_value = "설문 설명"
        mock_commands.create_survey.return_value = (True, "survey123")

        survey_handler.create_survey_flow(sample_user)

        mock_commands.create_survey.assert_called_once_with(sample_user, "테스트 설문", "설문 설명")
        mock_ui.print_success.assert_called_once()
        assert "survey123" in str(mock_ui.print_success.call_args)

    def test_create_survey_validation_error(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 생성 검증 실패"""
        mock_ui.get_validated_input.side_effect = ValueError("설문 제목은 3자 이상이어야 합니다")

        survey_handler.create_survey_flow(sample_user)

        mock_ui.print_error.assert_called_with("설문 제목은 3자 이상이어야 합니다")
        mock_commands.create_survey.assert_not_called()

    def test_create_survey_permission_denied(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 생성 권한 없음"""
        mock_ui.get_validated_input.return_value = "테스트 설문"
        mock_ui.get_input.return_value = "설문 설명"
        mock_commands.create_survey.return_value = (False, "설문 생성 권한이 없습니다")

        survey_handler.create_survey_flow(sample_user)

        mock_ui.print_error.assert_called()
        assert "권한이 없습니다" in str(mock_ui.print_error.call_args)


class TestSurveyHandlerAddQuestion:
    """질문 추가 flow 테스트"""

    def test_add_text_question_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """TEXT 질문 추가 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.return_value = "질문 내용"
        mock_ui.get_choice.return_value = QuestionType.TEXT.value
        mock_commands.add_question.return_value = (True, "question123")

        survey_handler.add_question_flow(sample_user)

        mock_commands.add_question.assert_called_once_with(
            sample_user, "survey123", "질문 내용", QuestionType.TEXT.value, None
        )
        mock_ui.print_success.assert_called_once()

    def test_add_multiple_choice_question_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """MULTIPLE_CHOICE 질문 추가 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.return_value = "질문 내용"
        mock_ui.get_choice.return_value = QuestionType.MULTIPLE_CHOICE.value
        mock_ui.get_input.side_effect = ["옵션1", "옵션2", ""]
        mock_commands.add_question.return_value = (True, "question123")

        survey_handler.add_question_flow(sample_user)

        assert mock_commands.add_question.call_args[0][4] == ["옵션1", "옵션2"]
        mock_ui.print_success.assert_called_once()

    def test_add_question_no_survey(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문이 없을 때 질문 추가 시도"""
        mock_commands.list_surveys.return_value = []

        survey_handler.add_question_flow(sample_user)

        mock_ui.print_info.assert_called_once_with("설문이 없습니다")
        mock_commands.add_question.assert_not_called()

    def test_add_question_failed(self, survey_handler, mock_ui, mock_commands, sample_user):
        """질문 추가 실패"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.return_value = "질문 내용"
        mock_ui.get_choice.return_value = QuestionType.TEXT.value
        mock_commands.add_question.return_value = (False, "설문을 찾을 수 없습니다")

        survey_handler.add_question_flow(sample_user)

        mock_ui.print_error.assert_called()
        assert "설문을 찾을 수 없습니다" in str(mock_ui.print_error.call_args)


class TestSurveyHandlerListSurveys:
    """설문 목록 조회 flow 테스트"""

    def test_list_surveys_with_data(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 목록 조회 성공"""
        surveys = [
            {"id": "survey1", "title": "설문1"},
            {"id": "survey2", "title": "설문2"}
        ]
        mock_commands.list_surveys.return_value = surveys

        survey_handler.list_surveys_flow(sample_user)

        mock_commands.list_surveys.assert_called_once_with(sample_user)
        mock_ui.print_surveys_table.assert_called_once_with(surveys)

    def test_list_surveys_empty(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문이 없을 때 목록 조회"""
        mock_commands.list_surveys.return_value = []

        survey_handler.list_surveys_flow(sample_user)

        mock_ui.print_info.assert_called_once_with("설문이 없습니다")

    def test_list_surveys_exception(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 목록 조회 중 예외 발생"""
        mock_commands.list_surveys.side_effect = Exception("DB 오류")

        survey_handler.list_surveys_flow(sample_user)

        mock_ui.print_error.assert_called()


class TestSurveyHandlerViewSurvey:
    """설문 상세 조회 flow 테스트"""

    def test_view_survey_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 상세 조회 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"text": "질문1", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)

        survey_handler.view_survey_flow(sample_user)

        mock_ui.print_questions_tree.assert_called_once()

    def test_view_survey_not_found(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 조회 실패"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_commands.get_survey.return_value = (False, "설문을 찾을 수 없습니다", None)

        survey_handler.view_survey_flow(sample_user)

        mock_ui.print_error.assert_called()


class TestSurveyHandlerUpdateSurvey:
    """설문 수정 flow 테스트"""

    def test_update_survey_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 수정 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "원래 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {
            "title": "원래 설문",
            "description": "원래 설명",
            "questions": []
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.get_validated_input.return_value = "수정된 설문"
        mock_ui.get_input.return_value = "수정된 설명"
        mock_ui.confirm.return_value = True
        mock_commands.update_survey.return_value = (True, None)

        survey_handler.update_survey_flow(sample_user)

        mock_commands.update_survey.assert_called_once_with(
            sample_user, "survey123", "수정된 설문", "수정된 설명"
        )
        mock_ui.print_success.assert_called_once()

    def test_update_survey_cancelled(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 수정 취소"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "원래 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {"title": "원래 설문", "description": "원래 설명", "questions": []}
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.get_validated_input.return_value = "수정된 설문"
        mock_ui.get_input.return_value = "수정된 설명"
        mock_ui.confirm.return_value = False

        survey_handler.update_survey_flow(sample_user)

        mock_commands.update_survey.assert_not_called()


class TestSurveyHandlerDeleteSurvey:
    """설문 삭제 flow 테스트"""

    def test_delete_survey_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 삭제 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "삭제할 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {"title": "삭제할 설문", "questions": []}
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = True
        mock_commands.delete_survey.return_value = (True, None)

        survey_handler.delete_survey_flow(sample_user)

        mock_commands.delete_survey.assert_called_once_with(sample_user, "survey123")
        mock_ui.print_success.assert_called_once()

    def test_delete_survey_cancelled(self, survey_handler, mock_ui, mock_commands, sample_user):
        """설문 삭제 취소"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "삭제할 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {"title": "삭제할 설문", "questions": []}
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = False

        survey_handler.delete_survey_flow(sample_user)

        mock_commands.delete_survey.assert_not_called()


class TestSurveyHandlerQuestionOperations:
    """질문 수정/삭제 flow 테스트"""

    def test_update_question_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """질문 수정 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "원래 질문", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.get_validated_input.return_value = "수정된 질문"
        mock_ui.confirm.return_value = True
        mock_commands.update_question.return_value = (True, None)

        survey_handler.update_question_flow(sample_user)

        mock_commands.update_question.assert_called_once()
        mock_ui.print_success.assert_called_once()

    def test_delete_question_success(self, survey_handler, mock_ui, mock_commands, sample_user):
        """질문 삭제 성공"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.side_effect = [1, 1]

        survey_data = {
            "title": "테스트 설문",
            "questions": [
                {"id": "q1", "text": "삭제할 질문", "type": "text", "options": None}
            ]
        }
        mock_commands.get_survey.return_value = (True, None, survey_data)
        mock_ui.confirm.return_value = True
        mock_commands.delete_question.return_value = (True, None)

        survey_handler.delete_question_flow(sample_user)

        mock_commands.delete_question.assert_called_once_with(sample_user, "q1")
        mock_ui.print_success.assert_called_once()

    def test_update_question_no_questions(self, survey_handler, mock_ui, mock_commands, sample_user):
        """질문이 없을 때 수정 시도"""
        mock_commands.list_surveys.return_value = [
            {"id": "survey123", "title": "테스트 설문"}
        ]
        mock_ui.get_int_input.return_value = 1

        survey_data = {"title": "테스트 설문", "questions": []}
        mock_commands.get_survey.return_value = (True, None, survey_data)

        survey_handler.update_question_flow(sample_user)

        mock_ui.print_info.assert_called_with("질문이 없습니다")
        mock_commands.update_question.assert_not_called()
