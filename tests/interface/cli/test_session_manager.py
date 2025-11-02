import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock
from interface.cli.session_manager import SessionManager
from domain.entities.user import User
from domain.entities.session import Session
from domain.value_objects.role import Role


@pytest.fixture
def temp_session_file(tmp_path):
    """임시 세션 파일 경로"""
    return tmp_path / "test_session"


@pytest.fixture
def session_manager(temp_session_file):
    """SessionManager 픽스처"""
    return SessionManager(session_file=temp_session_file)


@pytest.fixture
def sample_user():
    """샘플 사용자"""
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


@pytest.fixture
def sample_session():
    """샘플 세션"""
    return Session(
        id="session123",
        user_id="user123",
        tenant_id="tenant123",
        api_key="api_key_123",
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1)
    )


class TestSessionManagerSaveSession:
    """save_session 테스트"""

    def test_save_session_creates_file(self, session_manager, sample_user, sample_session, temp_session_file):
        """세션 파일 생성 확인

        시나리오:
            1. save_session 호출
            2. 파일이 생성되었는지 확인
        """
        session_manager.save_session("api_key_123", sample_user, sample_session)

        assert temp_session_file.exists()

    def test_save_session_saves_correct_data(self, session_manager, sample_user, sample_session, temp_session_file):
        """세션 데이터 저장 확인

        시나리오:
            1. save_session 호출
            2. 파일 내용 확인
        """
        session_manager.save_session("api_key_123", sample_user, sample_session)

        with open(temp_session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["api_key"] == "api_key_123"
        assert data["user_id"] == "user123"
        assert data["tenant_id"] == "tenant123"
        assert data["username"] == "testuser"
        assert data["role"] == Role.RESPONDENT.value
        assert "expires_at" in data


class TestSessionManagerLoadSession:
    """load_session 테스트"""

    def test_load_session_returns_none_if_file_not_exists(self, session_manager):
        """파일이 없을 때 None 반환

        시나리오:
            1. 세션 파일이 없는 상태
            2. load_session 호출
            3. None 반환 확인
        """
        result = session_manager.load_session()
        assert result is None

    def test_load_session_returns_data_if_valid(self, session_manager, sample_user, sample_session, temp_session_file):
        """유효한 세션 데이터 로드

        시나리오:
            1. save_session으로 세션 저장
            2. load_session으로 로드
            3. 데이터 일치 확인
        """
        session_manager.save_session("api_key_123", sample_user, sample_session)

        result = session_manager.load_session()

        assert result is not None
        assert result["api_key"] == "api_key_123"
        assert result["username"] == "testuser"

    def test_load_session_returns_none_if_expired(self, session_manager, sample_user, temp_session_file):
        """만료된 세션 로드 시 None 반환

        시나리오:
            1. 만료된 세션 저장
            2. load_session 호출
            3. None 반환 및 파일 삭제 확인
        """
        expired_session = Session(
            id="session123",
            user_id="user123",
            tenant_id="tenant123",
            api_key="api_key_123",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)
        )

        session_manager.save_session("api_key_123", sample_user, expired_session)

        result = session_manager.load_session()

        assert result is None
        assert not temp_session_file.exists()

    def test_load_session_handles_json_decode_error(self, session_manager, temp_session_file):
        """JSON 디코드 에러 처리

        시나리오:
            1. 잘못된 JSON 파일 생성
            2. load_session 호출
            3. None 반환 및 파일 삭제 확인
        """
        with open(temp_session_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        result = session_manager.load_session()

        assert result is None
        assert not temp_session_file.exists()

    def test_load_session_handles_missing_key(self, session_manager, temp_session_file):
        """필수 키 누락 처리

        시나리오:
            1. 필수 키가 누락된 JSON 파일 생성
            2. load_session 호출
            3. None 반환 및 파일 삭제 확인
        """
        with open(temp_session_file, "w", encoding="utf-8") as f:
            json.dump({"api_key": "test"}, f)

        result = session_manager.load_session()

        assert result is None
        assert not temp_session_file.exists()


class TestSessionManagerClearSession:
    """clear_session 테스트"""

    def test_clear_session_deletes_file(self, session_manager, sample_user, sample_session, temp_session_file):
        """세션 파일 삭제 확인

        시나리오:
            1. 세션 저장
            2. clear_session 호출
            3. 파일 삭제 확인
        """
        session_manager.save_session("api_key_123", sample_user, sample_session)
        assert temp_session_file.exists()

        session_manager.clear_session()

        assert not temp_session_file.exists()

    def test_clear_session_no_error_if_file_not_exists(self, session_manager):
        """파일이 없어도 에러 없음

        시나리오:
            1. 세션 파일이 없는 상태
            2. clear_session 호출
            3. 에러 발생하지 않음
        """
        session_manager.clear_session()


class TestSessionManagerIsLoggedIn:
    """is_logged_in 테스트"""

    def test_is_logged_in_returns_true_if_session_exists(self, session_manager, sample_user, sample_session):
        """세션이 있으면 True 반환

        시나리오:
            1. 세션 저장
            2. is_logged_in 호출
            3. True 반환 확인
        """
        session_manager.save_session("api_key_123", sample_user, sample_session)

        assert session_manager.is_logged_in() is True

    def test_is_logged_in_returns_false_if_no_session(self, session_manager):
        """세션이 없으면 False 반환

        시나리오:
            1. 세션 파일 없음
            2. is_logged_in 호출
            3. False 반환 확인
        """
        assert session_manager.is_logged_in() is False
