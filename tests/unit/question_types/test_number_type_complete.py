"""완벽한 NUMBER 질문 유형 테스트 - 70개 시나리오"""
import uuid
import math
from decimal import Decimal
import pytest
from domain.entities.question import Question
from domain.entities.response import Response
from domain.value_objects.types import QuestionType
from application.response_service import ResponseService
from interface.cli.validators import validate_number_answer


class TestNumberFormatValidation:
    """숫자 형식 검증 테스트 - 20개"""

    def test_valid_positive_integer(self):
        """양수 정수를 테스트합니다."""
        valid, error = validate_number_answer("42")
        assert valid is True
        assert error == ""

        valid, error = validate_number_answer("1000")
        assert valid is True

    def test_valid_negative_integer(self):
        """음수 정수를 테스트합니다."""
        valid, error = validate_number_answer("-10")
        assert valid is True

        valid, error = validate_number_answer("-999")
        assert valid is True

    def test_valid_decimal_numbers(self):
        """소수를 테스트합니다."""
        valid, error = validate_number_answer("3.14")
        assert valid is True

        valid, error = validate_number_answer("0.5")
        assert valid is True

    def test_valid_zero(self):
        """0을 테스트합니다."""
        valid, error = validate_number_answer("0")
        assert valid is True

        valid, error = validate_number_answer("0.0")
        assert valid is True

        valid, error = validate_number_answer("-0")
        assert valid is True

    def test_valid_leading_zeros(self):
        """선행 0을 테스트합니다."""
        valid, error = validate_number_answer("007")
        assert valid is True

        valid, error = validate_number_answer("00.5")
        assert valid is True

    def test_valid_trailing_zeros(self):
        """후행 0을 테스트합니다."""
        valid, error = validate_number_answer("10.00")
        assert valid is True

        valid, error = validate_number_answer("5.500")
        assert valid is True

    def test_valid_very_small_decimals(self):
        """매우 작은 소수를 테스트합니다."""
        valid, error = validate_number_answer("0.000001")
        assert valid is True

        valid, error = validate_number_answer("0.0000000001")
        assert valid is True

    def test_valid_scientific_notation_positive_exponent(self):
        """양수 지수 과학적 표기법을 테스트합니다."""
        valid, error = validate_number_answer("1e10")
        assert valid is True

        valid, error = validate_number_answer("2E+3")
        assert valid is True

    def test_valid_scientific_notation_negative_exponent(self):
        """음수 지수 과학적 표기법을 테스트합니다."""
        valid, error = validate_number_answer("3.14e-5")
        assert valid is True

        valid, error = validate_number_answer("1E-10")
        assert valid is True

    def test_valid_large_numbers(self):
        """큰 숫자를 테스트합니다."""
        valid, error = validate_number_answer("999999999999")
        assert valid is True

        valid, error = validate_number_answer("1234567890123456")
        assert valid is True

    def test_valid_negative_decimals(self):
        """음수 소수를 테스트합니다."""
        valid, error = validate_number_answer("-3.14")
        assert valid is True

        valid, error = validate_number_answer("-0.001")
        assert valid is True

    def test_valid_positive_with_explicit_sign(self):
        """명시적 + 부호를 테스트합니다."""
        valid, error = validate_number_answer("+42")
        assert valid is True

        valid, error = validate_number_answer("+3.14")
        assert valid is True

    def test_invalid_text_strings(self):
        """텍스트 문자열이 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("abc")
        assert valid is False
        assert "숫자" in error

        valid, error = validate_number_answer("not a number")
        assert valid is False

    def test_invalid_numbers_with_units(self):
        """단위가 포함된 숫자가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("42kg")
        assert valid is False

        valid, error = validate_number_answer("100%")
        assert valid is False

        valid, error = validate_number_answer("$500")
        assert valid is False

    def test_invalid_comma_separators(self):
        """쉼표 구분자가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("1,000")
        assert valid is False

        valid, error = validate_number_answer("1,000,000.50")
        assert valid is False

    def test_invalid_multiple_decimal_points(self):
        """다중 소수점이 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("3.14.15")
        assert valid is False

    def test_invalid_multiple_signs(self):
        """다중 부호가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("--5")
        assert valid is False

        valid, error = validate_number_answer("-5-")
        assert valid is False

        valid, error = validate_number_answer("+-5")
        assert valid is False

    def test_invalid_expressions(self):
        """수식이 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("5+3")
        assert valid is False

        valid, error = validate_number_answer("10-2")
        assert valid is False

        valid, error = validate_number_answer("2*5")
        assert valid is False

    def test_invalid_fractions(self):
        """분수가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("1/2")
        assert valid is False

        valid, error = validate_number_answer("3/4")
        assert valid is False

    def test_invalid_number_words(self):
        """숫자 단어가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("forty-two")
        assert valid is False

        valid, error = validate_number_answer("one hundred")
        assert valid is False

        valid, error = validate_number_answer("천")
        assert valid is False


class TestNumberSpecialValues:
    """특수 숫자 값 테스트 - 15개"""

    def test_positive_zero_vs_negative_zero(self):
        """양수 0과 음수 0을 테스트합니다."""
        valid, error = validate_number_answer("+0")
        assert valid is True

        valid, error = validate_number_answer("-0")
        assert valid is True

        valid, error = validate_number_answer("0.0")
        assert valid is True

        valid, error = validate_number_answer("-0.0")
        assert valid is True

    def test_very_large_exponents(self):
        """매우 큰 지수를 테스트합니다."""
        valid, error = validate_number_answer("1e308")
        assert valid is True

        valid, error = validate_number_answer("1.7e308")
        assert valid is True

    def test_very_small_exponents(self):
        """매우 작은 지수를 테스트합니다."""
        valid, error = validate_number_answer("1e-308")
        assert valid is True

        valid, error = validate_number_answer("2.2e-308")
        assert valid is True

    def test_invalid_infinity_keywords(self):
        """무한대 키워드가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("Infinity")
        assert valid is False

        valid, error = validate_number_answer("inf")
        assert valid is False

        valid, error = validate_number_answer("-inf")
        assert valid is False

    def test_invalid_nan_keywords(self):
        """NaN 키워드가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("NaN")
        assert valid is False

        valid, error = validate_number_answer("nan")
        assert valid is False

    def test_invalid_hexadecimal_numbers(self):
        """16진수가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("0xFF")
        assert valid is False

        valid, error = validate_number_answer("0x10")
        assert valid is False

    def test_invalid_octal_numbers(self):
        """8진수가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("0o77")
        assert valid is False

        valid, error = validate_number_answer("0o10")
        assert valid is False

    def test_invalid_binary_numbers(self):
        """2진수가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("0b1010")
        assert valid is False

        valid, error = validate_number_answer("0b11111111")
        assert valid is False

    def test_invalid_roman_numerals(self):
        """로마 숫자가 거부되는지 테스트합니다."""
        valid, error = validate_number_answer("X")
        assert valid is False

        valid, error = validate_number_answer("IV")
        assert valid is False

        valid, error = validate_number_answer("MMXXIV")
        assert valid is False

    def test_maximum_float_value(self):
        """최대 float 값을 테스트합니다."""
        max_float = "1.7976931348623157e+308"
        valid, error = validate_number_answer(max_float)
        assert valid is True

    def test_minimum_positive_float(self):
        """최소 양수 float를 테스트합니다."""
        min_float = "2.2250738585072014e-308"
        valid, error = validate_number_answer(min_float)
        assert valid is True

    def test_precision_limits(self):
        """정밀도 한계를 테스트합니다."""
        # 15자리 정밀도
        valid, error = validate_number_answer("1.234567890123456")
        assert valid is True

        # 17자리 (한계)
        valid, error = validate_number_answer("1.23456789012345678")
        assert valid is True

    def test_decimal_precision(self):
        """소수 정밀도를 테스트합니다."""
        valid, error = validate_number_answer("0.1")
        assert valid is True

        valid, error = validate_number_answer("0.01")
        assert valid is True

        valid, error = validate_number_answer("0.001")
        assert valid is True

    def test_negative_exponent_limits(self):
        """음수 지수 한계를 테스트합니다."""
        valid, error = validate_number_answer("1e-309")
        assert valid is True  # Python은 이를 0으로 처리

    def test_positive_exponent_limits(self):
        """양수 지수 한계를 테스트합니다."""
        valid, error = validate_number_answer("1e309")
        assert valid is True  # Python은 이를 inf로 처리할 수 있음


class TestNumberInputEdgeCases:
    """숫자 입력 엣지 케이스 - 15개"""

    def test_empty_string(self):
        """빈 문자열을 테스트합니다."""
        valid, error = validate_number_answer("")
        assert valid is False

    def test_whitespace_only(self):
        """공백만 있는 경우를 테스트합니다."""
        valid, error = validate_number_answer("   ")
        assert valid is False

    def test_leading_whitespace(self):
        """앞 공백이 있는 경우를 테스트합니다."""
        valid, error = validate_number_answer(" 42")
        assert valid is True  # Python float()는 앞뒤 공백을 처리

    def test_trailing_whitespace(self):
        """뒤 공백이 있는 경우를 테스트합니다."""
        valid, error = validate_number_answer("3.14 ")
        assert valid is True  # Python float()는 앞뒤 공백을 처리

    def test_unicode_number_characters(self):
        """유니코드 숫자 문자를 테스트합니다."""
        valid, error = validate_number_answer("٤٢")  # 아랍 숫자
        assert valid is False

        valid, error = validate_number_answer("३.१४")  # 힌디 숫자
        assert valid is False

    def test_fullwidth_numbers(self):
        """전각 숫자를 테스트합니다."""
        valid, error = validate_number_answer("４２")
        assert valid is False

        valid, error = validate_number_answer("３．１４")
        assert valid is False

    def test_subscript_numbers(self):
        """아래 첨자 숫자를 테스트합니다."""
        valid, error = validate_number_answer("₄₂")
        assert valid is False

    def test_superscript_numbers(self):
        """위 첨자 숫자를 테스트합니다."""
        valid, error = validate_number_answer("⁴²")
        assert valid is False

    def test_special_minus_signs(self):
        """특수 마이너스 기호를 테스트합니다."""
        valid, error = validate_number_answer("−5")  # 유니코드 마이너스
        assert valid is False

    def test_mixed_number_formats(self):
        """혼합 숫자 형식을 테스트합니다."""
        valid, error = validate_number_answer("12.34e5.6")
        assert valid is False

    def test_numbers_with_spaces(self):
        """숫자 중간에 공백이 있는 경우를 테스트합니다."""
        valid, error = validate_number_answer("1 234")
        assert valid is False

        valid, error = validate_number_answer("3. 14")
        assert valid is False

    def test_very_long_number_strings(self):
        """매우 긴 숫자 문자열을 테스트합니다."""
        long_number = "1" * 1000
        valid, error = validate_number_answer(long_number)
        assert valid is True  # 유효한 정수

    def test_sql_injection_in_number(self):
        """SQL 인젝션 시도를 테스트합니다."""
        valid, error = validate_number_answer("42'; DROP TABLE--")
        assert valid is False

    def test_script_injection_in_number(self):
        """스크립트 인젝션 시도를 테스트합니다."""
        valid, error = validate_number_answer("<script>42</script>")
        assert valid is False

    def test_special_characters_in_number(self):
        """특수 문자가 포함된 경우를 테스트합니다."""
        valid, error = validate_number_answer("42!")
        assert valid is False

        valid, error = validate_number_answer("#10")
        assert valid is False

        valid, error = validate_number_answer("@5")
        assert valid is False


class TestNumberQuestionIntegration:
    """NUMBER 질문 통합 테스트 - 20개"""

    def test_create_number_question_without_options(self, survey_repo, sample_survey):
        """옵션 없이 NUMBER 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="나이를 입력하세요",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(question)
        assert question.question_type == QuestionType.NUMBER
        assert question.options is None

    def test_create_required_number_question(self):
        """필수 NUMBER 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id="survey-123",
            text="월 소득",
            question_type=QuestionType.NUMBER,
            is_required=True,
        )
        assert question.is_required is True

    def test_create_optional_number_question(self):
        """선택적 NUMBER 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id="survey-123",
            text="예상 지출 (선택)",
            question_type=QuestionType.NUMBER,
            is_required=False,
        )
        assert question.is_required is False

    def test_number_question_validation_positive(self, response_service, sample_survey):
        """양수 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="참가자 수",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "50")
        assert result.is_success()

    def test_number_question_validation_negative(self, response_service, sample_survey):
        """음수 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="온도",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "-15")
        assert result.is_success()

    def test_number_question_validation_decimal(self, response_service, sample_survey):
        """소수 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="평점",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "4.5")
        assert result.is_success()

    def test_number_question_validation_invalid(self, response_service, sample_survey):
        """잘못된 입력 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="수량",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "abc")
        assert result.is_failure()
        assert "숫자" in result.error

    def test_number_question_with_zero(self, response_service, sample_survey):
        """0 입력을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="차액",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "0")
        assert result.is_success()

    def test_number_question_scientific_notation(self, response_service, sample_survey):
        """과학적 표기법을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="분자 수",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "6.022e23")
        assert result.is_success()

    def test_multiple_number_questions_in_survey(self, survey_repo, sample_survey):
        """한 설문에 여러 NUMBER 질문을 테스트합니다."""
        q1 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="키 (cm)",
            question_type=QuestionType.NUMBER,
            order=0,
        )
        q2 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="몸무게 (kg)",
            question_type=QuestionType.NUMBER,
            order=1,
        )

        for q in [q1, q2]:
            survey_repo.save_question(q)

        questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        number_questions = [q for q in questions if q.question_type == QuestionType.NUMBER]
        assert len(number_questions) >= 2

    def test_number_question_persistence_in_csv(self, survey_repo, sample_survey):
        """NUMBER 질문의 CSV 저장/로드를 테스트합니다."""
        original = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="테스트 숫자",
            question_type=QuestionType.NUMBER,
            order=5,
            is_required=True,
        )
        survey_repo.save_question(original)

        loaded_questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        loaded = next((q for q in loaded_questions if q.id == original.id), None)
        assert loaded is not None
        assert loaded.question_type == QuestionType.NUMBER
        assert loaded.order == 5
        assert loaded.is_required is True

    def test_number_results_aggregation_average(self, response_service, sample_survey, sample_admin_user, survey_repo):
        """숫자 결과 평균 계산을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="점수",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(question)

        # 여러 응답 추가
        for value in [10, 20, 30, 40, 50]:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=question.id,
                answer=str(value),
                respondent_id=str(uuid.uuid4()),
                answered_at=None,
                session_id=str(uuid.uuid4()),
                time_spent_seconds=5,
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(sample_admin_user, sample_survey.id)
        assert result.is_success()

        question_results = result.value.get(question.id)
        if question_results:
            assert question_results["average"] == 30.0  # (10+20+30+40+50)/5

    def test_number_results_aggregation_min_max(self, response_service, sample_survey, sample_admin_user, survey_repo):
        """숫자 결과 최소/최대 계산을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="가격",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(question)

        # 여러 응답 추가
        for value in [5, 15, 25, 35, 45]:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=question.id,
                answer=str(value),
                respondent_id=str(uuid.uuid4()),
                answered_at=None,
                session_id=str(uuid.uuid4()),
                time_spent_seconds=3,
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(sample_admin_user, sample_survey.id)
        assert result.is_success()

        question_results = result.value.get(question.id)
        if question_results:
            assert question_results["min"] == 5
            assert question_results["max"] == 45

    def test_number_with_decimals_in_results(self, response_service, sample_survey, sample_admin_user, survey_repo):
        """소수 포함 결과를 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="평균 시간",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(question)

        # 소수 응답 추가
        for value in [1.5, 2.3, 3.7, 4.1]:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=question.id,
                answer=str(value),
                respondent_id=str(uuid.uuid4()),
                answered_at=None,
                session_id=str(uuid.uuid4()),
                time_spent_seconds=3,
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(sample_admin_user, sample_survey.id)
        assert result.is_success()

    def test_number_question_with_large_values(self, response_service, sample_survey):
        """큰 숫자 값을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="연간 매출",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "1000000000")
        assert result.is_success()

        result = response_service._validate_answer(question, "9999999999999")
        assert result.is_success()

    def test_number_question_with_small_values(self, response_service, sample_survey):
        """작은 숫자 값을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="확률",
            question_type=QuestionType.NUMBER,
        )

        result = response_service._validate_answer(question, "0.00001")
        assert result.is_success()

        result = response_service._validate_answer(question, "0.0000000001")
        assert result.is_success()

    def test_optional_number_with_empty_answer(self, response_service, sample_survey):
        """선택적 NUMBER 질문에 빈 답변을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="추가 비용 (선택)",
            question_type=QuestionType.NUMBER,
            is_required=False,
        )

        result = response_service._validate_answer(question, "")
        assert result.is_success()  # 선택적이므로 빈 값 허용

    def test_required_number_with_empty_answer(self, response_service, sample_survey):
        """필수 NUMBER 질문에 빈 답변을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="필수 수량",
            question_type=QuestionType.NUMBER,
            is_required=True,
        )

        result = response_service._validate_answer(question, "")
        assert result.is_failure()

    def test_number_in_mixed_type_survey(self, survey_repo, sample_survey):
        """혼합 질문 유형 설문에서 NUMBER를 테스트합니다."""
        q1 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="이름",
            question_type=QuestionType.TEXT,
            order=0,
        )
        q2 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="나이",
            question_type=QuestionType.NUMBER,
            order=1,
        )
        q3 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="이메일",
            question_type=QuestionType.EMAIL,
            order=2,
        )

        for q in [q1, q2, q3]:
            survey_repo.save_question(q)

        questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        types = {q.question_type for q in questions}
        assert QuestionType.NUMBER in types

    def test_number_precision_in_calculations(self, response_service, sample_survey, sample_admin_user, survey_repo):
        """계산 시 숫자 정밀도를 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="정밀 측정",
            question_type=QuestionType.NUMBER,
        )
        survey_repo.save_question(question)

        # 정밀한 소수 응답
        for value in [0.1, 0.2, 0.3]:
            response = Response(
                id=str(uuid.uuid4()),
                survey_id=sample_survey.id,
                question_id=question.id,
                answer=str(value),
                respondent_id=str(uuid.uuid4()),
                answered_at=None,
                session_id=str(uuid.uuid4()),
                time_spent_seconds=2,
            )
            response_service.response_repository.save(response)

        result = response_service.get_survey_results(sample_admin_user, sample_survey.id)
        assert result.is_success()

        question_results = result.value.get(question.id)
        if question_results:
            # 부동소수점 정밀도 문제 고려
            assert abs(question_results["average"] - 0.2) < 0.01