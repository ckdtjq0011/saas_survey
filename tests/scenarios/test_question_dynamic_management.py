"""설문 진행 중 질문 동적 관리 시나리오 테스트

목적: Question CRUD 완전 커버 (특히 Update)
CRUD 커버리지: Question(CRUD) 집중
누락 CRUD 커버: Question Update (내용, 옵션)
"""

import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestQuestionDynamicManagement:
    """설문 진행 중 질문 동적 관리 테스트"""

    def test_question_text_and_options_modification(
        self, auth_service, survey_service, response_service
    ):
        """질문 내용 및 옵션 수정

        시나리오:
            1. 제품 피드백 설문 생성
            2. 여러 유형의 질문 추가
            3. 초기 응답 수집
            4. 질문 오타 발견 및 수정 (TEXT 질문)
            5. 객관식 선택지 추가 필요 (MULTIPLE_CHOICE 질문)
            6. 수정된 질문으로 신규 응답 수집
            7. 모든 응답이 정상 처리되는지 확인

        CRUD 커버리지:
            - Question: C, R, U (텍스트, 옵션) - 핵심
            - Response: C, R
        """
        tenant_id = auth_service.register_tenant("전자제품회사")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="product_manager",
            email="pm@electronics.com",
            password="PM@2024!",
            role=Role.SURVEY_MANAGER
        )
        manager_login = auth_service.login("product_manager", "PM@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "신제품 베타 피드백",
            "베타 테스터 여러분의 솔직한 피드백을 부탁드립니다"
        )
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "제품의 전반적인 완성도는 어떻습니까?",
            QuestionType.RATING
        )
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user,
            survey_id,
            "가장 유용한 기능은 무엇입니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["기능A", "기능B", "기능C"]
        )
        q2_id = q2.value

        q3 = survey_service.add_question(
            manager_user,
            survey_id,
            "추가로 원하시는 기눙을 적어주세요",
            QuestionType.TEXT
        )
        q3_id = q3.value

        users = []
        for i in range(3):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"beta_tester_{i}",
                email=f"tester{i}@test.com",
                password=f"Tester{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"beta_tester_{i}", f"Tester{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            users.append(user)

        initial_responses_data = [
            ("4", "기능A", "다크모드가 필요합니다"),
            ("5", "기능B", "알림 기능 추가 바랍니다"),
            ("3", "기능C", "UI 개선이 필요합니다"),
        ]

        for user, (rating, choice, text) in zip(users, initial_responses_data):
            submit = response_service.submit_response(
                user,
                survey_id,
                {q1_id: rating, q2_id: choice, q3_id: text}
            )
            assert submit.is_success()

        initial_results = response_service.get_survey_results(manager_user, survey_id)
        assert initial_results.is_success()
        assert initial_results.value[q3_id]["count"] == 3

        typo_fix_result = survey_service.update_question(
            manager_user,
            q3_id,
            text="추가로 원하시는 기능을 적어주세요"
        )
        assert typo_fix_result.is_success()

        updated_survey = survey_service.get_survey(manager_user, survey_id)
        assert updated_survey.is_success()
        updated_q3 = [q for q in updated_survey.value.questions if q.id == q3_id][0]
        assert updated_q3.text == "추가로 원하시는 기능을 적어주세요"
        assert "기눙" not in updated_q3.text

        options_add_result = survey_service.update_question(
            manager_user,
            q2_id,
            options=["기능A", "기능B", "기능C", "기능D", "기능E"]
        )
        assert options_add_result.is_success()

        updated_survey2 = survey_service.get_survey(manager_user, survey_id)
        updated_q2 = [q for q in updated_survey2.value.questions if q.id == q2_id][0]
        assert len(updated_q2.options) == 5
        assert "기능D" in updated_q2.options
        assert "기능E" in updated_q2.options

        new_users = []
        for i in range(2):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"new_tester_{i}",
                email=f"new{i}@test.com",
                password=f"New{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"new_tester_{i}", f"New{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            new_users.append(user)

        new_responses_data = [
            ("5", "기능D", "새 기능D가 좋습니다"),
            ("4", "기능E", "기능E도 훌륭합니다"),
        ]

        for user, (rating, choice, text) in zip(new_users, new_responses_data):
            submit = response_service.submit_response(
                user,
                survey_id,
                {q1_id: rating, q2_id: choice, q3_id: text}
            )
            assert submit.is_success()

        final_results = response_service.get_survey_results(manager_user, survey_id)
        assert final_results.is_success()
        final_data = final_results.value
        assert final_data[q1_id]["count"] == 5
        assert final_data[q2_id]["count"] == 5
        assert "기능D" in final_data[q2_id]["distribution"]
        assert "기능E" in final_data[q2_id]["distribution"]

    def test_question_wording_improvement(
        self, auth_service, survey_service, response_service
    ):
        """질문 문구 개선 프로세스

        시나리오:
            1. 직원 만족도 설문 생성
            2. 질문 초안 작성
            3. 일부 응답 수집 후 문구가 모호하다는 피드백 받음
            4. 질문 문구를 더 명확하게 수정
            5. 수정 후에도 기존 응답 유지 확인
            6. 신규 응답이 정상 처리되는지 확인

        CRUD 커버리지:
            - Question: C, R, U (문구 개선) - 핵심
            - Response: C, R (수정 전후)
        """
        tenant_id = auth_service.register_tenant("IT스타트업")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="hr_manager",
            email="hr@startup.com",
            password="HR@2024!",
            role=Role.SURVEY_MANAGER
        )
        manager_login = auth_service.login("hr_manager", "HR@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "2024 Q2 직원 만족도 조사",
            "회사 문화 개선을 위한 설문입니다"
        )
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "회사가 좋나요?",
            QuestionType.RATING
        )
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user,
            survey_id,
            "무엇을 개선하면 좋을까요?",
            QuestionType.TEXT
        )
        q2_id = q2.value

        early_employees = []
        for i in range(3):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"employee_{i}",
                email=f"emp{i}@startup.com",
                password=f"Emp{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"employee_{i}", f"Emp{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            early_employees.append(user)

        early_responses = [
            ("4", "질문이 모호합니다"),
            ("3", "구체적인 질문이 필요합니다"),
            ("5", "좋습니다"),
        ]

        for user, (rating, text) in zip(early_employees, early_responses):
            submit = response_service.submit_response(
                user,
                survey_id,
                {q1_id: rating, q2_id: text}
            )
            assert submit.is_success()

        before_update_results = response_service.get_survey_results(manager_user, survey_id)
        before_count = before_update_results.value[q1_id]["count"]
        assert before_count == 3

        improve_q1_result = survey_service.update_question(
            manager_user,
            q1_id,
            text="현재 회사의 근무 환경과 복지에 대해 전반적으로 만족하십니까?"
        )
        assert improve_q1_result.is_success()

        improve_q2_result = survey_service.update_question(
            manager_user,
            q2_id,
            text="근무 환경, 복지, 업무 프로세스 중 가장 개선이 필요한 부분과 구체적인 개선 방안을 작성해주세요"
        )
        assert improve_q2_result.is_success()

        improved_survey = survey_service.get_survey(manager_user, survey_id)
        improved_q1 = [q for q in improved_survey.value.questions if q.id == q1_id][0]
        improved_q2 = [q for q in improved_survey.value.questions if q.id == q2_id][0]
        assert "근무 환경과 복지" in improved_q1.text
        assert "구체적인 개선 방안" in improved_q2.text

        after_update_results = response_service.get_survey_results(manager_user, survey_id)
        after_count = after_update_results.value[q1_id]["count"]
        assert after_count == 3

        late_employees = []
        for i in range(2):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"late_employee_{i}",
                email=f"late{i}@startup.com",
                password=f"Late{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"late_employee_{i}", f"Late{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            late_employees.append(user)

        late_responses = [
            ("5", "재택근무 확대가 필요합니다. 주 3일 이상 재택을 원합니다."),
            ("4", "점심 식대 지원 확대와 건강검진 항목 추가가 필요합니다."),
        ]

        for user, (rating, text) in zip(late_employees, late_responses):
            submit = response_service.submit_response(
                user,
                survey_id,
                {q1_id: rating, q2_id: text}
            )
            assert submit.is_success()

        final_results = response_service.get_survey_results(manager_user, survey_id)
        final_data = final_results.value
        assert final_data[q1_id]["count"] == 5
        assert final_data[q2_id]["count"] == 5
        expected_avg = (4 + 3 + 5 + 5 + 4) / 5
        assert final_data[q1_id]["average"] == expected_avg

    def test_question_deletion_orphan_handling(
        self, auth_service, survey_service, response_service, response_repo
    ):
        """질문 삭제 후 응답 처리 (orphan response)

        시나리오:
            1. 다양한 질문이 있는 설문 생성
            2. 모든 질문에 대한 응답 수집
            3. 특정 질문 삭제 결정
            4. 질문 삭제
            5. 삭제된 질문은 설문에서 제외 확인
            6. 삭제된 질문의 응답은 orphan 상태로 남음
            7. 나머지 질문의 응답은 정상 유지 확인
            8. 통계는 남은 질문만 포함

        CRUD 커버리지:
            - Question: C, R, D - 핵심
            - Response: C, R (orphan 상태)
        """
        tenant_id = auth_service.register_tenant("마케팅에이전시")

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="marketing_lead",
            email="lead@agency.com",
            password="Lead@2024!",
            role=Role.SURVEY_MANAGER
        )
        manager_login = auth_service.login("marketing_lead", "Lead@2024!", tenant_id)
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "캠페인 효과 측정",
            "최근 광고 캠페인에 대한 고객 반응 조사"
        )
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "광고를 보셨습니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["예", "아니오"]
        )
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user,
            survey_id,
            "광고가 기억에 남습니까?",
            QuestionType.RATING
        )
        q2_id = q2.value

        q3 = survey_service.add_question(
            manager_user,
            survey_id,
            "광고 모델의 이름을 아십니까?",
            QuestionType.TEXT
        )
        q3_id = q3.value

        q4 = survey_service.add_question(
            manager_user,
            survey_id,
            "제품 구매 의향이 있습니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["있음", "없음", "고민중"]
        )
        q4_id = q4.value

        respondents = []
        for i in range(5):
            user_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"consumer_{i}",
                email=f"consumer{i}@test.com",
                password=f"Consumer{i}@2024!",
                role=Role.RESPONDENT
            )
            user_login = auth_service.login(f"consumer_{i}", f"Consumer{i}@2024!", tenant_id)
            user_validate = auth_service.validate_session(user_login.value)
            user, _ = user_validate.value
            respondents.append(user)

        responses_data = [
            ("예", "5", "김OO", "있음"),
            ("예", "4", "잘 모름", "고민중"),
            ("아니오", "1", "모름", "없음"),
            ("예", "5", "김OO", "있음"),
            ("예", "3", "잘 모름", "고민중"),
        ]

        for respondent, (q1_ans, q2_ans, q3_ans, q4_ans) in zip(respondents, responses_data):
            submit = response_service.submit_response(
                respondent,
                survey_id,
                {q1_id: q1_ans, q2_id: q2_ans, q3_id: q3_ans, q4_id: q4_ans}
            )
            assert submit.is_success()

        before_delete_results = response_service.get_survey_results(manager_user, survey_id)
        assert before_delete_results.is_success()
        assert q3_id in before_delete_results.value
        assert before_delete_results.value[q3_id]["count"] == 5

        before_delete_q3_responses = response_repo.find_by_question_id(q3_id)
        assert len(before_delete_q3_responses) == 5

        delete_result = survey_service.delete_question(manager_user, q3_id)
        assert delete_result.is_success()

        after_delete_survey = survey_service.get_survey(manager_user, survey_id)
        assert after_delete_survey.is_success()
        question_ids = [q.id for q in after_delete_survey.value.questions]
        assert q3_id not in question_ids
        assert len(question_ids) == 3

        after_delete_q3_responses = response_repo.find_by_question_id(q3_id)
        assert len(after_delete_q3_responses) == 5

        after_delete_results = response_service.get_survey_results(manager_user, survey_id)
        assert after_delete_results.is_success()
        assert q3_id not in after_delete_results.value

        assert q1_id in after_delete_results.value
        assert q2_id in after_delete_results.value
        assert q4_id in after_delete_results.value
        assert after_delete_results.value[q1_id]["count"] == 5
        assert after_delete_results.value[q2_id]["count"] == 5
        assert after_delete_results.value[q4_id]["count"] == 5
