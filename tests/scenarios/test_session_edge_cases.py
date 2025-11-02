"""세션 관리 엣지케이스 시나리오 테스트

목적: 세션 라이프사이클의 모든 엣지케이스 커버
커버리지: auth_service.py +8%
"""

import pytest
from datetime import datetime, timedelta
from domain.value_objects.role import Role


class TestSessionEdgeCases:
    """세션 관리 엣지케이스 엔드투엔드 테스트"""

    def test_session_validation_after_logout(
        self, auth_service, session_repo
    ):
        """로그아웃 후 세션 검증 실패

        시나리오:
            1. 사용자 로그인
            2. 세션 검증 성공
            3. 로그아웃
            4. 세션 검증 실패
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        login = auth_service.login("user", "password123", tenant_id)
        api_key = login.value

        validate_before = auth_service.validate_session(api_key)
        assert validate_before.is_success()

        logout = auth_service.logout(api_key)
        assert logout.is_success()

        validate_after = auth_service.validate_session(api_key)
        assert validate_after.is_failure()

    def test_logout_then_immediate_re_login(
        self, auth_service
    ):
        """로그아웃 후 즉시 재로그인

        시나리오:
            1. 사용자 로그인
            2. 로그아웃
            3. 즉시 재로그인
            4. 새 세션으로 작업 가능
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        login1 = auth_service.login("user", "password123", tenant_id)
        api_key1 = login1.value

        validate1 = auth_service.validate_session(api_key1)
        assert validate1.is_success()

        logout = auth_service.logout(api_key1)
        assert logout.is_success()

        login2 = auth_service.login("user", "password123", tenant_id)
        api_key2 = login2.value

        validate2 = auth_service.validate_session(api_key2)
        assert validate2.is_success()

        assert api_key1 != api_key2

    def test_sequential_re_login_creates_new_sessions(
        self, auth_service
    ):
        """순차적 재로그인으로 새 세션 생성

        시나리오:
            1. 사용자 로그인 (세션 1)
            2. 동일 사용자 재로그인 (세션 2)
            3. 두 API 키가 다름 확인
            4. 두 번째 세션 검증 성공
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        login1 = auth_service.login("user", "password123", tenant_id)
        api_key1 = login1.value

        login2 = auth_service.login("user", "password123", tenant_id)
        api_key2 = login2.value

        assert api_key1 != api_key2

        validate2 = auth_service.validate_session(api_key2)
        assert validate2.is_success()

    def test_session_during_user_deletion(
        self, auth_service
    ):
        """세션 중 사용자 삭제

        시나리오:
            1. 사용자 로그인
            2. 관리자가 해당 사용자 삭제
            3. 기존 세션으로 검증 시도
            4. 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        admin_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=Role.TENANT_ADMIN
        )

        user_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="user123",
            role=Role.RESPONDENT
        )
        user_id = user_result.value

        admin_login = auth_service.login("admin", "admin123", tenant_id)
        admin_validate = auth_service.validate_session(admin_login.value)
        admin_user, _ = admin_validate.value

        user_login = auth_service.login("user", "user123", tenant_id)
        user_api_key = user_login.value

        validate_before = auth_service.validate_session(user_api_key)
        assert validate_before.is_success()

        delete_result = auth_service.delete_user(admin_user, user_id)
        assert delete_result.is_success()

        validate_after = auth_service.validate_session(user_api_key)
        assert validate_after.is_failure()

    def test_invalid_api_key_validation_fails(
        self, auth_service
    ):
        """잘못된 API 키로 세션 검증 실패

        시나리오:
            1. 존재하지 않는 API 키로 세션 검증 시도
            2. 검증 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        fake_api_key = "invalid_api_key_12345678901234567890"

        validate = auth_service.validate_session(fake_api_key)
        assert validate.is_failure()
        assert ("유효" in validate.error or "API" in validate.error)
