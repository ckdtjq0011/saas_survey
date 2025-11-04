"""고객 피드백 응답 관리 라이프사이클 시나리오 테스트

목적: Response CRUD 완전 커버 (특히 Update/Delete)
CRUD 커버리지: Response(CRUD) 집중
누락 CRUD 커버: Response Update, Response Delete (개별/스팸)
"""

import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestResponseLifecycleManagement:
    """고객 피드백 응답 관리 라이프사이클 테스트"""

    def test_customer_feedback_response_editing(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """고객 피드백 응답 수정 및 재제출

        시나리오:
            1. 쇼핑몰 고객 만족도 설문 생성
            2. 고객 응답 제출
            3. 고객이 응답 내용 확인 후 수정 요청
            4. 응답 수정 처리
            5. 수정된 응답 확인
            6. 통계에 수정 사항 반영 확인

        CRUD 커버리지:
            - Survey: C, R
            - Question: C (×3)
            - Response: C, R, U (핵심)
        """
        tenant_id = auth_service.register_tenant("온라인쇼핑몰")
        assert tenant_id is not None

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="cs_manager",
            email="cs@shop.com",
            password="Manager@2024!",
            role=Role.SURVEY_MANAGER
        )
        assert manager_result.is_success()

        manager_login = auth_service.login("cs_manager", "Manager@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "2024년 4월 고객 만족도 조사",
            "더 나은 서비스를 위한 고객님의 소중한 의견을 듣고 싶습니다"
        )
        assert survey_result.is_success()
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "전반적인 쇼핑 경험에 만족하셨나요?",
            QuestionType.RATING
        )
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user,
            survey_id,
            "가장 만족스러웠던 점은?",
            QuestionType.MULTIPLE_CHOICE,
            ["배송 속도", "상품 품질", "고객 서비스", "가격", "포장 상태"]
        )
        q2_id = q2.value

        q3 = survey_service.add_question(
            manager_user,
            survey_id,
            "개선이 필요한 부분을 알려주세요",
            QuestionType.TEXT
        )
        q3_id = q3.value

        customer_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="customer_kim",
            email="kim@customer.com",
            password="Customer@123!",
            role=Role.RESPONDENT
        )
        assert customer_result.is_success()

        customer_login = auth_service.login("customer_kim", "Customer@123!", tenant_id)
        customer_validate = auth_service.validate_session(customer_login.value)
        customer_user, _ = customer_validate.value

        session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
        initial_submit = response_service.submit_response(
            customer_user,
            survey_id,
            {
                q1_id: "3",
                q2_id: "배송 속도",
                q3_id: "포장이 조금 부실했습니다"
            },
            session_id,
            time_spent_data
        )
        assert initial_submit.is_success()

        initial_responses = response_repo.find_by_survey_id(survey_id)
        customer_q1_response = [
            r for r in initial_responses
            if r.respondent_id == customer_user.id and r.question_id == q1_id
        ][0]
        assert customer_q1_response.answer == "3"

        update_result = response_service.update_response(
            customer_user,
            customer_q1_response.id,
            "4"
        )
        assert update_result.is_success()

        updated_responses = response_repo.find_by_question_id(q1_id)
        updated_response = [r for r in updated_responses if r.id == customer_q1_response.id][0]
        assert updated_response.answer == "4"

        customer_q3_response = [
            r for r in initial_responses
            if r.respondent_id == customer_user.id and r.question_id == q3_id
        ][0]

        text_update_result = response_service.update_response(
            customer_user,
            customer_q3_response.id,
            "포장이 조금 부실했습니다. 하지만 배송은 매우 빨랐습니다!"
        )
        assert text_update_result.is_success()

        final_text_response = [
            r for r in response_repo.find_by_question_id(q3_id)
            if r.id == customer_q3_response.id
        ][0]
        assert "배송은 매우 빨랐습니다" in final_text_response.answer

        final_results = response_service.get_survey_results(manager_user, survey_id)
        assert final_results.is_success()
        final_data = final_results.value
        assert final_data[q1_id]["average"] == 4.0

    def test_spam_response_deletion(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """스팸 응답 탐지 및 삭제

        시나리오:
            1. 이벤트 피드백 설문 생성
            2. 정상 참가자들 응답 제출
            3. 스팸 응답 발견
            4. 매니저가 스팸 응답 삭제
            5. 정상 응답만 남았는지 확인
            6. 통계 재계산 확인

        CRUD 커버리지:
            - Response: C, R, D (핵심)
        """
        tenant_id = auth_service.register_tenant("이벤트기획사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="event_manager",
            email="manager@event.com",
            password="Manager@2024!",
            role=Role.SURVEY_MANAGER
        )
        manager_login = auth_service.login("event_manager", "Manager@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "컨퍼런스 만족도 조사",
            "참가해주셔서 감사합니다"
        )
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "세션 품질은 어떠셨나요?",
            QuestionType.RATING
        )
        q1_id = q1.value

        participants = []
        for i in range(5):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"participant_{i}",
                email=f"p{i}@test.com",
                password=f"Pass{i}@123!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"participant_{i}", f"Pass{i}@123!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            participants.append(user)

        ratings = ["5", "4", "5", "1", "4"]

        for participant, rating in zip(participants, ratings):
            session_id1, time_spent_data1 = create_session_and_time_data(survey_repo, survey_id)
            submit = response_service.submit_response(
                participant,
                survey_id,
                {q1_id: rating},
                session_id1,
                time_spent_data1
            )
            assert submit.is_success()

        initial_results = response_service.get_survey_results(manager_user, survey_id)
        initial_avg = initial_results.value[q1_id]["average"]
        assert initial_avg == 3.8

        spam_responses = [
            r for r in response_repo.find_by_question_id(q1_id)
            if r.respondent_id == participants[3].id
        ]
        spam_response_id = spam_responses[0].id

        delete_result = response_service.delete_response(manager_user, spam_response_id)
        assert delete_result.is_success()

        remaining_responses = response_repo.find_by_question_id(q1_id)
        assert len(remaining_responses) == 4
        assert not any(r.id == spam_response_id for r in remaining_responses)

        final_results = response_service.get_survey_results(manager_user, survey_id)
        final_avg = final_results.value[q1_id]["average"]
        assert final_avg == 4.5
        assert final_results.value[q1_id]["count"] == 4

    def test_response_modification_statistics(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """응답 수정 후 통계 재집계 정확성 확인

        시나리오:
            1. 설문 생성 및 다수 응답 수집
            2. 초기 통계 확인
            3. 여러 응답 수정
            4. 통계가 정확히 업데이트되었는지 확인
            5. 일부 응답 삭제
            6. 최종 통계 재확인

        CRUD 커버리지:
            - Response: C (다수), R, U (다수), D (다수)
            - 통계 정확성 검증
        """
        tenant_id = auth_service.register_tenant("리서치회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="researcher",
            email="researcher@research.com",
            password="Research@2024!",
            role=Role.SURVEY_MANAGER
        )
        manager_login = auth_service.login("researcher", "Research@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "제품 만족도 조사",
            "신제품 개선을 위한 조사"
        )
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "제품에 만족하십니까?",
            QuestionType.RATING
        )
        q1_id = q1.value

        respondents = []
        for i in range(8):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"tester_{i}",
                email=f"tester{i}@test.com",
                password=f"Test{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"tester_{i}", f"Test{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            respondents.append(user)

        initial_ratings = ["3", "4", "2", "5", "3", "4", "3", "5"]

        for respondent, rating in zip(respondents, initial_ratings):
            session_id2, time_spent_data2 = create_session_and_time_data(survey_repo, survey_id)
            submit = response_service.submit_response(
                respondent,
                survey_id,
                {q1_id: rating},
                session_id2,
                time_spent_data2
            )
            assert submit.is_success()

        initial_results = response_service.get_survey_results(manager_user, survey_id)
        initial_data = initial_results.value[q1_id]
        expected_initial_avg = round(sum([3, 4, 2, 5, 3, 4, 3, 5]) / 8, 2)
        assert initial_data["average"] == expected_initial_avg
        assert initial_data["count"] == 8

        all_responses = response_repo.find_by_question_id(q1_id)

        responses_to_modify = [
            (r, "4") for r in all_responses
            if r.respondent_id in [respondents[0].id, respondents[2].id, respondents[4].id]
        ]

        for response, new_rating in responses_to_modify:
            update_result = response_service.update_response(
                [r for r in respondents if r.id == response.respondent_id][0],
                response.id,
                new_rating
            )
            assert update_result.is_success()

        after_update_results = response_service.get_survey_results(manager_user, survey_id)
        after_update_data = after_update_results.value[q1_id]
        expected_after_update_avg = round(sum([4, 4, 4, 5, 4, 4, 3, 5]) / 8, 2)
        assert after_update_data["average"] == expected_after_update_avg

        responses_to_delete = [
            r for r in response_repo.find_by_question_id(q1_id)
            if r.respondent_id in [respondents[6].id, respondents[7].id]
        ]

        for response in responses_to_delete:
            delete_result = response_service.delete_response(
                manager_user,
                response.id
            )
            assert delete_result.is_success()

        final_results = response_service.get_survey_results(manager_user, survey_id)
        final_data = final_results.value[q1_id]
        assert final_data["count"] == 6
        expected_final_avg = round(sum([4, 4, 4, 5, 4, 4]) / 6, 2)
        assert final_data["average"] == expected_final_avg
