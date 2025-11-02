import pytest
import uuid
from datetime import datetime
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from application.response_service import ResponseService


@pytest.fixture
def response_service(response_repo, survey_repo):
    """ResponseService 픽스처"""
    return ResponseService(response_repo, survey_repo)


class TestDuplicateResponseHandling:
    """중복 응답 처리 테스트"""

    def test_user_submits_response_twice_to_same_survey(
        self, response_service, sample_respondent_user, sample_tenant, survey_repo
    ):
        """동일 사용자가 같은 설문에 두 번 응답

        시나리오:
            1. 설문 및 질문 생성
            2. 첫 번째 응답 제출
            3. 두 번째 응답 제출
            4. 모두 성공 확인 (중복 방지 없음)
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        first_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "첫 번째 답변"}
        )
        assert first_result.is_success()

        second_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "두 번째 답변"}
        )
        assert second_result.is_success()

    def test_multiple_users_submit_responses_to_same_question(
        self, response_service, sample_tenant, survey_repo, auth_service, response_repo
    ):
        """여러 사용자가 동일 질문에 응답

        시나리오:
            1. 설문 및 질문 생성
            2. 3명의 사용자 등록
            3. 각각 응답 제출
            4. 질문별 응답이 3개인지 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        for i in range(3):
            user_result = auth_service.register_user(
                tenant_id=sample_tenant.id,
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                role=Role.RESPONDENT
            )
            user_id = user_result.value
            user = auth_service.user_repository.find_user_by_id(user_id)

            result = response_service.submit_response(
                user=user,
                survey_id=survey_id,
                answers={question_id: f"답변{i}"}
            )
            assert result.is_success()

        responses = response_repo.find_by_question_id(question_id)
        assert len(responses) == 3

    def test_user_submits_partial_answers(
        self, response_service, sample_respondent_user, sample_tenant, survey_repo
    ):
        """일부 질문만 응답

        시나리오:
            1. 3개 질문이 있는 설문 생성
            2. 2개 질문만 응답 제출
            3. 성공 확인 (부분 응답 허용)
        """
        survey_id = str(uuid.uuid4())
        questions = []

        for i in range(3):
            q_id = str(uuid.uuid4())
            question = Question(
                id=q_id,
                survey_id=survey_id,
                text=f"질문{i+1}",
                question_type=QuestionType.TEXT,
                options=None
            )
            questions.append(question)

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="설문",
            description="설명",
            created_at=datetime.now(),
            questions=tuple(questions)
        )
        survey_repo.save_survey(survey)
        for q in questions:
            survey_repo.save_question(q)

        partial_answers = {
            questions[0].id: "답변1",
            questions[1].id: "답변2"
        }

        result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers=partial_answers
        )

        assert result.is_success()


class TestPermissionRefinement:
    """권한 세분화 테스트"""

    def test_respondent_can_update_own_response(
        self, response_service, sample_respondent_user, sample_tenant, survey_repo, response_repo
    ):
        """응답자가 자신의 응답 수정 가능

        시나리오:
            1. 응답 제출
            2. 동일 사용자가 응답 수정
            3. 성공 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        submit_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "원래 답변"}
        )
        assert submit_result.is_success()

        responses = response_repo.find_by_question_id(question_id)
        response_id = responses[0].id

        update_result = response_service.update_response(
            user=sample_respondent_user,
            response_id=response_id,
            answer="수정된 답변"
        )

        assert update_result.is_success()

    def test_non_owner_survey_manager_cannot_view_results(
        self, response_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """소유자가 아닌 SURVEY_MANAGER는 결과 조회 불가

        시나리오:
            1. 다른 사용자의 설문 생성
            2. SURVEY_MANAGER가 결과 조회 시도
            3. 실패 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="다른 사람의 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        result = response_service.get_survey_results(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert result.is_failure()
        assert "권한이 없습니다" in result.error

    def test_survey_owner_can_view_results(
        self, response_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """설문 소유자는 결과 조회 가능

        시나리오:
            1. 사용자가 설문 생성
            2. 본인 설문 결과 조회
            3. 성공 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="내 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        result = response_service.get_survey_results(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert result.is_success()

    def test_tenant_admin_can_view_all_results(
        self, response_service, sample_admin_user, sample_tenant, survey_repo
    ):
        """TENANT_ADMIN은 모든 결과 조회 가능

        시나리오:
            1. 다른 사용자의 설문 생성
            2. TENANT_ADMIN이 결과 조회
            3. 성공 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=str(uuid.uuid4()),
            title="다른 사람의 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        result = response_service.get_survey_results(
            user=sample_admin_user,
            survey_id=survey_id
        )

        assert result.is_success()


class TestStatisticsAccuracy:
    """통계 정확도 테스트"""

    def test_rating_average_calculation_with_multiple_responses(
        self, response_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """여러 응답의 평점 평균 계산 정확도

        시나리오:
            1. RATING 질문 생성
            2. 5개 응답 제출 (1,2,3,4,5)
            3. 결과 조회하여 평균이 3.0인지 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="평점",
            question_type=QuestionType.RATING,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="평점 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        for rating in [1, 2, 3, 4, 5]:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=question_id,
                answer=str(rating),
                respondent_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert result.is_success()
        stats = result.value
        assert question_id in stats
        assert stats[question_id]["count"] == 5
        assert stats[question_id]["average"] == 3.0

    def test_multiple_choice_distribution_accuracy(
        self, response_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """객관식 선택지 분포 정확도

        시나리오:
            1. MULTIPLE_CHOICE 질문 생성
            2. 선택지별 응답 제출 (A:3개, B:2개, C:1개)
            3. 결과 조회하여 분포 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="선택",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=("A", "B", "C")
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="객관식 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        answers = ["A", "A", "A", "B", "B", "C"]
        for answer in answers:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=question_id,
                answer=answer,
                respondent_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert result.is_success()
        stats = result.value
        assert question_id in stats
        assert stats[question_id]["count"] == 6
        assert stats[question_id]["distribution"]["A"] == 3
        assert stats[question_id]["distribution"]["B"] == 2
        assert stats[question_id]["distribution"]["C"] == 1

    def test_text_question_response_collection(
        self, response_service, sample_manager_user, sample_tenant, survey_repo
    ):
        """텍스트 질문 응답 수집 정확도

        시나리오:
            1. TEXT 질문 생성
            2. 3개 응답 제출
            3. 결과 조회하여 모든 답변이 포함되었는지 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="의견",
            question_type=QuestionType.TEXT,
            options=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="텍스트 설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        expected_answers = ["답변1", "답변2", "답변3"]
        for answer in expected_answers:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=question_id,
                answer=answer,
                respondent_id=str(uuid.uuid4()),
                created_at=datetime.now()
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(
            user=sample_manager_user,
            survey_id=survey_id
        )

        assert result.is_success()
        stats = result.value
        assert question_id in stats
        assert stats[question_id]["count"] == 3
        assert set(stats[question_id]["answers"]) == set(expected_answers)
