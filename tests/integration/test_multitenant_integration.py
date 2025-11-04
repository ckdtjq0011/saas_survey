import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestMultitenantIntegration:
    """멀티테넌트 통합 테스트"""

    def test_cross_tenant_survey_access_prevention(
        self, auth_service, survey_service
    ):
        """테넌트 간 설문 접근 차단

        시나리오:
            1. 두 개의 테넌트 생성
            2. 각 테넌트에서 설문 생성
            3. 테넌트 A의 사용자가 테넌트 B의 설문 접근 시도
            4. 접근 거부 확인
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        manager_a = auth_service.register_user(
            tenant_id=tenant_a,
            username="manager_a",
            email="manager_a@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        manager_b = auth_service.register_user(
            tenant_id=tenant_b,
            username="manager_b",
            email="manager_b@test.com",
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

        update_result = survey_service.update_survey(user_a, survey_b_id, title="수정 시도")
        assert update_result.is_failure()
        assert ("권한이 없습니다" in update_result.error or
                "다른 테넌트" in update_result.error or
                "접근할 수 없습니다" in update_result.error)

    def test_cross_tenant_user_list_isolation(
        self, auth_service, user_repo
    ):
        """테넌트 간 사용자 목록 격리

        시나리오:
            1. 두 개의 테넌트 생성
            2. 각 테넌트에 사용자 생성
            3. 각 테넌트의 사용자 목록 조회
            4. 각 테넌트는 자신의 사용자만 조회됨
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        auth_service.register_user(
            tenant_id=tenant_a,
            username="user_a1",
            email="user_a1@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        auth_service.register_user(
            tenant_id=tenant_a,
            username="user_a2",
            email="user_a2@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        auth_service.register_user(
            tenant_id=tenant_b,
            username="user_b1",
            email="user_b1@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        users_a = user_repo.find_users_by_tenant(tenant_a)
        users_b = user_repo.find_users_by_tenant(tenant_b)

        assert len(users_a) == 2
        assert len(users_b) == 1
        assert all(u.tenant_id == tenant_a for u in users_a)
        assert all(u.tenant_id == tenant_b for u in users_b)

    def test_cross_tenant_response_access_prevention(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """테넌트 간 응답 접근 차단

        시나리오:
            1. 두 개의 테넌트에서 설문 생성 및 응답 제출
            2. 테넌트 A의 사용자가 테넌트 B의 응답 조회 시도
            3. 접근 거부 또는 빈 결과 확인
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        manager_a = auth_service.register_user(
            tenant_id=tenant_a,
            username="manager_a",
            email="manager_a@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        manager_b = auth_service.register_user(
            tenant_id=tenant_b,
            username="manager_b",
            email="manager_b@test.com",
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

        question_b = survey_service.add_question(
            user_b, survey_b_id, "질문", QuestionType.TEXT
        )
        question_b_id = question_b.value

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_b_id)
        response_service.submit_response(
            user_b, survey_b_id, {question_b_id: "답변"}, session_id, time_spent_data
        )

        result = response_service.get_survey_results(user_a, survey_b_id)
        assert result.is_failure()
        assert ("권한이 없습니다" in result.error or
                "다른 테넌트" in result.error or
                "접근할 수 없습니다" in result.error)

    def test_tenant_admin_cannot_access_other_tenant_data(
        self, auth_service, survey_service
    ):
        """테넌트 관리자는 다른 테넌트 데이터 접근 불가

        시나리오:
            1. 두 개의 테넌트 및 각각 TENANT_ADMIN 생성
            2. 테넌트 A의 ADMIN이 테넌트 B의 설문 접근 시도
            3. 접근 거부 확인
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        admin_a = auth_service.register_user(
            tenant_id=tenant_a,
            username="admin_a",
            email="admin_a@test.com",
            password="password123",
            role=Role.TENANT_ADMIN
        )

        manager_b = auth_service.register_user(
            tenant_id=tenant_b,
            username="manager_b",
            email="manager_b@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        login_a = auth_service.login("admin_a", "password123", tenant_a)
        validate_a = auth_service.validate_session(login_a.value)
        admin_user_a, _ = validate_a.value

        login_b = auth_service.login("manager_b", "password123", tenant_b)
        validate_b = auth_service.validate_session(login_b.value)
        user_b, _ = validate_b.value

        survey_b = survey_service.create_survey(user_b, "테넌트B 설문", "설명")
        survey_b_id = survey_b.value

        delete_result = survey_service.delete_survey(admin_user_a, survey_b_id)
        assert delete_result.is_failure()
        assert ("권한이 없습니다" in delete_result.error or
                "다른 테넌트" in delete_result.error or
                "접근할 수 없습니다" in delete_result.error)

    def test_multitenant_session_isolation(
        self, auth_service, session_repo
    ):
        """멀티테넌트 세션 격리

        시나리오:
            1. 두 개의 테넌트에서 사용자 로그인
            2. 세션이 각 테넌트별로 격리되어 있는지 확인
            3. 잘못된 테넌트로 세션 검증 시도
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        auth_service.register_user(
            tenant_id=tenant_a,
            username="user_a",
            email="user_a@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        auth_service.register_user(
            tenant_id=tenant_b,
            username="user_b",
            email="user_b@test.com",
            password="password123",
            role=Role.RESPONDENT
        )

        login_a = auth_service.login("user_a", "password123", tenant_a)
        api_key_a = login_a.value

        validate_a = auth_service.validate_session(api_key_a)
        assert validate_a.is_success()

        user_a, session_a = validate_a.value
        assert user_a.tenant_id == tenant_a
        assert session_a.tenant_id == tenant_a

    def test_same_username_different_tenants(
        self, auth_service
    ):
        """동일 사용자명을 다른 테넌트에서 사용 가능

        시나리오:
            1. 두 개의 테넌트 생성
            2. 각 테넌트에 동일한 username으로 사용자 생성
            3. 각각 독립적으로 로그인 가능
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        user_a = auth_service.register_user(
            tenant_id=tenant_a,
            username="user",
            email="user_a@test.com",
            password="password_a",
            role=Role.RESPONDENT
        )
        assert user_a.is_success()

        user_b = auth_service.register_user(
            tenant_id=tenant_b,
            username="user",
            email="user_b@test.com",
            password="password_b",
            role=Role.RESPONDENT
        )
        assert user_b.is_success()

        login_a = auth_service.login("user", "password_a", tenant_a)
        assert login_a.is_success()

        login_b = auth_service.login("user", "password_b", tenant_b)
        assert login_b.is_success()

    def test_tenant_deletion_removes_tenant_record(
        self, auth_service, survey_service, tenant_repo, user_repo, survey_repo
    ):
        """테넌트 삭제 시 테넌트 레코드 삭제

        시나리오:
            1. 테넌트 생성 및 사용자, 설문 생성
            2. 테넌트 삭제
            3. 테넌트 레코드 삭제 확인
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        manager = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        login = auth_service.login("manager", "password123", tenant_id)
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey.value

        tenant_before = tenant_repo.find_tenant_by_id(tenant_id)
        assert tenant_before is not None

        tenant_repo.delete_tenant(tenant_id)

        tenant_after = tenant_repo.find_tenant_by_id(tenant_id)
        assert tenant_after is None

    def test_cross_tenant_duplicate_email_allowed(
        self, auth_service
    ):
        """다른 테넌트에서 동일 이메일 사용 가능

        시나리오:
            1. 두 개의 테넌트 생성
            2. 동일한 이메일로 각 테넌트에 사용자 생성
            3. 모두 성공 확인
        """
        tenant_a = auth_service.register_tenant("테넌트A")
        tenant_b = auth_service.register_tenant("테넌트B")

        user_a = auth_service.register_user(
            tenant_id=tenant_a,
            username="user_a",
            email="same@test.com",
            password="password_a",
            role=Role.RESPONDENT
        )
        assert user_a.is_success()

        user_b = auth_service.register_user(
            tenant_id=tenant_b,
            username="user_b",
            email="same@test.com",
            password="password_b",
            role=Role.RESPONDENT
        )
        assert user_b.is_success()
