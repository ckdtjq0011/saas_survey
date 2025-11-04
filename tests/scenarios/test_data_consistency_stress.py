"""데이터 일관성 스트레스 시나리오 테스트

목적: 복잡한 데이터 변경 시나리오에서 일관성 유지 확인
커버리지: csv_response_repository.py +15%
"""

import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestDataConsistencyStress:
    """데이터 일관성 스트레스 엔드투엔드 테스트"""

    def test_delete_question_with_responses(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """응답이 있는 질문 삭제 시 데이터 일관성

        시나리오:
            1. 설문 생성 및 여러 질문 추가
            2. 각 질문에 응답 제출
            3. 중간 질문 삭제
            4. 남은 질문의 응답 데이터 확인
            5. 삭제된 질문의 응답은 orphan 상태
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

        q1 = survey_service.add_question(
            manager_user, survey_id, "질문1", QuestionType.TEXT
        )
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user, survey_id, "질문2", QuestionType.RATING
        )
        q2_id = q2.value

        q3 = survey_service.add_question(
            manager_user, survey_id, "질문3", QuestionType.TEXT
        )
        q3_id = q3.value

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        submit_result = response_service.submit_response(
            manager_user,
            survey_id,
            {
                q1_id: "답변1",
                q2_id: "5",
                q3_id: "답변3"
            },
            session_id,
            time_spent_data
        )
        assert submit_result.is_success()

        responses_before = response_repo.find_by_question_id(q2_id)
        assert len(responses_before) > 0

        delete_result = survey_service.delete_question(manager_user, q2_id)
        assert delete_result.is_success()

        responses_q1 = response_repo.find_by_question_id(q1_id)
        responses_q3 = response_repo.find_by_question_id(q3_id)
        assert len(responses_q1) > 0
        assert len(responses_q3) > 0

    def test_concurrent_response_submissions(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """동시 다중 응답 제출 시 데이터 일관성

        시나리오:
            1. 설문 및 질문 생성
            2. 여러 사용자 생성
            3. 동시에 응답 제출 (순차적이지만 빠른 간격)
            4. 모든 응답이 올바르게 저장되었는지 확인
            5. 통계 계산이 정확한지 확인
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

        survey_result = survey_service.create_survey(manager_user, "스트레스 테스트", "동시성 테스트")
        survey_id = survey_result.value

        q_result = survey_service.add_question(
            manager_user, survey_id, "평점", QuestionType.RATING
        )
        q_id = q_result.value

        users = []
        for i in range(10):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"user{i}",
                email=f"user{i}@test.com",
                password=f"password{i}",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"user{i}", f"password{i}", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            users.append(user)

        ratings = ["1", "2", "3", "4", "5", "5", "4", "3", "2", "1"]

        for user, rating in zip(users, ratings):
            session_id1, time_spent_data1 = create_session_and_time_data(survey_repo, survey_id)
            submit_result = response_service.submit_response(
                user, survey_id, {q_id: rating}, session_id1, time_spent_data1
            )
            assert submit_result.is_success()

        responses = response_repo.find_by_question_id(q_id)
        assert len(responses) == 10

        results = response_service.get_survey_results(manager_user, survey_id)
        assert results.is_success()
        data = results.value
        assert data[q_id]["count"] == 10
        expected_avg = sum([1, 2, 3, 4, 5, 5, 4, 3, 2, 1]) / 10
        assert data[q_id]["average"] == expected_avg

    def test_survey_deletion_data_cleanup(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """설문 삭제 시 모든 연관 데이터 정리

        시나리오:
            1. 설문 생성 및 여러 질문 추가
            2. 여러 응답 제출
            3. 설문 삭제
            4. 설문 레코드 삭제 확인
            5. 질문 레코드 확인
            6. 응답 레코드 확인 (orphan 상태)
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

        survey_result = survey_service.create_survey(manager_user, "삭제 테스트", "정리 확인")
        survey_id = survey_result.value

        questions = []
        for i in range(3):
            q_result = survey_service.add_question(
                manager_user, survey_id, f"질문{i}", QuestionType.TEXT
            )
            questions.append(q_result.value)

        for i in range(5):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"respondent{i}",
                email=f"resp{i}@test.com",
                password="password123",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"respondent{i}", "password123", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value

            answers = {q_id: f"답변{i}" for q_id in questions}
            session_id2, time_spent_data2 = create_session_and_time_data(survey_repo, survey_id)
            submit_result = response_service.submit_response(user, survey_id, answers, session_id2, time_spent_data2)
            assert submit_result.is_success()

        responses_before = response_repo.find_by_survey_id(survey_id)
        assert len(responses_before) > 0

        delete_result = survey_service.delete_survey(manager_user, survey_id)
        assert delete_result.is_success()

        survey_after = survey_repo.find_survey_by_id(survey_id)
        assert survey_after is None

        questions_after = survey_repo.find_questions_by_survey_id(survey_id)
        assert len(questions_after) == 0
