import pytest
from domain.value_objects.types import QuestionType


class TestCLIQuestionTypes:
    """CLI에서 질문 타입 처리 테스트

    CLI handler에서 사용하는 소문자 문자열이 정상적으로 처리되는지 검증합니다.
    """

    def test_add_text_question(self, survey_commands, sample_manager_user):
        """TEXT 타입 질문 추가 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자

        시나리오:
            1. 설문 생성
            2. "text" 문자열로 TEXT 질문 추가
            3. 질문 추가 성공 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "텍스트 질문 테스트 설문",
            "텍스트 질문 테스트"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "의견을 자유롭게 작성해주세요",
            "text"
        )
        assert success
        assert question_id is not None

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert len(survey_data["questions"]) == 1
        assert survey_data["questions"][0]["type"] == "text"

    def test_add_rating_question(self, survey_commands, sample_manager_user):
        """RATING 타입 질문 추가 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자

        시나리오:
            1. 설문 생성
            2. "rating" 문자열로 RATING 질문 추가
            3. 질문 추가 성공 검증
            4. RATING 타입이 올바르게 저장되었는지 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "평점 질문 테스트 설문",
            "평점 질문 테스트"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "서비스 만족도를 평가해주세요",
            "rating"
        )
        assert success
        assert question_id is not None

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert len(survey_data["questions"]) == 1
        assert survey_data["questions"][0]["type"] == "rating"
        assert survey_data["questions"][0]["options"] == []

    def test_add_multiple_choice_question(self, survey_commands, sample_manager_user):
        """MULTIPLE_CHOICE 타입 질문 추가 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자

        시나리오:
            1. 설문 생성
            2. "choice" 문자열로 MULTIPLE_CHOICE 질문 추가
            3. 질문 추가 성공 검증
            4. 선택지가 올바르게 저장되었는지 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "객관식 질문 테스트 설문",
            "객관식 질문 테스트"
        )
        assert success

        options = ["매우 만족", "만족", "보통", "불만족", "매우 불만족"]
        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "전반적인 만족도는?",
            "choice",
            options
        )
        assert success
        assert question_id is not None

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert len(survey_data["questions"]) == 1
        assert survey_data["questions"][0]["type"] == "choice"
        assert survey_data["questions"][0]["options"] == options

    def test_submit_response_with_rating(self, survey_commands, sample_manager_user, sample_respondent_user):
        """RATING 질문에 응답 제출 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. RATING 질문이 있는 설문 생성
            2. 1-5 범위의 평점 응답 제출
            3. 응답 제출 성공 검증
            4. 결과 조회로 응답이 올바르게 집계되었는지 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "평점 응답 테스트 설문",
            "평점 응답 테스트"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "서비스 품질을 평가해주세요",
            "rating"
        )
        assert success

        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "5"}
        )
        assert success, f"응답 제출 실패: {error}"

        success, error, results = survey_commands.get_results(sample_manager_user, survey_id)
        assert success
        assert len(results["results"]) == 1
        assert "5" in results["results"][0]["answer_distribution"]
        assert results["results"][0]["answer_distribution"]["5"] == 1

    def test_rating_validation(self, survey_commands, sample_manager_user, sample_respondent_user):
        """RATING 값 범위 검증 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. RATING 질문이 있는 설문 생성
            2. 잘못된 범위의 값(0, 6) 제출 시도
            3. 응답 제출 실패 검증
            4. 올바른 범위의 값(1, 3, 5) 제출 성공 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "평점 검증 테스트 설문",
            "평점 검증 테스트"
        )
        assert success

        success, question_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "서비스를 평가해주세요",
            "rating"
        )
        assert success

        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "0"}
        )
        assert not success
        assert "1-5" in error or "범위" in error

        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "6"}
        )
        assert not success
        assert "1-5" in error or "범위" in error

        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {question_id: "3"}
        )
        assert success

    def test_mixed_question_types_workflow(self, survey_commands, sample_manager_user, sample_respondent_user):
        """여러 질문 타입 혼합 워크플로우 테스트

        Args:
            survey_commands: Commands 픽스처
            sample_manager_user: 설문 관리자
            sample_respondent_user: 응답자

        시나리오:
            1. 설문 생성
            2. 모든 타입의 질문 추가 (text, rating, choice)
            3. 각 타입에 맞는 응답 제출
            4. 결과 조회로 모든 응답이 올바르게 처리되었는지 검증
        """
        success, survey_id = survey_commands.create_survey(
            sample_manager_user,
            "혼합 질문 타입 테스트 설문",
            "모든 질문 타입 테스트"
        )
        assert success

        success, q1_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "의견을 작성해주세요",
            "text"
        )
        assert success

        success, q2_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "만족도를 평가해주세요",
            "rating"
        )
        assert success

        success, q3_id = survey_commands.add_question(
            sample_manager_user,
            survey_id,
            "선호하는 항목은?",
            "choice",
            ["항목A", "항목B", "항목C"]
        )
        assert success

        success, error, survey_data = survey_commands.get_survey(sample_manager_user, survey_id)
        assert success
        assert len(survey_data["questions"]) == 3
        assert survey_data["questions"][0]["type"] == "text"
        assert survey_data["questions"][1]["type"] == "rating"
        assert survey_data["questions"][2]["type"] == "choice"

        success, error = survey_commands.submit_response(
            sample_respondent_user,
            survey_id,
            {
                q1_id: "매우 좋은 서비스입니다",
                q2_id: "5",
                q3_id: "항목A"
            }
        )
        assert success, f"응답 제출 실패: {error}"

        success, error, results = survey_commands.get_results(sample_manager_user, survey_id)
        assert success
        assert len(results["results"]) == 3

        text_result = next(r for r in results["results"] if "의견을 작성해주세요" in r["question"])
        assert "매우 좋은 서비스입니다" in text_result["answer_distribution"]

        rating_result = next(r for r in results["results"] if "만족도를 평가해주세요" in r["question"])
        assert "5" in rating_result["answer_distribution"]

        choice_result = next(r for r in results["results"] if "선호하는 항목은?" in r["question"])
        assert "항목A" in choice_result["answer_distribution"]
