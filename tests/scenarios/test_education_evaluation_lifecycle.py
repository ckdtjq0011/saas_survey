"""대학교 강의평가 전체 라이프사이클 시나리오 테스트

목적: 실제 교육기관 환경에서의 강의평가 전체 프로세스 시뮬레이션
CRUD 커버리지: Survey(CRUD), Question(CRUD), Response(CRUD), User(CRUD)
누락 CRUD 커버: Response Update/Delete, Question Update
"""

import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType
from tests.conftest import create_session_and_time_data


class TestEducationEvaluationLifecycle:
    """대학교 강의평가 전체 라이프사이클 엔드투엔드 테스트"""

    def test_university_course_evaluation_full_cycle(
        self, auth_service, survey_service, response_service, response_repo, survey_repo
    ):
        """대학교 강의평가 전체 라이프사이클 (전체 CRUD 통합)

        시나리오:
            1. 테넌트 및 관리자 생성 (Tenant C, User C)
            2. 학기 설문 생성 (Survey C)
            3. 평가 항목 추가 (Question C×5)
            4. 학생 계정 대량 생성 (User C×10)
            5. 학생들 평가 제출 (Response C×50)
            6. 중간 집계 조회 (Response R, Survey R)
            7. 질문 오타 발견 및 수정 (Question U)
            8. 학생 평가 수정 요청 처리 (Response U)
            9. 중복 응답 삭제 (Response D)
            10. 평가 기간 연장으로 설문 설명 수정 (Survey U)
            11. 부적절 질문 삭제 (Question D)
            12. 최종 결과 조회 및 통계 (Response R)
            13. 졸업생 계정 삭제 (User D)
            14. 설문 아카이빙 (Survey D)

        CRUD 커버리지:
            - Tenant: C, R
            - User: C (교수, 학생×10), R, D (졸업생)
            - Survey: C, R, U (설명), D
            - Question: C (×5), R, U (오타 수정), D (부적절 질문)
            - Response: C (×50), R, U (재평가), D (중복)
            - Session: C, R, D
        """
        tenant_id = auth_service.register_tenant("서울대학교")
        assert tenant_id is not None

        admin_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="admin_kim",
            email="admin@snu.ac.kr",
            password="Admin@2024!",
            role=Role.TENANT_ADMIN
        )
        assert admin_result.is_success()

        professor_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="prof_lee",
            email="prof.lee@snu.ac.kr",
            password="Prof@2024!",
            role=Role.SURVEY_MANAGER
        )
        assert professor_result.is_success()

        prof_login = auth_service.login("prof_lee", "Prof@2024!", tenant_id)
        assert prof_login.is_success()
        prof_validate = auth_service.validate_session(prof_login.value)
        prof_user, _ = prof_validate.value

        survey_result = survey_service.create_survey(
            prof_user,
            "2024-1학기 소프트웨어공학 강의평가",
            "수업 개선을 위한 익명 평가입니다. 솔직한 의견 부탁드립니다."
        )
        assert survey_result.is_success()
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            prof_user,
            survey_id,
            "강의 내용에 전반적으로 만족하십니까?",
            QuestionType.RATING
        )
        assert q1.is_success()
        q1_id = q1.value

        q2 = survey_service.add_question(
            prof_user,
            survey_id,
            "교수님의 강의 전달력은 어떠셨습니까?",
            QuestionType.RATING
        )
        assert q2.is_success()
        q2_id = q2.value

        q3 = survey_service.add_question(
            prof_user,
            survey_id,
            "가장 도움이 된 부분은 무엇입니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["이론 강의", "실습 과제", "프로젝트", "팀 활동", "교재"]
        )
        assert q3.is_success()
        q3_id = q3.value

        q4 = survey_service.add_question(
            prof_user,
            survey_id,
            "개선이 필요한 부분을 자유롭게 작성해주세요",
            QuestionType.TEXT
        )
        assert q4.is_success()
        q4_id = q4.value

        q5 = survey_service.add_question(
            prof_user,
            survey_id,
            "교수님의 인격은 어떠했습니까?",
            QuestionType.RATING
        )
        assert q5.is_success()
        q5_id = q5.value

        students = []
        for i in range(10):
            student_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"student_{i:03d}",
                email=f"s{2024000+i}@snu.ac.kr",
                password=f"Student{i}@2024!",
                role=Role.RESPONDENT
            )
            assert student_result.is_success()

            student_login = auth_service.login(
                f"student_{i:03d}",
                f"Student{i}@2024!",
                tenant_id
            )
            assert student_login.is_success()
            student_validate = auth_service.validate_session(student_login.value)
            student_user, _ = student_validate.value
            students.append(student_user)

        evaluation_data = [
            ("5", "5", "실습 과제", "실습이 매우 도움되었습니다", "5"),
            ("4", "5", "프로젝트", "프로젝트가 실무에 가까웠습니다", "4"),
            ("5", "4", "이론 강의", "이론이 체계적이었습니다", "5"),
            ("3", "3", "팀 활동", "팀 활동이 조금 어려웠습니다", "3"),
            ("4", "4", "교재", "교재가 이해하기 쉬웠습니다", "4"),
            ("5", "5", "실습 과제", "과제가 흥미로웠습니다", "5"),
            ("4", "4", "프로젝트", "프로젝트 주제가 좋았습니다", "4"),
            ("5", "5", "이론 강의", "강의가 명쾌했습니다", "5"),
            ("3", "4", "실습 과제", "과제 난이도가 적절했습니다", "3"),
            ("4", "4", "팀 활동", "팀 협업을 배웠습니다", "4"),
        ]

        submitted_response_ids = []
        for student, (r1, r2, mc, txt, r5) in zip(students, evaluation_data):
            session_id, time_spent_data = create_session_and_time_data(survey_repo, survey_id)
            submit_result = response_service.submit_response(
                student,
                survey_id,
                {
                    q1_id: r1,
                    q2_id: r2,
                    q3_id: mc,
                    q4_id: txt,
                    q5_id: r5
                },
                session_id,
                time_spent_data
            )
            assert submit_result.is_success()

        mid_results = response_service.get_survey_results(prof_user, survey_id)
        assert mid_results.is_success()
        mid_data = mid_results.value
        assert mid_data[q1_id]["count"] == 10
        expected_avg_q1 = sum([5, 4, 5, 3, 4, 5, 4, 5, 3, 4]) / 10
        assert mid_data[q1_id]["average"] == expected_avg_q1

        typo_fix = survey_service.update_question(
            prof_user,
            q2_id,
            text="교수님의 강의 전달력은 어떠하셨습니까?"
        )
        assert typo_fix.is_success()

        updated_survey = survey_service.get_survey(prof_user, survey_id)
        assert updated_survey.is_success()
        updated_q2 = [q for q in updated_survey.value.questions if q.id == q2_id][0]
        assert updated_q2.text == "교수님의 강의 전달력은 어떠하셨습니까?"

        student_0_responses = response_repo.find_by_survey_id(survey_id)
        student_0_q1_response = [
            r for r in student_0_responses
            if r.respondent_id == students[0].id and r.question_id == q1_id
        ][0]

        revision_result = response_service.update_response(
            students[0],
            student_0_q1_response.id,
            "4"
        )
        assert revision_result.is_success()

        revised_responses = response_repo.find_by_question_id(q1_id)
        revised_answer = [
            r for r in revised_responses if r.id == student_0_q1_response.id
        ][0]
        assert revised_answer.answer == "4"

        student_9_responses = [
            r for r in response_repo.find_by_survey_id(survey_id)
            if r.respondent_id == students[9].id and r.question_id == q1_id
        ]

        duplicate_response_id = student_9_responses[0].id
        delete_result = response_service.delete_response(students[9], duplicate_response_id)
        assert delete_result.is_success()

        remaining_responses = response_repo.find_by_question_id(q1_id)
        assert len(remaining_responses) == 9
        assert not any(r.id == duplicate_response_id for r in remaining_responses)

        extend_result = survey_service.update_survey(
            prof_user,
            survey_id,
            description="수업 개선을 위한 익명 평가입니다. 평가 기간이 2일 연장되었습니다. 솔직한 의견 부탁드립니다."
        )
        assert extend_result.is_success()

        extended_survey = survey_service.get_survey(prof_user, survey_id)
        assert "2일 연장" in extended_survey.value.description

        inappropriate_delete = survey_service.delete_question(prof_user, q5_id)
        assert inappropriate_delete.is_success()

        final_survey = survey_service.get_survey(prof_user, survey_id)
        assert final_survey.is_success()
        assert len(final_survey.value.questions) == 4
        assert not any(q.id == q5_id for q in final_survey.value.questions)

        final_results = response_service.get_survey_results(prof_user, survey_id)
        assert final_results.is_success()
        final_data = final_results.value
        assert q1_id in final_data
        assert q2_id in final_data
        assert q3_id in final_data
        assert q4_id in final_data
        assert q5_id not in final_data

        assert final_data[q1_id]["count"] == 9
        assert final_data[q3_id]["distribution"]["실습 과제"] == 3

        admin_login = auth_service.login("admin_kim", "Admin@2024!", tenant_id)
        admin_validate = auth_service.validate_session(admin_login.value)
        admin_user, _ = admin_validate.value

        graduate_student = students[-1]
        delete_user_result = auth_service.delete_user(admin_user, graduate_student.id)
        assert delete_user_result.is_success()

        archive_result = survey_service.delete_survey(prof_user, survey_id)
        assert archive_result.is_success()

        archived_check = survey_service.get_survey(prof_user, survey_id)
        assert archived_check.is_failure()
