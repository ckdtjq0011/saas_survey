import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestErrorPropagation:
    """에러 전파 통합 테스트"""

    def test_invalid_survey_id_propagates_to_service(
        self, auth_service, survey_service
    ):
        """잘못된 설문 ID가 서비스 레이어까지 전파

        시나리오:
            1. 사용자 생성 및 로그인
            2. 존재하지 않는 설문 ID로 수정 시도
            3. 서비스 레이어에서 에러 반환
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        result = survey_service.update_survey(
            manager_user, "nonexistent_survey_id", title="새 제목"
        )
        assert result.is_failure()
        assert "설문을 찾을 수 없습니다" in result.error

    def test_invalid_question_id_propagates_to_service(
        self, auth_service, survey_service
    ):
        """잘못된 질문 ID가 서비스 레이어까지 전파

        시나리오:
            1. 설문 생성
            2. 존재하지 않는 질문 ID로 수정 시도
            3. 서비스 레이어에서 에러 반환
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        result = survey_service.update_question(
            manager_user, "nonexistent_question_id", text="새 질문"
        )
        assert result.is_failure()
        assert "질문을 찾을 수 없습니다" in result.error

    def test_permission_error_propagates_from_domain_to_service(
        self, auth_service, survey_service
    ):
        """권한 에러가 도메인에서 서비스까지 전파

        시나리오:
            1. 두 명의 SURVEY_MANAGER 생성
            2. Manager A가 설문 생성
            3. Manager B가 수정 시도
            4. 도메인 레이어 권한 검증 실패가 서비스까지 전파
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_a",
            email="manager_a@test.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )

        auth_service.register_user(
            tenant_id=tenant_id,
            username="manager_b",
            email="manager_b@test.com",
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

        result = survey_service.update_survey(user_b, survey_id, title="B가 수정")
        assert result.is_failure()
        assert "권한이 없습니다" in result.error

    def test_validation_error_propagates_from_value_object(
        self, auth_service
    ):
        """값 객체 검증 에러가 전파

        시나리오:
            1. 잘못된 형식의 이메일로 사용자 등록 시도
            2. 값 객체 검증 실패가 서비스까지 전파
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        with pytest.raises(ValueError) as excinfo:
            auth_service.register_user(
                tenant_id=tenant_id,
                username="user",
                email="invalid-email",
                password="password123",
                role=Role.RESPONDENT
            )
        assert "이메일" in str(excinfo.value) or "email" in str(excinfo.value).lower()

    def test_duplicate_username_error_propagates(
        self, auth_service
    ):
        """중복 사용자명 에러가 전파

        시나리오:
            1. 사용자 등록
            2. 동일 사용자명으로 재등록 시도
            3. 중복 에러 전파
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        result1 = auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user1@test.com",
            password="password123",
            role=Role.RESPONDENT
        )
        assert result1.is_success()

        result2 = auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user2@test.com",
            password="password123",
            role=Role.RESPONDENT
        )
        assert result2.is_failure()
        assert "이미 존재" in result2.error or "중복" in result2.error

    def test_invalid_answer_type_propagates_to_response_service(
        self, auth_service, survey_service, response_service, survey_repo
    ):
        """잘못된 답변 형식 에러가 전파

        시나리오:
            1. RATING 질문 생성
            2. 범위 밖의 값으로 응답 제출
            3. 검증 실패 에러 전파
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
        validate = auth_service.validate_session(login.value)
        manager_user, _ = validate.value

        survey_result = survey_service.create_survey(manager_user, "설문", "설명")
        survey_id = survey_result.value

        question_result = survey_service.add_question(
            manager_user, survey_id, "만족도", QuestionType.RATING
        )
        question_id = question_result.value

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        result = response_service.submit_response(
            manager_user, survey_id, {question_id: "10"}, session_id, time_spent_data
        )
        assert result.is_failure()
        assert ("1-5" in result.error or "1에서 5" in result.error or "범위" in result.error)

    def test_login_with_wrong_password_error(
        self, auth_service
    ):
        """잘못된 비밀번호 로그인 에러

        시나리오:
            1. 사용자 등록
            2. 잘못된 비밀번호로 로그인 시도
            3. 인증 실패 에러 전파
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        auth_service.register_user(
            tenant_id=tenant_id,
            username="user",
            email="user@test.com",
            password="correct_password",
            role=Role.RESPONDENT
        )

        result = auth_service.login("user", "wrong_password", tenant_id)
        assert result.is_failure()
        assert "비밀번호" in result.error or "인증" in result.error

    def test_nonexistent_user_login_error(
        self, auth_service
    ):
        """존재하지 않는 사용자 로그인 에러

        시나리오:
            1. 테넌트만 생성
            2. 존재하지 않는 사용자로 로그인 시도
            3. 에러 전파
        """
        tenant_id = auth_service.register_tenant("테스트 테넌트")

        result = auth_service.login("nonexistent_user", "password", tenant_id)
        assert result.is_failure()
        assert ("사용자명 또는 비밀번호가 올바르지 않습니다" in result.error or
                "사용자를 찾을 수 없습니다" in result.error)
