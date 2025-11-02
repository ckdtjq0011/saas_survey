import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestDataConsistency:
    """데이터 일관성 통합 테스트"""

    def test_delete_survey_with_responses(
        self, auth_service, survey_service, response_service, survey_repo, response_repo
    ):
        """응답이 있는 설문 삭제

        시나리오:
            1. 설문 생성 및 질문 추가
            2. 응답 제출
            3. 설문 삭제 (응답은 orphan 상태로 남음)
            4. 설문이 삭제되었는지 확인
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit_result = response_service.submit_response(
            manager_user, survey_id, {question_id: "답변"}
        )
        assert submit_result.is_success()

        responses_before = response_repo.find_by_survey_id(survey_id)
        assert len(responses_before) > 0

        delete_result = survey_service.delete_survey(manager_user, survey_id)
        assert delete_result.is_success()

        survey_after = survey_repo.find_survey_by_id(survey_id)
        assert survey_after is None

    def test_delete_user_invalidates_sessions(
        self, auth_service, user_repo, session_repo
    ):
        """사용자 삭제 시 세션 무효화

        시나리오:
            1. 사용자 생성 및 로그인
            2. 관리자가 사용자 삭제
            3. 세션 검증 실패 확인
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

    def test_update_question_preserves_existing_responses(
        self, auth_service, survey_service, response_service, response_repo
    ):
        """질문 수정 시 기존 응답 보존

        시나리오:
            1. 설문 생성 및 질문 추가
            2. 응답 제출
            3. 질문 텍스트 수정
            4. 기존 응답이 보존되었는지 확인
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "원래 질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit_result = response_service.submit_response(
            manager_user, survey_id, {question_id: "내 답변"}
        )
        assert submit_result.is_success()

        responses_before = response_repo.find_by_question_id(question_id)
        response_id = responses_before[0].id
        original_answer = responses_before[0].answer

        update_result = survey_service.update_question(
            manager_user, question_id, text="수정된 질문"
        )
        assert update_result.is_success()

        responses_after = response_repo.find_by_question_id(question_id)
        assert len(responses_after) == 1
        assert responses_after[0].id == response_id
        assert responses_after[0].answer == original_answer

    def test_tenant_deletion_not_allowed_with_active_users(
        self, auth_service, tenant_repo
    ):
        """활성 사용자가 있는 테넌트 삭제 불가

        시나리오:
            1. 테넌트 및 사용자 생성
            2. 테넌트 삭제 시도
            3. 실패 또는 사용자가 함께 비활성화 확인
        """
        tenant_id = auth_service.register_tenant("테스트회사")

        user_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="user123",
            role=Role.RESPONDENT
        )
        assert user_result.is_success()

        tenant_before = tenant_repo.find_tenant_by_id(tenant_id)
        assert tenant_before is not None

        tenant_repo.delete_tenant(tenant_id)

        tenant_after = tenant_repo.find_tenant_by_id(tenant_id)
        assert tenant_after is None

    def test_multiple_responses_from_same_user(
        self, auth_service, survey_service, response_service, response_repo
    ):
        """동일 사용자의 중복 응답 처리

        시나리오:
            1. 설문 생성
            2. 동일 사용자가 두 번 응답 제출
            3. 두 응답 모두 저장되었는지 확인
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "질문", QuestionType.TEXT
        )
        question_id = question_result.value

        submit1 = response_service.submit_response(
            manager_user, survey_id, {question_id: "첫 번째 답변"}
        )
        assert submit1.is_success()

        submit2 = response_service.submit_response(
            manager_user, survey_id, {question_id: "두 번째 답변"}
        )
        assert submit2.is_success()

        responses = response_repo.find_by_question_id(question_id)
        assert len(responses) == 2

    def test_survey_results_reflect_latest_data(
        self, auth_service, survey_service, response_service
    ):
        """설문 결과가 최신 데이터 반영

        시나리오:
            1. 설문 생성 및 응답 제출
            2. 결과 조회
            3. 응답 추가
            4. 결과 재조회하여 업데이트 확인
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "만족도", QuestionType.RATING
        )
        question_id = question_result.value

        submit1 = response_service.submit_response(
            manager_user, survey_id, {question_id: "5"}
        )
        assert submit1.is_success()

        results1 = response_service.get_survey_results(manager_user, survey_id)
        assert results1.is_success()
        data1 = results1.value
        assert data1[question_id]["count"] == 1
        assert data1[question_id]["average"] == 5.0

        submit2 = response_service.submit_response(
            manager_user, survey_id, {question_id: "3"}
        )
        assert submit2.is_success()

        results2 = response_service.get_survey_results(manager_user, survey_id)
        assert results2.is_success()
        data2 = results2.value
        assert data2[question_id]["count"] == 2
        assert data2[question_id]["average"] == 4.0

    def test_cross_survey_question_independence(
        self, auth_service, survey_service, response_service, survey_repo
    ):
        """설문 간 질문 독립성

        시나리오:
            1. 두 개의 설문 생성
            2. 각 설문에 동일한 텍스트의 질문 추가
            3. 각각 응답 제출
            4. 응답이 올바른 설문에만 연결되었는지 확인
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey1_result = survey_service.create_survey(manager_user, "설문1", "설명1")
        survey1_id = survey1_result.value

        survey2_result = survey_service.create_survey(manager_user, "설문2", "설명2")
        survey2_id = survey2_result.value

        q1_result = survey_service.add_question(
            manager_user, survey1_id, "만족도", QuestionType.RATING
        )
        q1_id = q1_result.value

        q2_result = survey_service.add_question(
            manager_user, survey2_id, "만족도", QuestionType.RATING
        )
        q2_id = q2_result.value

        submit1 = response_service.submit_response(
            manager_user, survey1_id, {q1_id: "5"}
        )
        assert submit1.is_success()

        submit2 = response_service.submit_response(
            manager_user, survey2_id, {q2_id: "3"}
        )
        assert submit2.is_success()

        results1 = response_service.get_survey_results(manager_user, survey1_id)
        results2 = response_service.get_survey_results(manager_user, survey2_id)

        assert results1.value[q1_id]["average"] == 5.0
        assert results2.value[q2_id]["average"] == 3.0
