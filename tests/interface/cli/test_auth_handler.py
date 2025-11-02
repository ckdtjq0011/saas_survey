import pytest
from unittest.mock import Mock, MagicMock, patch
from domain.entities.user import User
from domain.value_objects.role import Role
from interface.cli.handlers.auth_handler import AuthHandler
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
    ui.pause = Mock()
    ui.get_input = Mock()
    ui.get_validated_input = Mock()
    ui.get_choice = Mock()
    ui.get_int_input = Mock()
    ui.print_tenants_table = Mock()
    ui.confirm = Mock()
    return ui


@pytest.fixture
def auth_handler(mock_commands, mock_ui):
    """AuthHandler fixture"""
    return AuthHandler(mock_commands, mock_ui)


@pytest.fixture
def sample_user():
    """Sample user fixture"""
    return User(
        id="user123",
        tenant_id="tenant123",
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$dummy_hash",
        role=Role.TENANT_ADMIN,
        created_at=datetime.now(),
        is_active=True
    )


class TestAuthHandlerRegisterTenant:
    """테넌트 등록 flow 테스트"""

    def test_register_tenant_success(self, auth_handler, mock_ui, mock_commands):
        """테넌트 등록 성공

        시나리오:
            1. 사용자가 테넌트 이름 입력
            2. Commands.register_tenant 호출 성공
            3. 성공 메시지 출력
        """
        mock_ui.get_validated_input.return_value = "테스트 회사"
        mock_commands.register_tenant.return_value = "tenant123"

        auth_handler.register_tenant_flow()

        mock_ui.print_section.assert_called_once_with("테넌트 등록")
        mock_commands.register_tenant.assert_called_once_with("테스트 회사")
        mock_ui.print_success.assert_called_once()
        assert "tenant123" in str(mock_ui.print_success.call_args)
        mock_ui.pause.assert_called_once()

    def test_register_tenant_validation_error(self, auth_handler, mock_ui, mock_commands):
        """테넌트 등록 검증 실패

        시나리오:
            1. 사용자가 빈 이름 입력
            2. ValueError 발생
            3. 에러 메시지 출력
        """
        mock_ui.get_validated_input.side_effect = ValueError("테넌트 이름은 필수입니다")

        auth_handler.register_tenant_flow()

        mock_ui.print_error.assert_called_once_with("테넌트 이름은 필수입니다")
        mock_ui.pause.assert_called_once()

    def test_register_tenant_unexpected_error(self, auth_handler, mock_ui, mock_commands):
        """테넌트 등록 중 예외 발생

        시나리오:
            1. Commands.register_tenant에서 예외 발생
            2. 에러 핸들러 호출
            3. 에러 메시지 출력
        """
        mock_ui.get_validated_input.return_value = "테스트 회사"
        mock_commands.register_tenant.side_effect = Exception("DB 연결 실패")

        auth_handler.register_tenant_flow()

        mock_ui.print_error.assert_called()
        assert mock_ui.pause.call_count >= 1


class TestAuthHandlerRegisterUser:
    """사용자 등록 flow 테스트"""

    def test_register_user_success(self, auth_handler, mock_ui, mock_commands):
        """사용자 등록 성공

        시나리오:
            1. 테넌트 선택
            2. 사용자 정보 입력
            3. 사용자 등록 성공
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.side_effect = [
            "testuser",
            "test@example.com",
            "password123"
        ]
        mock_ui.get_choice.return_value = "tenant_admin"
        mock_commands.register_user.return_value = (True, "user123")

        auth_handler.register_user_flow()

        mock_commands.register_user.assert_called_once_with(
            "tenant123", "testuser", "test@example.com", "password123", "tenant_admin"
        )
        mock_ui.print_success.assert_called_once()
        assert "user123" in str(mock_ui.print_success.call_args)

    def test_register_user_no_tenant(self, auth_handler, mock_ui, mock_commands):
        """테넌트가 없을 때 사용자 등록 시도

        시나리오:
            1. 테넌트 목록 조회 시 빈 리스트
            2. 등록 프로세스 중단
        """
        mock_commands.list_tenants.return_value = []

        auth_handler.register_user_flow()

        mock_ui.print_info.assert_called_once_with("등록된 테넌트가 없습니다")
        mock_ui.pause.assert_called_once()
        mock_commands.register_user.assert_not_called()

    def test_register_user_failed(self, auth_handler, mock_ui, mock_commands):
        """사용자 등록 실패

        시나리오:
            1. 사용자 정보 입력
            2. 중복 사용자명으로 등록 실패
            3. 에러 메시지 출력
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.side_effect = [
            "testuser",
            "test@example.com",
            "password123"
        ]
        mock_ui.get_choice.return_value = "respondent"
        mock_commands.register_user.return_value = (False, "이미 존재하는 사용자명입니다")

        auth_handler.register_user_flow()

        mock_ui.print_error.assert_called()
        assert "이미 존재하는 사용자명입니다" in str(mock_ui.print_error.call_args)

    def test_register_user_validation_error(self, auth_handler, mock_ui, mock_commands):
        """사용자 등록 입력 검증 실패

        시나리오:
            1. 잘못된 이메일 형식 입력
            2. ValueError 발생
            3. 에러 메시지 출력
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_validated_input.side_effect = [
            "testuser",
            ValueError("유효한 이메일 형식이 아닙니다")
        ]

        auth_handler.register_user_flow()

        mock_ui.print_error.assert_called_with("유효한 이메일 형식이 아닙니다")


class TestAuthHandlerLogin:
    """로그인 flow 테스트"""

    def test_login_success(self, auth_handler, mock_ui, mock_commands, sample_user):
        """로그인 성공

        시나리오:
            1. 테넌트 선택
            2. 사용자명/비밀번호 입력
            3. 로그인 성공
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_input.side_effect = ["testuser", "password123"]
        mock_commands.login.return_value = (True, "api_key_123", sample_user)

        success, api_key, user = auth_handler.login_flow()

        assert success is True
        assert api_key == "api_key_123"
        assert user == sample_user
        mock_ui.print_success.assert_called_once()
        assert "testuser" in str(mock_ui.print_success.call_args)

    def test_login_wrong_credentials(self, auth_handler, mock_ui, mock_commands):
        """로그인 실패 - 잘못된 인증 정보

        시나리오:
            1. 사용자명/비밀번호 입력
            2. 잘못된 인증 정보로 로그인 실패
            3. 에러 메시지 출력
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_input.side_effect = ["testuser", "wrongpassword"]
        mock_commands.login.return_value = (False, "사용자명 또는 비밀번호가 올바르지 않습니다", None)

        success, api_key, user = auth_handler.login_flow()

        assert success is False
        assert api_key == ""
        assert user is None
        mock_ui.print_error.assert_called()

    def test_login_no_tenant(self, auth_handler, mock_ui, mock_commands):
        """로그인 시 테넌트 선택 취소

        시나리오:
            1. 테넌트 선택 취소
            2. 로그인 프로세스 중단
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 0

        success, api_key, user = auth_handler.login_flow()

        assert success is False
        mock_commands.login.assert_not_called()

    def test_login_exception(self, auth_handler, mock_ui, mock_commands):
        """로그인 중 예외 발생

        시나리오:
            1. Commands.login에서 예외 발생
            2. 에러 핸들러 호출
            3. False 반환
        """
        mock_commands.list_tenants.return_value = [
            {"id": "tenant123", "name": "테스트 회사"}
        ]
        mock_ui.get_int_input.return_value = 1
        mock_ui.get_input.side_effect = ["testuser", "password123"]
        mock_commands.login.side_effect = Exception("네트워크 오류")

        success, api_key, user = auth_handler.login_flow()

        assert success is False
        assert api_key == ""
        assert user is None
        mock_ui.print_error.assert_called()


class TestAuthHandlerLogout:
    """로그아웃 flow 테스트"""

    def test_logout_success(self, auth_handler, mock_ui, mock_commands):
        """로그아웃 성공

        시나리오:
            1. 로그아웃 확인
            2. Commands.logout 성공
            3. 성공 메시지 출력
        """
        mock_ui.confirm.return_value = True
        mock_commands.logout.return_value = True

        result = auth_handler.logout_flow("api_key_123")

        assert result is True
        mock_commands.logout.assert_called_once_with("api_key_123")
        mock_ui.print_success.assert_called_once_with("로그아웃되었습니다")

    def test_logout_cancelled(self, auth_handler, mock_ui, mock_commands):
        """로그아웃 취소

        시나리오:
            1. 사용자가 로그아웃 취소
            2. Commands.logout 호출 안 됨
        """
        mock_ui.confirm.return_value = False

        result = auth_handler.logout_flow("api_key_123")

        assert result is False
        mock_commands.logout.assert_not_called()

    def test_logout_failed(self, auth_handler, mock_ui, mock_commands):
        """로그아웃 실패

        시나리오:
            1. Commands.logout 실패
            2. 에러 메시지 출력
        """
        mock_ui.confirm.return_value = True
        mock_commands.logout.return_value = False

        result = auth_handler.logout_flow("api_key_123")

        assert result is False
        mock_ui.print_error.assert_called_with("로그아웃 실패")

    def test_logout_exception(self, auth_handler, mock_ui, mock_commands):
        """로그아웃 중 예외 발생

        시나리오:
            1. Commands.logout에서 예외 발생
            2. 에러 핸들러 호출
            3. False 반환
        """
        mock_ui.confirm.return_value = True
        mock_commands.logout.side_effect = Exception("네트워크 오류")

        result = auth_handler.logout_flow("api_key_123")

        assert result is False
        mock_ui.print_error.assert_called()
