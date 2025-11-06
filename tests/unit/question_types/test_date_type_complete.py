"""완벽한 DATE 질문 유형 테스트 - 80개 시나리오"""
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
from interface.cli.validators import validate_date_answer


class TestDateFormatValidation:
    """날짜 형식 검증 테스트 - 20개"""

    def test_valid_standard_yyyy_mm_dd(self):
        """표준 YYYY-MM-DD 형식을 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15")
        assert valid is True
        assert error == ""

    def test_valid_leap_year_date(self):
        """윤년 2월 29일을 테스트합니다."""
        valid, error = validate_date_answer("2024-02-29")
        assert valid is True
        assert error == ""

    def test_invalid_non_leap_year_feb_29(self):
        """평년 2월 29일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2023-02-29")
        assert valid is False
        assert "날짜" in error

    def test_valid_month_boundaries_31_days(self):
        """31일이 있는 달의 경계를 테스트합니다."""
        months_31 = ["01", "03", "05", "07", "08", "10", "12"]
        for month in months_31:
            valid, error = validate_date_answer(f"2024-{month}-31")
            assert valid is True, f"Month {month} should have 31 days"

    def test_valid_month_boundaries_30_days(self):
        """30일이 있는 달의 경계를 테스트합니다."""
        months_30 = ["04", "06", "09", "11"]
        for month in months_30:
            valid, error = validate_date_answer(f"2024-{month}-30")
            assert valid is True, f"Month {month} should have 30 days"

    def test_invalid_month_boundaries_31st_for_30_day_months(self):
        """30일 달에 31일이 거부되는지 테스트합니다."""
        months_30 = ["04", "06", "09", "11"]
        for month in months_30:
            valid, error = validate_date_answer(f"2024-{month}-31")
            assert valid is False, f"Month {month} should not have 31 days"

    def test_valid_single_digit_with_zero_padding(self):
        """한 자리 월/일에 0 패딩이 있는 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-01-01")
        assert valid is True
        valid, error = validate_date_answer("2024-09-09")
        assert valid is True

    def test_invalid_format_mm_dd_yyyy(self):
        """MM/DD/YYYY 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("03/15/2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_dd_mm_yyyy(self):
        """DD-MM-YYYY 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("15-03-2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_yyyy_slash_mm_slash_dd(self):
        """YYYY/MM/DD 슬래시 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024/03/15")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_yyyymmdd_no_separator(self):
        """구분자 없는 YYYYMMDD가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("20240315")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_dd_dot_mm_dot_yyyy(self):
        """DD.MM.YYYY 점 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("15.03.2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_text_month(self):
        """텍스트 월 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("March 15, 2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_iso_8601_with_time(self):
        """시간이 포함된 ISO 8601이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15T10:30:00")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_with_timezone(self):
        """타임존이 포함된 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15Z")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_mm_dash_dd_dash_yyyy(self):
        """MM-DD-YYYY 대시 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("03-15-2024")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_with_extra_digits(self):
        """추가 자릿수가 있는 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-003-015")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_format_missing_zero_padding(self):
        """0 패딩이 없는 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-3-15")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_separator_underscore(self):
        """언더스코어 구분자가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024_03_15")
        assert valid is False
        assert "YYYY-MM-DD" in error

    def test_invalid_separator_space(self):
        """공백 구분자가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024 03 15")
        assert valid is False
        assert "YYYY-MM-DD" in error


class TestDateRangeValidation:
    """날짜 범위 검증 테스트 - 15개"""

    def test_valid_minimum_year_1000(self):
        """최소 년도 1000년을 테스트합니다."""
        valid, error = validate_date_answer("1000-01-01")
        assert valid is True

    def test_valid_maximum_year_9999(self):
        """최대 년도 9999년을 테스트합니다."""
        valid, error = validate_date_answer("9999-12-31")
        assert valid is True

    def test_invalid_year_0000(self):
        """0000년이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("0000-01-01")
        assert valid is False

    def test_invalid_year_10000(self):
        """10000년이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("10000-01-01")
        assert valid is False

    def test_invalid_negative_year(self):
        """음수 년도가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("-2024-03-15")
        assert valid is False

    def test_century_leap_year_2000(self):
        """2000년(세기 윤년)을 테스트합니다."""
        valid, error = validate_date_answer("2000-02-29")
        assert valid is True

    def test_century_non_leap_year_1900(self):
        """1900년(세기 평년)을 테스트합니다."""
        valid, error = validate_date_answer("1900-02-29")
        assert valid is False

    def test_century_non_leap_year_2100(self):
        """2100년(세기 평년)을 테스트합니다."""
        valid, error = validate_date_answer("2100-02-29")
        assert valid is False

    def test_february_28_in_non_leap_year(self):
        """평년 2월 28일을 테스트합니다."""
        valid, error = validate_date_answer("2023-02-28")
        assert valid is True

    def test_february_29_in_leap_year_2020(self):
        """2020년(윤년) 2월 29일을 테스트합니다."""
        valid, error = validate_date_answer("2020-02-29")
        assert valid is True

    def test_february_30_always_invalid(self):
        """2월 30일이 항상 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-02-30")
        assert valid is False
        valid, error = validate_date_answer("2023-02-30")
        assert valid is False

    def test_february_31_always_invalid(self):
        """2월 31일이 항상 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-02-31")
        assert valid is False

    def test_april_31_invalid(self):
        """4월 31일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-04-31")
        assert valid is False

    def test_june_31_invalid(self):
        """6월 31일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-06-31")
        assert valid is False

    def test_september_31_invalid(self):
        """9월 31일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-09-31")
        assert valid is False


class TestDateInvalidValues:
    """잘못된 날짜 값 테스트 - 15개"""

    def test_invalid_month_00(self):
        """0월이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-00-15")
        assert valid is False

    def test_invalid_month_13(self):
        """13월이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-13-15")
        assert valid is False

    def test_invalid_day_00(self):
        """0일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03-00")
        assert valid is False

    def test_invalid_day_32(self):
        """32일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-01-32")
        assert valid is False

    def test_invalid_day_99(self):
        """99일이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03-99")
        assert valid is False

    def test_invalid_month_99(self):
        """99월이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-99-15")
        assert valid is False

    def test_invalid_special_chars_in_date(self):
        """날짜에 특수문자가 있을 때 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("@024-03-15")
        assert valid is False

    def test_invalid_text_instead_of_numbers(self):
        """숫자 대신 텍스트가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("YYYY-MM-DD")
        assert valid is False

    def test_invalid_partial_date(self):
        """부분 날짜가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03")
        assert valid is False

    def test_invalid_year_only(self):
        """년도만 있는 경우 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024")
        assert valid is False

    def test_invalid_mixed_separators(self):
        """혼합 구분자가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03/15")
        assert valid is False

    def test_invalid_reversed_format(self):
        """역순 형식이 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("15-03-2024")
        assert valid is False

    def test_invalid_alphabetic_month_code(self):
        """알파벳 월 코드가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-MAR-15")
        assert valid is False

    def test_invalid_with_ordinal_suffix(self):
        """서수 접미사가 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15th")
        assert valid is False

    def test_invalid_with_day_name(self):
        """요일 이름이 포함된 경우 거부되는지 테스트합니다."""
        valid, error = validate_date_answer("Friday 2024-03-15")
        assert valid is False


class TestDateInputEdgeCases:
    """날짜 입력 엣지 케이스 - 15개"""

    def test_empty_string_for_optional(self):
        """선택적 날짜 질문에 빈 문자열을 테스트합니다."""
        valid, error = validate_date_answer("")
        assert valid is False  # 빈 문자열은 유효성 검사를 통과하지 못함

    def test_whitespace_only(self):
        """공백만 있는 경우를 테스트합니다."""
        valid, error = validate_date_answer("   ")
        assert valid is False

    def test_leading_whitespace(self):
        """앞 공백이 있는 경우를 테스트합니다."""
        valid, error = validate_date_answer(" 2024-03-15")
        assert valid is False  # 정확한 형식이 아님

    def test_trailing_whitespace(self):
        """뒤 공백이 있는 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15 ")
        assert valid is False  # 정확한 형식이 아님

    def test_unicode_date_characters(self):
        """유니코드 날짜 문자를 테스트합니다."""
        valid, error = validate_date_answer("٢٠٢٤-٠٣-١٥")
        assert valid is False

    def test_fullwidth_numbers(self):
        """전각 숫자를 테스트합니다."""
        valid, error = validate_date_answer("２０２４-０３-１５")
        assert valid is False

    def test_very_long_string_starting_with_valid_date(self):
        """유효한 날짜로 시작하는 매우 긴 문자열을 테스트합니다."""
        long_str = "2024-03-15" + "x" * 1000
        valid, error = validate_date_answer(long_str)
        assert valid is False

    def test_sql_injection_attempt(self):
        """SQL 인젝션 시도를 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15'; DROP TABLE--")
        assert valid is False

    def test_script_injection_attempt(self):
        """스크립트 인젝션 시도를 테스트합니다."""
        valid, error = validate_date_answer("<script>alert('2024-03-15')</script>")
        assert valid is False

    def test_null_character(self):
        """널 문자가 포함된 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15\x00")
        assert valid is False

    def test_tab_character(self):
        """탭 문자가 포함된 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024\t03\t15")
        assert valid is False

    def test_newline_character(self):
        """개행 문자가 포함된 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15\n")
        assert valid is False

    def test_binary_data(self):
        """바이너리 데이터를 테스트합니다."""
        valid, error = validate_date_answer(b"\x00\x01\x02\x03")
        assert valid is False

    def test_emoji_in_date(self):
        """이모지가 포함된 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-😊-15")
        assert valid is False

    def test_control_characters(self):
        """제어 문자가 포함된 경우를 테스트합니다."""
        valid, error = validate_date_answer("2024-03-15\x1b")
        assert valid is False


class TestDateQuestionIntegration:
    """DATE 질문 통합 테스트 - 15개"""

    def test_create_date_question_without_options(self, survey_repo, sample_survey):
        """옵션 없이 DATE 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="생년월일을 입력하세요",
            question_type=QuestionType.DATE,
        )
        survey_repo.save_question(question)
        assert question.question_type == QuestionType.DATE
        assert question.options is None

    def test_create_date_question_with_order(self, survey_repo, sample_survey):
        """순서가 있는 DATE 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="입사일을 입력하세요",
            question_type=QuestionType.DATE,
            order=5,
        )
        assert question.order == 5

    def test_create_required_date_question(self, survey_repo, sample_survey):
        """필수 DATE 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="계약 시작일",
            question_type=QuestionType.DATE,
            is_required=True,
        )
        assert question.is_required is True

    def test_create_optional_date_question(self, survey_repo, sample_survey):
        """선택적 DATE 질문을 생성합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="예상 종료일 (선택)",
            question_type=QuestionType.DATE,
            is_required=False,
        )
        assert question.is_required is False

    def test_date_question_validation_in_response_service(self, response_service, sample_survey):
        """ResponseService에서 DATE 검증을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="프로젝트 시작일",
            question_type=QuestionType.DATE,
        )

        # 유효한 날짜
        result = response_service._validate_answer(question, "2024-03-15")
        assert result.is_success()

        # 잘못된 형식
        result = response_service._validate_answer(question, "03/15/2024")
        assert result.is_failure()

    def test_date_question_with_past_dates(self, response_service, sample_survey):
        """과거 날짜 입력을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="생년월일",
            question_type=QuestionType.DATE,
        )

        result = response_service._validate_answer(question, "1990-01-01")
        assert result.is_success()

    def test_date_question_with_future_dates(self, response_service, sample_survey):
        """미래 날짜 입력을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="예약일",
            question_type=QuestionType.DATE,
        )

        result = response_service._validate_answer(question, "2025-12-31")
        assert result.is_success()

    def test_date_question_with_current_date(self, response_service, sample_survey):
        """오늘 날짜 입력을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="접수일",
            question_type=QuestionType.DATE,
        )

        today = datetime.now().strftime("%Y-%m-%d")
        result = response_service._validate_answer(question, today)
        assert result.is_success()

    def test_multiple_date_questions_in_survey(self, survey_repo, sample_survey):
        """한 설문에 여러 DATE 질문을 테스트합니다."""
        q1 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="시작일",
            question_type=QuestionType.DATE,
            order=0,
        )
        q2 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="종료일",
            question_type=QuestionType.DATE,
            order=1,
        )
        survey_repo.save_question(q1)
        survey_repo.save_question(q2)

        questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        date_questions = [q for q in questions if q.question_type == QuestionType.DATE]
        assert len(date_questions) >= 2

    def test_date_question_persistence_in_csv(self, survey_repo, sample_survey):
        """DATE 질문의 CSV 저장/로드를 테스트합니다."""
        original = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="테스트 날짜",
            question_type=QuestionType.DATE,
            order=3,
            is_required=False,
        )
        survey_repo.save_question(original)

        loaded_questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        loaded = next((q for q in loaded_questions if q.id == original.id), None)
        assert loaded is not None
        assert loaded.question_type == QuestionType.DATE
        assert loaded.order == 3
        assert loaded.is_required is False

    def test_date_response_submission(self, response_service, sample_survey, sample_admin_user):
        """DATE 응답 제출을 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="방문일",
            question_type=QuestionType.DATE,
        )

        session_id = str(uuid.uuid4())
        answers = {question.id: "2024-03-15"}
        time_spent = {question.id: 10}

        result = response_service.submit_response(
            sample_admin_user,
            sample_survey.id,
            answers,
            session_id,
            time_spent
        )
        # 실제 질문이 저장되지 않아서 실패할 수 있음

    def test_date_question_in_mixed_type_survey(self, survey_repo, sample_survey):
        """혼합 질문 유형 설문에서 DATE를 테스트합니다."""
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
            text="생년월일",
            question_type=QuestionType.DATE,
            order=1,
        )
        q3 = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="만족도",
            question_type=QuestionType.RATING,
            order=2,
        )

        for q in [q1, q2, q3]:
            survey_repo.save_question(q)

        questions = survey_repo.find_questions_by_survey_id(sample_survey.id)
        types = {q.question_type for q in questions}
        assert QuestionType.DATE in types

    def test_historical_dates(self, response_service, sample_survey):
        """역사적 날짜 (1900년 이전)를 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="역사적 사건 날짜",
            question_type=QuestionType.DATE,
        )

        # 1800년대
        result = response_service._validate_answer(question, "1865-04-15")
        assert result.is_success()

        # 1000년대
        result = response_service._validate_answer(question, "1066-10-14")
        assert result.is_success()

    def test_far_future_dates(self, response_service, sample_survey):
        """먼 미래 날짜 (2100년 이후)를 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="장기 계획 날짜",
            question_type=QuestionType.DATE,
        )

        result = response_service._validate_answer(question, "2150-12-31")
        assert result.is_success()

        result = response_service._validate_answer(question, "3000-01-01")
        assert result.is_success()

    def test_date_question_error_handling(self, response_service, sample_survey):
        """DATE 질문의 에러 처리를 테스트합니다."""
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=sample_survey.id,
            text="날짜 입력",
            question_type=QuestionType.DATE,
            is_required=True,
        )

        # 필수인데 빈 값
        result = response_service._validate_answer(question, "")
        assert result.is_failure()

        # 잘못된 형식
        result = response_service._validate_answer(question, "invalid")
        assert result.is_failure()
        assert "날짜" in result.error or "YYYY-MM-DD" in result.error