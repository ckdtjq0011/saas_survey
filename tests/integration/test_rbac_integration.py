import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestRBACIntegration:
    """RBAC 통합 테스트"""

    def test_tenant_admin_can_manage_all_surveys_in_tenant(self, auth_service, survey_service):
        """TENANT_ADMIN은 테넌트 내 모든 설문 관리 가능

        시나리오:
            1. 테넌트 생성
            2. TENANT_ADMIN과 SURVEY_MANAGER 생성
            3. SURVEY_MANAGER가 설문 생성
            4. TENANT_ADMIN이 다른 사용자의 설문 수정/삭제 가능
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        admin_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=Role.TENANT_ADMIN
        )
        admin_id = admin_result.value

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )
        manager_id = manager_result.value

        admin_login = auth_service.login("admin", "admin123", tenant_id)
        admin_validate = auth_service.validate_session(admin_login.value)
        admin_user, _ = admin_validate.value

        manager_login = auth_service.login("manager", "manager123", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(manager_user, "매니저 설문", "설명")
        assert survey_result.is_success()
        survey_id = survey_result.value

        update_result = survey_service.update_survey(admin_user, survey_id, title="어드민이 수정")
        assert update_result.is_success()

        delete_result = survey_service.delete_survey(admin_user, survey_id)
        assert delete_result.is_success()

    def test_survey_manager_cannot_manage_others_surveys(self, auth_service, survey_service):
        """SURVEY_MANAGER는 다른 사용자의 설문 관리 불가

        시나리오:
            1. 두 명의 SURVEY_MANAGER 생성
            2. Manager A가 설문 생성
            3. Manager B가 Manager A의 설문 수정/삭제 시도
            4. 모두 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_a_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_a",
            email="manager_a@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        manager_b_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_b",
            email="manager_b@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        login_a = auth_service.login("manager_a", "manager123", tenant_id)
        validate_a = auth_service.validate_session(login_a.value)
        manager_a_user, _ = validate_a.value

        login_b = auth_service.login("manager_b", "manager123", tenant_id)
        validate_b = auth_service.validate_session(login_b.value)
        manager_b_user, _ = validate_b.value

        survey_result = survey_service.create_survey(manager_a_user, "A의 설문", "설명")
        survey_id = survey_result.value

        update_result = survey_service.update_survey(manager_b_user, survey_id, title="B가 수정 시도")
        assert update_result.is_failure()
        assert "권한이 없습니다" in update_result.error

        delete_result = survey_service.delete_survey(manager_b_user, survey_id)
        assert delete_result.is_failure()
        assert "권한이 없습니다" in delete_result.error

    def test_respondent_cannot_create_survey(self, auth_service, survey_service):
        """RESPONDENT는 설문 생성 불가

        시나리오:
            1. RESPONDENT 생성
            2. 설문 생성 시도
            3. 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        respondent_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="respondent",
            email="respondent@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        login = auth_service.login("respondent", "resp123", tenant_id)
        validate = auth_service.validate_session(login.value)
        respondent_user, _ = validate.value

        survey_result = survey_service.create_survey(respondent_user, "응답자 설문", "설명")
        assert survey_result.is_failure()
        assert "권한이 없습니다" in survey_result.error

    def test_respondent_can_submit_and_modify_own_response(
        self, auth_service, survey_service, response_service, survey_repo
    ):
        """RESPONDENT는 자신의 응답 제출 및 수정 가능

        시나리오:
            1. SURVEY_MANAGER가 설문 생성
            2. RESPONDENT가 응답 제출
            3. RESPONDENT가 자신의 응답 수정
            4. 성공 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        respondent_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="respondent",
            email="respondent@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        manager_login = auth_service.login("manager", "manager123", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        respondent_login = auth_service.login("respondent", "resp123", tenant_id)
        respondent_validate = auth_service.validate_session(respondent_login.value)
        respondent_user, _ = respondent_validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit_result = response_service.submit_response(
            respondent_user, survey_id, {question_id: "원래 답변"}
        )
        assert submit_result.is_success()

        responses = response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        update_result = response_service.update_response(
            respondent_user, response_id, "수정된 답변"
        )
        assert update_result.is_success()

    def test_respondent_cannot_modify_others_response(
        self, auth_service, survey_service, response_service
    ):
        """RESPONDENT는 다른 사용자의 응답 수정 불가

        시나리오:
            1. 두 명의 RESPONDENT 생성
            2. Respondent A가 응답 제출
            3. Respondent B가 A의 응답 수정 시도
            4. 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        resp_a_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="resp_a",
            email="resp_a@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        resp_b_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="resp_b",
            email="resp_b@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        manager_login = auth_service.login("manager", "manager123", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        resp_a_login = auth_service.login("resp_a", "resp123", tenant_id)
        resp_a_validate = auth_service.validate_session(resp_a_login.value)
        resp_a_user, _ = resp_a_validate.value

        resp_b_login = auth_service.login("resp_b", "resp123", tenant_id)
        resp_b_validate = auth_service.validate_session(resp_b_login.value)
        resp_b_user, _ = resp_b_validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit_result = response_service.submit_response(
            resp_a_user, survey_id, {question_id: "A의 답변"}
        )
        assert submit_result.is_success()

        responses = response_service.response_repository.find_by_question_id(question_id)
        response_id = responses[0].id

        update_result = response_service.update_response(
            resp_b_user, response_id, "B가 수정 시도"
        )
        assert update_result.is_failure()
        assert "권한이 없습니다" in update_result.error

    def test_survey_owner_can_view_results(
        self, auth_service, survey_service, response_service
    ):
        """설문 소유자는 결과 조회 가능

        시나리오:
            1. SURVEY_MANAGER가 설문 생성
            2. RESPONDENT가 응답 제출
            3. SURVEY_MANAGER가 결과 조회
            4. 성공 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager",
            email="manager@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        respondent_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="respondent",
            email="respondent@test.com",
            password="resp123",
            role=Role.RESPONDENT
        )

        manager_login = auth_service.login("manager", "manager123", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        respondent_login = auth_service.login("respondent", "resp123", tenant_id)
        respondent_validate = auth_service.validate_session(respondent_login.value)
        respondent_user, _ = respondent_validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit_result = response_service.submit_response(
            respondent_user, survey_id, {question_id: "답변"}
        )
        assert submit_result.is_success()

        results_result = response_service.get_survey_results(manager_user, survey_id)
        assert results_result.is_success()
        results = results_result.value
        assert question_id in results

    def test_non_owner_manager_cannot_view_results(
        self, auth_service, survey_service, response_service
    ):
        """소유자가 아닌 SURVEY_MANAGER는 결과 조회 불가

        시나리오:
            1. Manager A가 설문 생성
            2. Manager B가 결과 조회 시도
            3. 실패 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        manager_a_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_a",
            email="manager_a@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        manager_b_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_b",
            email="manager_b@test.com",
            password="manager123",
            role=Role.SURVEY_MANAGER
        )

        login_a = auth_service.login("manager_a", "manager123", tenant_id)
        validate_a = auth_service.validate_session(login_a.value)
        manager_a_user, _ = validate_a.value

        login_b = auth_service.login("manager_b", "manager123", tenant_id)
        validate_b = auth_service.validate_session(login_b.value)
        manager_b_user, _ = validate_b.value

        survey_result = survey_service.create_survey(manager_a_user, "A의 설문", "설명")
        survey_id = survey_result.value

        results_result = response_service.get_survey_results(manager_b_user, survey_id)
        assert results_result.is_failure()
        assert "권한이 없습니다" in results_result.error
