import pytest
import uuid
from datetime import datetime
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from application.survey_service import SurveyService


@pytest.fixture
def survey_service(survey_repo):
    """SurveyService 픽스처"""
    return SurveyService(survey_repo)


class TestOwnershipValidation:
    """설문 소유권 검증 테스트"""

    def test_non_owner_survey_manager_cannot_manage_survey(
        self, survey_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """소유자가 아닌 SURVEY_MANAGER는 설문 관리 불가

        시나리오:
            1. 다른 사용자가 설문 생성
            2. SURVEY_MANAGER가 질문 추가 시도
            3. 실패 확인 (소유자만 관리 가능)
        """
        survey_id = str(uuid.uuid4())
        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="다른 사람의 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        result = survey_service.add_question(
            user=sample_manager_user,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT
        )

        assert result.is_failure()
        assert "권한이 없습니다" in result.error

    def test_non_owner_respondent_cannot_manage_survey(
        self, survey_service, sample_respondent_user, sample_tenant, survey_repo
    ):
        """소유자가 아닌 RESPONDENT는 설문 관리 불가

        시나리오:
            1. 설문 생성
            2. RESPONDENT가 질문 추가 시도
            3. 실패 확인
        """
        survey_id = str(uuid.uuid4())
        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        result = survey_service.add_question(
            user=sample_respondent_user,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT
        )

        assert result.is_failure()
        assert "권한이 없습니다" in result.error

    def test_owner_can_manage_survey_all_operations(
        self, survey_service, sample_manager_user, sample_tenant
    ):
        """소유자는 모든 작업 가능

        시나리오:
            1. 설문 생성
            2. 질문 추가
            3. 설문 수정
            4. 질문 수정
            5. 설문 삭제
            6. 모든 작업 성공 확인
        """
        create_result = survey_service.create_survey(
            user=sample_manager_user,
            title="내 설문",
            description="설명"
        )
        assert create_result.is_success()
        survey_id = create_result.value

        add_q_result = survey_service.add_question(
            user=sample_manager_user,
            survey_id=survey_id,
            text="질문1",
            question_type=QuestionType.TEXT
        )
        assert add_q_result.is_success()
        question_id = add_q_result.value

        update_s_result = survey_service.update_survey(
            user=sample_manager_user,
            survey_id=survey_id,
            title="수정된 제목"
        )
        assert update_s_result.is_success()

        update_q_result = survey_service.update_question(
            user=sample_manager_user,
            question_id=question_id,
            text="수정된 질문"
        )
        assert update_q_result.is_success()

        delete_result = survey_service.delete_survey(
            user=sample_manager_user,
            survey_id=survey_id
        )
        assert delete_result.is_success()

    def test_cross_tenant_survey_access_denied(
        self, survey_service, sample_manager_user, survey_repo, auth_service
    ):
        """다른 테넌트의 설문 접근 거부

        시나리오:
            1. 테넌트A의 사용자가 설문 생성
            2. 테넌트B의 사용자가 해당 설문 조회 시도
            3. 실패 확인
        """
        tenant_a_id = str(uuid.uuid4())
        tenant_a_result = auth_service.register_tenant("테넌트A")
        tenant_a_id = tenant_a_result

        user_a_result = auth_service.register_user(
            tenant_id=tenant_a_id,
            username="usera",
            email="usera@example.com",
            password="password123",
            role=Role.SURVEY_MANAGER
        )
        user_a_id = user_a_result.value
        user_a = auth_service.user_repository.find_user_by_id(user_a_id)

        survey_id = str(uuid.uuid4())
        survey = Survey(
            id=survey_id,
            tenant_id=tenant_a_id,
            owner_id=user_a_id,
            title="테넌트A 설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey)

        get_result = survey_service.get_survey(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert get_result.is_failure()
        assert "다른 테넌트" in get_result.error


class TestQuestionManagement:
    """질문 관리 테스트"""

    def test_add_multiple_questions_to_survey(
        self, survey_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """설문에 여러 질문 추가

        시나리오:
            1. 설문 생성
            2. 3개의 질문 추가
            3. 설문 조회하여 질문 수 확인
        """
        create_result = survey_service.create_survey(
            user=sample_manager_user,
            title="다중 질문 설문",
            description="설명"
        )
        survey_id = create_result.value

        question_ids = []
        for i in range(3):
            result = survey_service.add_question(
                user=sample_manager_user,
                survey_id=survey_id,
                text=f"질문{i+1}",
                question_type=QuestionType.TEXT
            )
            assert result.is_success()
            question_ids.append(result.value)

        survey = survey_repo.find_survey_by_id(survey_id)
        assert survey is not None
        assert len(survey.questions) == 3

    def test_update_question_with_invalid_id(self, survey_service, sample_manager_user):
        """존재하지 않는 질문 수정 시도

        시나리오:
            1. 존재하지 않는 question_id로 수정 시도
            2. 실패 확인
        """
        result = survey_service.update_question(
            user=sample_manager_user,
            question_id="nonexistent_question_id",
            text="수정"
        )

        assert result.is_failure()
        assert "질문을 찾을 수 없습니다" in result.error

    def test_delete_question_from_multi_question_survey(
        self, survey_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """여러 질문 중 하나만 삭제

        시나리오:
            1. 설문 생성 및 3개 질문 추가
            2. 중간 질문 삭제
            3. 설문 조회하여 2개 질문만 남았는지 확인
        """
        create_result = survey_service.create_survey(
            user=sample_manager_user,
            title="질문 삭제 테스트",
            description="설명"
        )
        survey_id = create_result.value

        question_ids = []
        for i in range(3):
            result = survey_service.add_question(
                user=sample_manager_user,
                survey_id=survey_id,
                text=f"질문{i+1}",
                question_type=QuestionType.TEXT
            )
            question_ids.append(result.value)

        delete_result = survey_service.delete_question(
            user=sample_manager_user,
            question_id=question_ids[1]
        )
        assert delete_result.is_success()

        survey = survey_repo.find_survey_by_id(survey_id)
        assert len(survey.questions) == 2


class TestSurveyStatus:
    """설문 상태 관리 테스트"""

    def test_get_surveys_by_user_filters_by_tenant(
        self, survey_service, sample_manager_user, sample_tenant, survey_repo, auth_service
    ):
        """get_surveys_by_user가 테넌트별 필터링 수행

        시나리오:
            1. 테넌트A에 설문 2개 생성
            2. 테넌트B에 설문 1개 생성
            3. 테넌트A 사용자가 조회 시 2개만 조회
        """
        survey1_id = str(uuid.uuid4())
        survey1 = Survey(
            id=survey1_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="설문1",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey1)

        survey2_id = str(uuid.uuid4())
        survey2 = Survey(
            id=survey2_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="설문2",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey2)

        other_tenant_id = auth_service.register_tenant("다른테넌트")
        survey3_id = str(uuid.uuid4())
        survey3 = Survey(
            id=survey3_id,
            tenant_id=other_tenant_id,
            owner_id=str(uuid.uuid4()),
            title="다른테넌트설문",
            description="설명",
            created_at=datetime.now(),
            questions=()
        )
        survey_repo.save_survey(survey3)

        surveys = survey_service.get_surveys_by_user(sample_manager_user)

        assert len(surveys) == 2
        assert all(s.tenant_id == sample_tenant.id for s in surveys)

    def test_delete_survey_cascades_to_questions(
        self, survey_service, sample_manager_user, survey_repo
    ):
        """설문 삭제 시 질문도 함께 삭제

        시나리오:
            1. 설문 생성 및 질문 2개 추가
            2. 설문 삭제
            3. 질문도 함께 삭제되었는지 확인
        """
        create_result = survey_service.create_survey(
            user=sample_manager_user,
            title="삭제 테스트",
            description="설명"
        )
        survey_id = create_result.value

        question_ids = []
        for i in range(2):
            result = survey_service.add_question(
                user=sample_manager_user,
                survey_id=survey_id,
                text=f"질문{i+1}",
                question_type=QuestionType.TEXT
            )
            question_ids.append(result.value)

        delete_result = survey_service.delete_survey(
            user=sample_manager_user,
            survey_id=survey_id
        )
        assert delete_result.is_success()

        survey = survey_repo.find_survey_by_id(survey_id)
        assert survey is None

        questions = survey_repo.find_questions_by_survey_id(survey_id)
        assert len(questions) == 0

    def test_update_survey_validates_fields(
        self, survey_service, sample_manager_user, survey_repo
    ):
        """설문 수정 시 필드 검증

        시나리오:
            1. 설문 생성
            2. title과 description 수정
            3. 변경사항이 저장되었는지 확인
        """
        create_result = survey_service.create_survey(
            user=sample_manager_user,
            title="원본 제목",
            description="원본 설명"
        )
        survey_id = create_result.value

        update_result = survey_service.update_survey(
            user=sample_manager_user,
            survey_id=survey_id,
            title="수정된 제목",
            description="수정된 설명"
        )
        assert update_result.is_success()

        updated_survey = survey_repo.find_survey_by_id(survey_id)
        assert updated_survey is not None
        assert updated_survey.title == "수정된 제목"
        assert updated_survey.description == "수정된 설명"
