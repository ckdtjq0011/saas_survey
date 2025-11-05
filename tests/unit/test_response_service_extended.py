import pytest
import uuid
import csv
from datetime import datetime
from pathlib import Path
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.category import Category
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from application.response_service import ResponseService
from tests.conftest import create_session_and_time_data


@pytest.fixture
def response_service(response_repo, response_history_repo, survey_repo, category_repo):
    """ResponseService 픽스처"""
    return ResponseService(response_repo, response_history_repo, survey_repo, category_repo)


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

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)

        first_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "첫 번째 답변"},
            session_id=session_id,
            time_spent_data=time_spent_data
        )
        assert first_result.is_success()

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)

        second_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "두 번째 답변"},
            session_id=session_id,
            time_spent_data=time_spent_data
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

            session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)

            result = response_service.submit_response(
                user=user,
                survey_id=survey_id,
                answers={question_id: f"답변{i}"},
                session_id=session_id,
                time_spent_data=time_spent_data
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

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)

        result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers=partial_answers,
            session_id=session_id,
            time_spent_data=time_spent_data
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

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)

        submit_result = response_service.submit_response(
            user=sample_respondent_user,
            survey_id=survey_id,
            answers={question_id: "원래 답변"},
            session_id=session_id,
            time_spent_data=time_spent_data
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
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
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
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
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
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
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


class TestExportResults:
    """설문 결과 CSV Export 테스트"""

    def test_export_results_creates_two_csv_files(
        self, response_service, sample_manager_user, sample_tenant, survey_repo, tmp_path
    ):
        """설문 결과를 Raw Data와 Summary 두 개의 CSV 파일로 export 성공

        시나리오:
            1. 설문 및 질문 생성 (RATING, TEXT, MULTIPLE_CHOICE)
            2. 여러 응답 추가
            3. export_results_to_csv 호출
            4. 두 개의 CSV 파일이 생성되었는지 확인
            5. 파일이 존재하고 읽을 수 있는지 확인
        """
        survey_id = str(uuid.uuid4())
        rating_q_id = str(uuid.uuid4())
        choice_q_id = str(uuid.uuid4())
        text_q_id = str(uuid.uuid4())

        rating_q = Question(
            id=rating_q_id,
            survey_id=survey_id,
            text="평점 질문",
            question_type=QuestionType.RATING,
            options=None,
            category_id=None
        )

        choice_q = Question(
            id=choice_q_id,
            survey_id=survey_id,
            text="객관식 질문",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=("선택1", "선택2", "선택3"),
            category_id=None
        )

        text_q = Question(
            id=text_q_id,
            survey_id=survey_id,
            text="텍스트 질문",
            question_type=QuestionType.TEXT,
            options=None,
            category_id=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="테스트 설문",
            description="Export 테스트용 설문",
            created_at=datetime.now(),
            questions=(rating_q, choice_q, text_q)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(rating_q)
        survey_repo.save_question(choice_q)
        survey_repo.save_question(text_q)

        for i in range(5):
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=rating_q_id,
                answer=str((i % 5) + 1),
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10 + i
            ))

            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=choice_q_id,
                answer=f"선택{(i % 3) + 1}",
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=15 + i
            ))

            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=text_q_id,
                answer=f"텍스트 답변 {i+1}",
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=20 + i
            ))

        result = response_service.export_results_to_csv(
            user=sample_manager_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_success()
        raw_path, summary_path = result.value

        assert Path(raw_path).exists()
        assert Path(summary_path).exists()
        assert Path(raw_path).suffix == ".csv"
        assert Path(summary_path).suffix == ".csv"
        assert "raw" in Path(raw_path).name
        assert "summary" in Path(summary_path).name

    def test_export_results_raw_data_format(
        self, response_service, sample_manager_user, sample_tenant, survey_repo, tmp_path
    ):
        """Raw Data CSV의 형식이 올바른지 검증

        시나리오:
            1. 설문 및 응답 생성
            2. CSV export
            3. Raw Data CSV 읽기
            4. 헤더 확인
            5. 데이터 행 수 확인
            6. 필수 필드 확인 (응답ID, 질문, 답변 등)
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="테스트 질문",
            question_type=QuestionType.RATING,
            options=None,
            category_id=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="테스트설문",
            description="설명",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        for i in range(3):
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=question_id,
                answer=str(i + 3),
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
            ))

        result = response_service.export_results_to_csv(
            user=sample_manager_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_success()
        raw_path, _ = result.value

        with open(raw_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 3

            expected_headers = [
                "응답ID", "설문제목", "질문", "질문유형", "질문범주",
                "답변", "응답자ID", "응답시간", "소요시간(초)", "세션ID"
            ]
            assert list(reader.fieldnames) == expected_headers

            for row in rows:
                assert row["설문제목"] == "테스트설문"
                assert row["질문"] == "테스트 질문"
                assert row["질문유형"] == "rating"
                assert row["답변"] in ["3", "4", "5"]
                assert row["소요시간(초)"] == "10"

    def test_export_results_permission_check(
        self, response_service, sample_respondent_user, sample_tenant, survey_repo, tmp_path
    ):
        """권한 없는 사용자의 export 차단

        시나리오:
            1. 설문 생성 (RESPONDENT는 소유자 아님)
            2. RESPONDENT 사용자가 export 시도
            3. 권한 없음 에러 반환
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.TEXT,
            options=None,
            category_id=None
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

        result = response_service.export_results_to_csv(
            user=sample_respondent_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_failure()
        assert "권한" in result.error

    def test_export_results_no_responses(
        self, response_service, sample_manager_user, sample_tenant, survey_repo, tmp_path
    ):
        """응답이 없는 설문의 export

        시나리오:
            1. 설문 생성 (응답 없음)
            2. export 시도
            3. CSV 파일은 생성되지만 데이터 행은 0개
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="질문",
            question_type=QuestionType.RATING,
            options=None,
            category_id=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="빈설문",
            description="응답 없음",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        result = response_service.export_results_to_csv(
            user=sample_manager_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_success()
        raw_path, _ = result.value

        with open(raw_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0

    def test_export_results_with_category(
        self, response_service, sample_manager_user, sample_tenant, survey_repo, category_repo, tmp_path
    ):
        """범주 정보가 포함된 설문 export

        시나리오:
            1. 범주 생성
            2. 범주가 설정된 질문으로 설문 생성
            3. 응답 추가
            4. export
            5. CSV에 범주 이름이 포함되었는지 확인
        """
        category_id = str(uuid.uuid4())
        category = Category(
            id=category_id,
            tenant_id=sample_tenant.id,
            name="만족도",
            description="만족도 관련 질문",
            parent_id=None,
            order=1,
            is_active=True,
            created_at=datetime.now()
        )
        category_repo.save_category(category)

        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="만족도 평가",
            question_type=QuestionType.RATING,
            options=None,
            category_id=category_id
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="범주설문",
            description="범주 테스트",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        response_service.response_repository.save(Response(
            id=str(uuid.uuid4()),
            survey_id=survey_id,
            question_id=question_id,
            answer="5",
            respondent_id=str(uuid.uuid4()),
            answered_at=datetime.now(),
            session_id=str(uuid.uuid4()),
            time_spent_seconds=10
        ))

        result = response_service.export_results_to_csv(
            user=sample_manager_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_success()
        raw_path, _ = result.value

        with open(raw_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["질문범주"] == "만족도"

    def test_export_results_summary_format(
        self, response_service, sample_manager_user, sample_tenant, survey_repo, tmp_path
    ):
        """Summary CSV의 형식이 올바른지 검증

        시나리오:
            1. RATING 질문으로 설문 생성
            2. 여러 평점 응답 추가
            3. export
            4. Summary CSV 읽기
            5. 설문 정보, 평균 평점, 분포 확인
        """
        survey_id = str(uuid.uuid4())
        question_id = str(uuid.uuid4())

        question = Question(
            id=question_id,
            survey_id=survey_id,
            text="서비스 평가",
            question_type=QuestionType.RATING,
            options=None,
            category_id=None
        )

        survey = Survey(
            id=survey_id,
            tenant_id=sample_tenant.id,
            owner_id=sample_manager_user.id,
            title="만족도조사",
            description="서비스 만족도",
            created_at=datetime.now(),
            questions=(question,)
        )
        survey_repo.save_survey(survey)
        survey_repo.save_question(question)

        ratings = [5, 5, 4, 4, 3]
        for rating in ratings:
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=survey_id,
                question_id=question_id,
                answer=str(rating),
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=str(uuid.uuid4()),
                time_spent_seconds=10
            ))

        result = response_service.export_results_to_csv(
            user=sample_manager_user,
            survey_id=survey_id,
            export_dir=tmp_path
        )

        assert result.is_success()
        _, summary_path = result.value

        with open(summary_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "만족도조사" in content
            assert "서비스 평가" in content
            assert "rating" in content
            assert "4.2" in content or "4.20" in content
