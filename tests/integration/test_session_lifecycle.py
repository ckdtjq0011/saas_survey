import pytest
from dataclasses import replace
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestSessionLifecycle:
    """세션 라이프사이클 통합 테스트"""

    def test_login_logout_login_workflow(
        self, auth_service, session_repo
    ):
        """로그인-로그아웃-재로그인 흐름

        시나리오:
            1. 사용자 로그인
            2. 세션 검증 성공
            3. 로그아웃
            4. 세션 검증 실패
            5. 재로그인
            6. 새 세션 검증 성공
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

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

        validate_after_logout = auth_service.validate_session(api_key1)
        assert validate_after_logout.is_failure()

        login2 = auth_service.login("user", "password123", tenant_id)
        api_key2 = login2.value

        validate2 = auth_service.validate_session(api_key2)
        assert validate2.is_success()

        assert api_key1 != api_key2

    def test_re_login_creates_new_session(
        self, auth_service
    ):
        """재로그인 시 새 세션 생성

        시나리오:
            1. 사용자 로그인 (세션1)
            2. 동일 사용자 재로그인 (세션2)
            3. 두 API 키가 다름
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

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

        assert login1.is_success()
        assert login2.is_success()
        assert api_key1 != api_key2

    def test_session_remains_valid_after_operations(
        self, auth_service
    ):
        """여러 작업 후에도 세션 유지

        시나리오:
            1. 사용자 로그인
            2. 세션 검증 (1차)
            3. 세션 검증 (2차)
            4. 모든 검증 성공
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        login = auth_service.login("user", "password123", tenant_id)
        api_key = login.value

        validate1 = auth_service.validate_session(api_key)
        assert validate1.is_success()

        validate2 = auth_service.validate_session(api_key)
        assert validate2.is_success()

        user1, session1 = validate1.value
        user2, session2 = validate2.value

        assert user1.id == user2.id
        assert session1.id == session2.id

    def test_session_invalidated_after_user_deletion(
        self, auth_service
    ):
        """사용자 삭제 후 세션 무효화

        시나리오:
            1. TENANT_ADMIN과 일반 사용자 생성
            2. 일반 사용자 로그인
            3. TENANT_ADMIN이 일반 사용자 삭제
            4. 세션 검증 실패
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

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

    def test_logout_clears_session_data(
        self, auth_service
    ):
        """로그아웃 시 세션 데이터 삭제

        시나리오:
            1. 사용자 로그인
            2. 로그아웃
            3. 해당 API 키로 세션 검증 실패
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

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

    def test_session_persists_across_operations(
        self, auth_service, survey_service
    ):
        """세션이 여러 작업 동안 유지됨

        시나리오:
            1. SURVEY_MANAGER 로그인
            2. 세션으로 설문 생성
            3. 세션으로 질문 추가
            4. 세션으로 설문 수정
            5. 모든 작업이 동일 세션으로 성공
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        login = auth_service.login("manager", "password123", tenant_id)
        api_key = login.value

        validate1 = auth_service.validate_session(api_key)
        assert validate1.is_success()
        user, _ = validate1.value

        survey_result = survey_service.create_survey(user, "설문1", "설명1")
        assert survey_result.is_success()
        survey_id = survey_result.value

        validate2 = auth_service.validate_session(api_key)
        assert validate2.is_success()
        user, _ = validate2.value

        question_result = survey_service.add_question(
            user, survey_id, "질문1", QuestionType.TEXT
        )
        assert question_result.is_success()

        validate3 = auth_service.validate_session(api_key)
        assert validate3.is_success()
        user, _ = validate3.value

        update_result = survey_service.update_survey(user, survey_id, title="수정된 설문")
        assert update_result.is_success()
