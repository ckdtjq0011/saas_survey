"""권한 에스컬레이션 방지 시나리오 테스트

목적: 모든 권한 우회 시도 차단 확인
커버리지: auth_service.py +10%
"""

import pytest
from datetime import datetime, timedelta
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestPermissionEscalationPrevention:
    """권한 에스컬레이션 방지 엔드투엔드 테스트"""

    def test_respondent_cannot_delete_survey(
        self, auth_service, survey_service
    ):
        """RESPONDENT가 설문 삭제 시도 시 차단

        시나리오:
            1. SURVEY_MANAGER가 설문 생성
            2. RESPONDENT가 해당 설문 삭제 시도
            3. 권한 없음 에러 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        resp_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="respondent",
            email="resp@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        manager_login = auth_service.login("manager", "manager123", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        resp_login = auth_service.login("respondent", "resp123", tenant_id)
        resp_validate = auth_service.validate_session(resp_login.value)
        resp_user, _ = resp_validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        delete_result = survey_service.delete_survey(resp_user, survey_id)
        assert delete_result.is_failure()
        assert "권한" in delete_result.error

    def test_cross_tenant_data_access_blocked(
        self, auth_service, survey_service
    ):
        """크로스 테넌트 데이터 접근 차단

        시나리오:
            1. 테넌트 A와 B 생성
            2. 각 테넌트에서 관리자와 설문 생성
            3. 테넌트 A 관리자가 테넌트 B 설문 접근 시도
            4. 접근 차단 확인
        """
        tenant_a = auth_service.register_tenant("회사A")
        tenant_b = auth_service.register_tenant("회사B")

        manager_a_result = auth_service.register_user(
            tenant_id=tenant_a,
            username="manager_a",
            email="managera@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        manager_b_result = auth_service.register_user(
            tenant_id=tenant_b,
            username="manager_b",
            email="managerb@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        login_a = auth_service.login("manager_a", "password123", tenant_a)
        validate_a = auth_service.validate_session(login_a.value)
        user_a, _ = validate_a.value

        login_b = auth_service.login("manager_b", "password123", tenant_b)
        validate_b = auth_service.validate_session(login_b.value)
        user_b, _ = validate_b.value

        survey_b = survey_service.create_survey(user_b, "테넌트B 설문", "설명")
        survey_b_id = survey_b.value

        access_result = survey_service.update_survey(user_a, survey_b_id, title="접근 시도")
        assert access_result.is_failure()
        assert ("권한" in access_result.error or "테넌트" in access_result.error or "접근" in access_result.error)

    def test_logout_invalidates_session(
        self, auth_service, survey_service
    ):
        """로그아웃 후 세션 무효화 확인

        시나리오:
            1. 사용자 로그인
            2. 로그아웃
            3. 무효화된 세션으로 설문 생성 시도
            4. 세션 무효화 에러 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        login = auth_service.login("manager", "manager123", tenant_id)
        api_key = login.value

        validate_before = auth_service.validate_session(api_key)
        assert validate_before.is_success()

        logout = auth_service.logout(api_key)
        assert logout.is_success()

        validate_after = auth_service.validate_session(api_key)
        assert validate_after.is_failure()
        assert ("유효" in validate_after.error or "세션" in validate_after.error)

    def test_survey_manager_cannot_modify_others_survey(
        self, auth_service, survey_service
    ):
        """SURVEY_MANAGER가 타인 설문 수정 시도 시 차단

        시나리오:
            1. 두 명의 SURVEY_MANAGER 생성
            2. Manager A가 설문 생성
            3. Manager B가 수정 시도
            4. 권한 없음 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_a_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_a",
            email="managera@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        manager_b_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_b",
            email="managerb@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        login_a = auth_service.login("manager_a", "password123", tenant_id)
        validate_a = auth_service.validate_session(login_a.value)
        user_a, _ = validate_a.value

        login_b = auth_service.login("manager_b", "password123", tenant_id)
        validate_b = auth_service.validate_session(login_b.value)
        user_b, _ = validate_b.value

        survey_result = survey_service.create_survey(user_a, "A의 설문", "설명")
        survey_id = survey_result.value

        update_result = survey_service.update_survey(user_b, survey_id, title="B가 수정 시도")
        assert update_result.is_failure()
        assert "권한" in update_result.error

    def test_deleted_user_session_invalid(
        self, auth_service, survey_service
    ):
        """삭제된 사용자의 세션 무효화

        시나리오:
            1. 관리자와 일반 사용자 생성
            2. 일반 사용자 로그인
            3. 관리자가 일반 사용자 삭제
            4. 삭제된 사용자의 세션 무효화 확인
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
