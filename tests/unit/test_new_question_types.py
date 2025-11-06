"""새로운 질문 유형에 대한 단위 테스트입니다."""
import uuid
from datetime import datetime
import pytest
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.user import User
from domain.entities.survey import Survey
from domain.value_objects.types import QuestionType
from domain.value_objects.role import Role
from application.response_service import ResponseService
from interface.cli.validators import (
    validate_date_answer,
    validate_number_answer,
    validate_email_answer,
    validate_yes_no_answer,
    validate_scale_10_answer,
    validate_multi_select_answer,
)


class TestNewQuestionTypes:
    """새로운 질문 유형 테스트."""

    def test_date_question_type(self):
        """DATE 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="생년월일을 입력하세요",
            question_type=QuestionType.DATE,
        )
        assert question.question_type == QuestionType.DATE
        assert question.question_type.display_name == "날짜"
        assert "YYYY-MM-DD" in question.question_type.description

    def test_number_question_type(self):
        """NUMBER 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="나이를 입력하세요",
            question_type=QuestionType.NUMBER,
        )
        assert question.question_type == QuestionType.NUMBER
        assert question.question_type.display_name == "숫자"

    def test_email_question_type(self):
        """EMAIL 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="이메일을 입력하세요",
            question_type=QuestionType.EMAIL,
        )
        assert question.question_type == QuestionType.EMAIL
        assert question.question_type.display_name == "이메일"

    def test_yes_no_question_type(self):
        """YES_NO 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="동의하시나요?",
            question_type=QuestionType.YES_NO,
        )
        assert question.question_type == QuestionType.YES_NO
        assert question.question_type.display_name == "예/아니오"

    def test_scale_10_question_type(self):
        """SCALE_10 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="1-10점으로 평가해주세요",
            question_type=QuestionType.SCALE_10,
        )
        assert question.question_type == QuestionType.SCALE_10
        assert question.question_type.display_name == "10점 척도"
        assert "1-10" in question.question_type.description

    def test_multi_select_question_type(self):
        """MULTI_SELECT 질문 유형을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="관심 분야를 모두 선택하세요",
            question_type=QuestionType.MULTI_SELECT,
            options=("Python", "Java", "JavaScript", "Go"),
        )
        assert question.question_type == QuestionType.MULTI_SELECT
        assert question.question_type.display_name == "다중 선택"
        assert question.options == ("Python", "Java", "JavaScript", "Go")

    def test_multi_select_requires_options(self):
        """MULTI_SELECT 질문이 선택지를 요구하는지 테스트합니다."""
        with pytest.raises(ValueError, match="다중 선택 질문은 최소 2개 이상의 선택지가 필요합니다"):
            Question(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                text="선택하세요",
                question_type=QuestionType.MULTI_SELECT,
                options=None,
            )


class TestNewQuestionValidators:
    """새로운 질문 유형 검증기 테스트."""

    def test_validate_date_answer(self):
        """날짜 답변 검증을 테스트합니다."""
        # 유효한 날짜
        valid, error = validate_date_answer("2024-03-15")
        assert valid is True
        assert error == ""

        # 잘못된 형식
        valid, error = validate_date_answer("03/15/2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

        # 잘못된 날짜
        valid, error = validate_date_answer("2024-13-32")
        assert valid is False

    def test_validate_number_answer(self):
        """숫자 답변 검증을 테스트합니다."""
        # 정수
        valid, error = validate_number_answer("42")
        assert valid is True
        assert error == ""

        # 소수
        valid, error = validate_number_answer("3.14")
        assert valid is True
        assert error == ""

        # 음수
        valid, error = validate_number_answer("-10")
        assert valid is True
        assert error == ""

        # 잘못된 입력
        valid, error = validate_number_answer("abc")
        assert valid is False
        assert "숫자" in error

    def test_validate_email_answer(self):
        """이메일 답변 검증을 테스트합니다."""
        # 유효한 이메일
        valid, error = validate_email_answer("user@example.com")
        assert valid is True
        assert error == ""

        # 잘못된 형식
        valid, error = validate_email_answer("not-an-email")
        assert valid is False
        assert "이메일" in error

        valid, error = validate_email_answer("user@")
        assert valid is False

        valid, error = validate_email_answer("@example.com")
        assert valid is False

    def test_validate_yes_no_answer(self):
        """예/아니오 답변 검증을 테스트합니다."""
        # 유효한 답변들
        for answer in ["y", "Y", "yes", "Yes", "n", "N", "no", "No", "예", "아니오"]:
            valid, error = validate_yes_no_answer(answer)
            assert valid is True
            assert error == ""

        # 잘못된 답변
        valid, error = validate_yes_no_answer("maybe")
        assert valid is False
        assert "y (예) 또는 n (아니오)" in error

    def test_validate_scale_10_answer(self):
        """10점 척도 답변 검증을 테스트합니다."""
        # 유효한 척도
        for i in range(1, 11):
            valid, error = validate_scale_10_answer(str(i))
            assert valid is True
            assert error == ""

        # 범위 벗어남
        valid, error = validate_scale_10_answer("0")
        assert valid is False
        assert "1-10" in error

        valid, error = validate_scale_10_answer("11")
        assert valid is False
        assert "1-10" in error

        # 숫자 아님
        valid, error = validate_scale_10_answer("five")
        assert valid is False
        assert "숫자" in error

    def test_validate_multi_select_answer(self):
        """다중 선택 답변 검증을 테스트합니다."""
        options = ["옵션1", "옵션2", "옵션3"]

        # 유효한 선택
        valid, error = validate_multi_select_answer("옵션1, 옵션2", options)
        assert valid is True
        assert error == ""

        # 단일 선택도 가능
        valid, error = validate_multi_select_answer("옵션1", options)
        assert valid is True
        assert error == ""

        # 모든 옵션 선택
        valid, error = validate_multi_select_answer("옵션1, 옵션2, 옵션3", options)
        assert valid is True
        assert error == ""

        # 유효하지 않은 선택
        valid, error = validate_multi_select_answer("옵션1, 옵션4", options)
        assert valid is False
        assert "옵션4" in error

        # 빈 선택
        valid, error = validate_multi_select_answer("", options)
        assert valid is False
        assert "최소 하나" in error


class TestResponseServiceWithNewTypes:
    """새로운 질문 유형을 포함한 ResponseService 테스트."""

    def test_validate_date_answer(self, response_service, sample_survey, sample_tenant):
        """DATE 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="입사일을 입력하세요",
            question_type=QuestionType.DATE,
        )

        # 유효한 날짜
        result = response_service._validate_answer(question, "2024-03-15")
        assert result.is_success()

        # 잘못된 형식
        result = response_service._validate_answer(question, "03/15/2024")
        assert result.is_failure()

    def test_validate_number_answer(self, response_service, sample_survey):
        """NUMBER 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="연봉을 입력하세요",
            question_type=QuestionType.NUMBER,
        )

        # 유효한 숫자
        result = response_service._validate_answer(question, "50000000")
        assert result.is_success()

        result = response_service._validate_answer(question, "3.14")
        assert result.is_success()

        # 숫자가 아닌 값
        result = response_service._validate_answer(question, "많이")
        assert result.is_failure()

    def test_validate_email_answer(self, response_service, sample_survey):
        """EMAIL 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="연락처 이메일을 입력하세요",
            question_type=QuestionType.EMAIL,
        )

        # 유효한 이메일
        result = response_service._validate_answer(question, "test@example.com")
        assert result.is_success()

        # 잘못된 이메일
        result = response_service._validate_answer(question, "not-email")
        assert result.is_failure()

    def test_validate_yes_no_answer(self, response_service, sample_survey):
        """YES_NO 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="개인정보 제공에 동의하시나요?",
            question_type=QuestionType.YES_NO,
        )

        # 유효한 답변
        for answer in ["y", "n", "yes", "no", "예", "아니오"]:
            result = response_service._validate_answer(question, answer)
            assert result.is_success()

        # 잘못된 답변
        result = response_service._validate_answer(question, "maybe")
        assert result.is_failure()

    def test_validate_scale_10_answer(self, response_service, sample_survey):
        """SCALE_10 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="서비스 만족도를 10점 만점으로 평가해주세요",
            question_type=QuestionType.SCALE_10,
        )

        # 유효한 척도
        for i in range(1, 11):
            result = response_service._validate_answer(question, str(i))
            assert result.is_success()

        # 범위 벗어남
        result = response_service._validate_answer(question, "0")
        assert result.is_failure()

        result = response_service._validate_answer(question, "11")
        assert result.is_failure()

    def test_validate_multi_select_answer(self, response_service, sample_survey):
        """MULTI_SELECT 유형 답변 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="사용 중인 프로그래밍 언어를 모두 선택하세요",
            question_type=QuestionType.MULTI_SELECT,
            options=("Python", "Java", "JavaScript", "Go"),
        )

        # 유효한 선택
        result = response_service._validate_answer(question, "Python, Java")
        assert result.is_success()

        result = response_service._validate_answer(question, "Python")
        assert result.is_success()

        # 유효하지 않은 선택
        result = response_service._validate_answer(question, "Python, Ruby")
        assert result.is_failure()
        assert "Ruby" in result.error

    def test_survey_results_with_new_types(self, response_service, sample_survey, sample_admin_user, survey_repo):
        """새로운 질문 유형의 설문 결과 집계를 테스트합니다."""
        # YES_NO 질문 추가
        yes_no_q = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="재구매 의사가 있으신가요?",
            question_type=QuestionType.YES_NO,
        )
        survey_repo.save_question(yes_no_q)

        # SCALE_10 질문 추가
        scale_q = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="추천 점수를 주세요",
            question_type=QuestionType.SCALE_10,
        )
        survey_repo.save_question(scale_q)

        # NUMBER 질문 추가
        number_q = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="월 평균 사용 시간",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(number_q)

        # 응답 추가
        session_id = str(uuid.uuid4())

        # YES_NO 응답
        for answer in ["y", "y", "n", "y"]:
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=yes_no_q.id,
                answer=answer,
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=session_id,
                time_spent_seconds=5,
            ))

        # SCALE_10 응답
        for score in [8, 9, 7, 10, 8]:
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=scale_q.id,
                answer=str(score),
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=session_id,
                time_spent_seconds=3,
            ))

        # NUMBER 응답
        for hours in [100, 150, 200, 120]:
            response_service.response_repository.save(Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=number_q.id,
                answer=str(hours),
                respondent_id=str(uuid.uuid4()),
                answered_at=datetime.now(),
                session_id=session_id,
                time_spent_seconds=4,
            ))

        # 결과 조회
        result = response_service.get_survey_results(sample_admin_user, sample_survey.id)
        assert result.is_success()
        results = result.value

        # YES_NO 결과 검증
        yes_no_results = results[yes_no_q.id]
        assert yes_no_results["distribution"]["예"] == 3
        assert yes_no_results["distribution"]["아니오"] == 1

        # SCALE_10 결과 검증
        scale_results = results[scale_q.id]
        assert scale_results["average"] == 8.4  # (8+9+7+10+8)/5
        assert scale_results["count"] == 5

        # NUMBER 결과 검증
        number_results = results[number_q.id]
        assert number_results["average"] == 142.5  # (100+150+200+120)/4
        assert number_results["min"] == 100
        assert number_results["max"] == 200