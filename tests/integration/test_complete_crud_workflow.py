import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


def test_complete_crud_workflow(auth_service, survey_service, response_service, tenant_repo, user_repo, survey_repo):
    """완전한 CRUD 워크플로우 테스트

    시나리오:
    1. 테넌트 생성
    2. 관리자 사용자 생성
    3. 로그인
    4. 설문 생성
    5. 질문 추가
    6. 설문 수정
    7. 응답자 생성
    8. 응답 제출
    9. 결과 조회
    10. 데이터 삭제 (응답 -> 질문 -> 설문 -> 사용자)
    """

    tenant_id = auth_service.register_tenant("테스트회사")
    assert tenant_id is not None

    admin_result = auth_service.register_user(
        tenant_id=tenant_id,
        username="admin",
        email="admin@test.com",
        password="admin123",
        role=Role.TENANT_ADMIN
    )
    assert admin_result.is_success()
    admin_id = admin_result.value

    login_result = auth_service.login("admin", "admin123", tenant_id)
    assert login_result.is_success()
    api_key = login_result.value

    validate_result = auth_service.validate_session(api_key)
    assert validate_result.is_success()
    admin_user, session = validate_result.value

    survey_result = survey_service.create_survey(admin_user, "만족도조사", "테스트 설문")
    assert survey_result.is_success()
    survey_id = survey_result.value

    q1_result = survey_service.add_question(
        admin_user, survey_id, "의견을 입력하세요", QuestionType.TEXT
    )
    assert q1_result.is_success()

    q2_result = survey_service.add_question(
        admin_user, survey_id, "만족도는?", QuestionType.RATING
    )
    assert q2_result.is_success()

    q3_result = survey_service.add_question(
        admin_user, survey_id, "선택하세요", QuestionType.MULTIPLE_CHOICE, ["A", "B", "C"]
    )
    assert q3_result.is_success()

    update_result = survey_service.update_survey(admin_user, survey_id, title="수정된 제목")
    assert update_result.is_success()

    updated_survey_result = survey_service.get_survey(admin_user, survey_id)
    assert updated_survey_result.is_success()
    updated_survey = updated_survey_result.value
    assert updated_survey.title == "수정된 제목"

    respondent_result = auth_service.register_user(
        tenant_id=tenant_id,
        username="respondent",
        email="respondent@test.com",
        password="resp123",
        role=Role.RESPONDENT
    )
    assert respondent_result.is_success()

    resp_login_result = auth_service.login("respondent", "resp123", tenant_id)
    assert resp_login_result.is_success()
    resp_api_key = resp_login_result.value

    resp_validate_result = auth_service.validate_session(resp_api_key)
    assert resp_validate_result.is_success()
    respondent_user, _ = resp_validate_result.value

    questions = survey_repo.find_questions_by_survey_id(survey_id)
    answers = {
        questions[0].id: "좋습니다",
        questions[1].id: "4",
        questions[2].id: "A"
    }

    submit_result = response_service.submit_response(respondent_user, survey_id, answers)
    assert submit_result.is_success()

    results_result = response_service.get_survey_results(admin_user, survey_id)
    assert results_result.is_success()
    results = results_result.value
    assert len(results) == 3

    responses = response_service.response_repository.find_by_survey_id(survey_id)
    for resp in responses:
        response_service.response_repository.delete_response(resp.id)

    for question in questions:
        survey_service.delete_question(admin_user, question.id)

    delete_survey_result = survey_service.delete_survey(admin_user, survey_id)
    assert delete_survey_result.is_success()

    delete_user_result = auth_service.delete_user(admin_user, respondent_user.id)
    assert delete_user_result.is_success()

    assert user_repo.find_user_by_id(respondent_user.id) is None
    assert survey_repo.find_survey_by_id(survey_id) is None


def test_multitenant_isolation(auth_service, survey_service):
    """멀티테넌트 격리 테스트"""

    tenant_a_id = auth_service.register_tenant("회사A")
    tenant_b_id = auth_service.register_tenant("회사B")

    admin_a_result = auth_service.register_user(
        tenant_id=tenant_a_id,
        username="admin_a",
        email="admin_a@test.com",
        password="admin123",
        role=Role.TENANT_ADMIN
    )
    assert admin_a_result.is_success()

    admin_b_result = auth_service.register_user(
        tenant_id=tenant_b_id,
        username="admin_b",
        email="admin_b@test.com",
        password="admin123",
        role=Role.TENANT_ADMIN
    )
    assert admin_b_result.is_success()

    login_a_result = auth_service.login("admin_a", "admin123", tenant_a_id)
    assert login_a_result.is_success()
    validate_a_result = auth_service.validate_session(login_a_result.value)
    admin_a_user, _ = validate_a_result.value

    login_b_result = auth_service.login("admin_b", "admin123", tenant_b_id)
    assert login_b_result.is_success()
    validate_b_result = auth_service.validate_session(login_b_result.value)
    admin_b_user, _ = validate_b_result.value

    survey_a_result = survey_service.create_survey(admin_a_user, "설문A", "설명A")
    assert survey_a_result.is_success()
    survey_a_id = survey_a_result.value

    survey_b_result = survey_service.create_survey(admin_b_user, "설문B", "설명B")
    assert survey_b_result.is_success()
    survey_b_id = survey_b_result.value

    access_b_from_a = survey_service.get_survey(admin_a_user, survey_b_id)
    assert access_b_from_a.is_failure()
    assert "다른 테넌트" in access_b_from_a.error

    access_a_from_b = survey_service.get_survey(admin_b_user, survey_a_id)
    assert access_a_from_b.is_failure()
    assert "다른 테넌트" in access_a_from_b.error


def test_validation_rating_answer(auth_service, survey_service, response_service):
    """RATING 답변 검증 테스트"""

    tenant_id = auth_service.register_tenant("테스트회사")
    admin_result = auth_service.register_user(
        tenant_id=tenant_id,
        username="admin",
        email="admin@test.com",
        password="admin123",
        role=Role.TENANT_ADMIN
    )
    login_result = auth_service.login("admin", "admin123", tenant_id)
    validate_result = auth_service.validate_session(login_result.value)
    admin_user, _ = validate_result.value

    survey_result = survey_service.create_survey(admin_user, "평점조사", "설명")
    survey_id = survey_result.value

    q_result = survey_service.add_question(
        admin_user, survey_id, "만족도는?", QuestionType.RATING
    )
    question_id = q_result.value

    invalid_result = response_service.submit_response(admin_user, survey_id, {question_id: "10"})
    assert invalid_result.is_failure()
    assert "1-5 사이여야 합니다" in invalid_result.error

    valid_result = response_service.submit_response(admin_user, survey_id, {question_id: "4"})
    assert valid_result.is_success()


def test_validation_multiple_choice_answer(auth_service, survey_service, response_service):
    """MULTIPLE_CHOICE 답변 검증 테스트"""

    tenant_id = auth_service.register_tenant("테스트회사")
    admin_result = auth_service.register_user(
        tenant_id=tenant_id,
        username="admin",
        email="admin@test.com",
        password="admin123",
        role=Role.TENANT_ADMIN
    )
    login_result = auth_service.login("admin", "admin123", tenant_id)
    validate_result = auth_service.validate_session(login_result.value)
    admin_user, _ = validate_result.value

    survey_result = survey_service.create_survey(admin_user, "선택조사", "설명")
    survey_id = survey_result.value

    q_result = survey_service.add_question(
        admin_user, survey_id, "선택하세요", QuestionType.MULTIPLE_CHOICE, ["A", "B", "C"]
    )
    question_id = q_result.value

    invalid_result = response_service.submit_response(admin_user, survey_id, {question_id: "D"})
    assert invalid_result.is_failure()
    assert "유효하지 않은 선택지입니다" in invalid_result.error

    valid_result = response_service.submit_response(admin_user, survey_id, {question_id: "B"})
    assert valid_result.is_success()
