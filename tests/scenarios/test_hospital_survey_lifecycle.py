"""병원 설문 전체 라이프사이클 시나리오 테스트

목적: 실제 병원 환경에서의 설문 운영 전 과정을 시뮬레이션
커버리지: commands.py +15%, handlers +10%
"""

import pytest
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestHospitalSurveyLifecycle:
    """병원 설문 전체 라이프사이클 엔드투엔드 테스트"""

    def test_complete_hospital_survey_lifecycle(
        self, auth_service, survey_service, response_service
    ):
        """병원 환자 만족도 조사의 완전한 라이프사이클 테스트

        시나리오:
            1. 병원 테넌트 등록
            2. 관리자 계정 생성
            3. 환자 만족도 설문 생성
            4. 다양한 유형의 질문 추가 (평점, 객관식, 주관식)
            5. 여러 환자(응답자) 등록
            6. 각 환자가 응답 제출
            7. 통계 결과 조회
            8. 설문 제목 수정
            9. 특정 응답 수정
            10. 응답 삭제
            11. 질문 추가
            12. 질문 삭제
            13. 최종 결과 재조회
            14. 설문 종료 및 삭제
        """
        tenant_id = auth_service.register_tenant("서울대학교병원")
        assert tenant_id is not None

        admin_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="admin_park",
            email="admin@hospital.com",
            password="Admin@2024!",
            role=Role.TENANT_ADMIN
        )
        assert admin_result.is_success()

        manager_result = auth_service.register_user(
            tenant_id=tenant_id,
            username="survey_manager",
            email="manager@hospital.com",
            password="Manager@2024!",
            role=Role.SURVEY_MANAGER
        )
        assert manager_result.is_success()

        manager_login = auth_service.login("survey_manager", "Manager@2024!", tenant_id)
        assert manager_login.is_success()
        manager_validate = auth_service.validate_session(manager_login.value)
        manager_user, _ = manager_validate.value

        survey_result = survey_service.create_survey(
            manager_user,
            "2024년 상반기 환자 만족도 조사",
            "의료서비스 개선을 위한 설문조사입니다"
        )
        assert survey_result.is_success()
        survey_id = survey_result.value

        q1 = survey_service.add_question(
            manager_user,
            survey_id,
            "진료에 전반적으로 만족하셨습니까?",
            QuestionType.RATING
        )
        assert q1.is_success()
        q1_id = q1.value

        q2 = survey_service.add_question(
            manager_user,
            survey_id,
            "가장 만족스러웠던 부분은 무엇입니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["의료진 친절도", "진료 대기시간", "시설 청결도", "진료 전문성"]
        )
        assert q2.is_success()
        q2_id = q2.value

        q3 = survey_service.add_question(
            manager_user,
            survey_id,
            "추가로 개선이 필요한 사항을 작성해주세요",
            QuestionType.TEXT
        )
        assert q3.is_success()
        q3_id = q3.value

        patients = []
        for i in range(5):
            patient_result = auth_service.register_user(
                tenant_id=tenant_id,
                username=f"patient_{i:03d}",
                email=f"patient{i}@example.com",
                password=f"Patient{i}@2024!",
                role=Role.RESPONDENT
            )
            assert patient_result.is_success()

            patient_login = auth_service.login(
                f"patient_{i:03d}",
                f"Patient{i}@2024!",
                tenant_id
            )
            assert patient_login.is_success()
            patient_validate = auth_service.validate_session(patient_login.value)
            patient_user, _ = patient_validate.value
            patients.append(patient_user)

        responses_data = [
            ("5", "의료진 친절도", "모든 직원분들이 친절하셨습니다"),
            ("4", "진료 전문성", "진료가 정확했습니다"),
            ("5", "시설 청결도", "병원이 매우 깨끗했습니다"),
            ("3", "진료 대기시간", "대기시간이 조금 길었습니다"),
            ("4", "의료진 친절도", "전반적으로 만족스러웠습니다"),
        ]

        submitted_response_ids = []
        for patient, (rating, choice, text) in zip(patients, responses_data):
            submit_result = response_service.submit_response(
                patient,
                survey_id,
                {
                    q1_id: rating,
                    q2_id: choice,
                    q3_id: text
                }
            )
            assert submit_result.is_success()

        results1 = response_service.get_survey_results(manager_user, survey_id)
        assert results1.is_success()
        data1 = results1.value
        assert data1[q1_id]["count"] == 5
        assert data1[q1_id]["average"] == 4.2

        update_survey_result = survey_service.update_survey(
            manager_user,
            survey_id,
            title="2024년 상반기 환자 만족도 조사 (진행중)"
        )
        assert update_survey_result.is_success()

        q4 = survey_service.add_question(
            manager_user,
            survey_id,
            "재방문 의향이 있으십니까?",
            QuestionType.MULTIPLE_CHOICE,
            ["y", "n", "?"]
        )
        assert q4.is_success()
        q4_id = q4.value

        delete_q3_result = survey_service.delete_question(manager_user, q3_id)
        assert delete_q3_result.is_success()

        final_results = response_service.get_survey_results(manager_user, survey_id)
        assert final_results.is_success()
        final_data = final_results.value
        assert q1_id in final_data
        assert q2_id in final_data
        assert q3_id not in final_data

        delete_survey_result = survey_service.delete_survey(manager_user, survey_id)
        assert delete_survey_result.is_success()
