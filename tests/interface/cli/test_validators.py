import pytest
from interface.cli.validators import (
    validate_email,
    validate_password,
    validate_username,
    validate_tenant_name,
    validate_survey_title,
    validate_question_text,
    validate_rating_answer,
    create_validator,
)


class TestValidateEmail:
    """이메일 검증 테스트"""

    def test_valid_email(self):
        """유효한 이메일 형식"""
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error == ""

    def test_invalid_email_no_at(self):
        """@ 없는 이메일"""
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False
        assert "유효하지 않은" in error

    def test_invalid_email_no_domain(self):
        """도메인 없는 이메일"""
        is_valid, error = validate_email("user@")
        assert is_valid is False
        assert "유효하지 않은" in error


class TestValidatePassword:
    """비밀번호 검증 테스트"""

    def test_valid_password(self):
        """유효한 비밀번호"""
        is_valid, error = validate_password("password123")
        assert is_valid is True
        assert error == ""

    def test_password_too_short(self):
        """8자 미만 비밀번호"""
        is_valid, error = validate_password("pass1")
        assert is_valid is False
        assert "최소 8자" in error

    def test_password_no_digit(self):
        """숫자 없는 비밀번호"""
        is_valid, error = validate_password("password")
        assert is_valid is False
        assert "숫자를 포함" in error

    def test_password_no_letter(self):
        """문자 없는 비밀번호"""
        is_valid, error = validate_password("12345678")
        assert is_valid is False
        assert "문자를 포함" in error


class TestValidateUsername:
    """사용자명 검증 테스트"""

    def test_valid_username(self):
        """유효한 사용자명"""
        is_valid, error = validate_username("testuser")
        assert is_valid is True
        assert error == ""

    def test_username_too_short(self):
        """3자 미만 사용자명"""
        is_valid, error = validate_username("ab")
        assert is_valid is False
        assert "최소 3자" in error

    def test_username_too_long(self):
        """20자 초과 사용자명"""
        is_valid, error = validate_username("a" * 21)
        assert is_valid is False
        assert "최대 20자" in error

    def test_username_starts_with_digit(self):
        """숫자로 시작하는 사용자명"""
        is_valid, error = validate_username("1testuser")
        assert is_valid is False
        assert "영문자로 시작" in error

    def test_username_invalid_chars(self):
        """특수문자 포함 사용자명"""
        is_valid, error = validate_username("test@user")
        assert is_valid is False
        assert "영문자, 숫자, _, -" in error


class TestValidateTenantName:
    """테넌트 이름 검증 테스트"""

    def test_valid_tenant_name(self):
        """유효한 테넌트 이름"""
        is_valid, error = validate_tenant_name("테스트 회사")
        assert is_valid is True
        assert error == ""

    def test_tenant_name_too_short(self):
        """2자 미만 테넌트 이름"""
        is_valid, error = validate_tenant_name("a")
        assert is_valid is False
        assert "최소 2자" in error

    def test_tenant_name_too_long(self):
        """50자 초과 테넌트 이름"""
        is_valid, error = validate_tenant_name("a" * 51)
        assert is_valid is False
        assert "최대 50자" in error


class TestValidateSurveyTitle:
    """설문 제목 검증 테스트"""

    def test_valid_survey_title(self):
        """유효한 설문 제목"""
        is_valid, error = validate_survey_title("만족도 조사")
        assert is_valid is True
        assert error == ""

    def test_survey_title_too_short(self):
        """3자 미만 설문 제목"""
        is_valid, error = validate_survey_title("ab")
        assert is_valid is False
        assert "최소 3자" in error

    def test_survey_title_too_long(self):
        """100자 초과 설문 제목"""
        is_valid, error = validate_survey_title("a" * 101)
        assert is_valid is False
        assert "최대 100자" in error


class TestValidateQuestionText:
    """질문 내용 검증 테스트"""

    def test_valid_question_text(self):
        """유효한 질문 내용"""
        is_valid, error = validate_question_text("이 서비스에 만족하십니까?")
        assert is_valid is True
        assert error == ""

    def test_question_text_too_short(self):
        """5자 미만 질문 내용"""
        is_valid, error = validate_question_text("질문")
        assert is_valid is False
        assert "최소 5자" in error

    def test_question_text_too_long(self):
        """500자 초과 질문 내용"""
        is_valid, error = validate_question_text("a" * 501)
        assert is_valid is False
        assert "최대 500자" in error


class TestValidateRatingAnswer:
    """평점 답변 검증 테스트"""

    def test_valid_rating_answer(self):
        """유효한 평점 답변"""
        is_valid, error = validate_rating_answer("3")
        assert is_valid is True
        assert error == ""

    def test_rating_answer_not_digit(self):
        """숫자가 아닌 평점"""
        is_valid, error = validate_rating_answer("abc")
        assert is_valid is False
        assert "숫자여야" in error

    def test_rating_answer_out_of_range_low(self):
        """1보다 작은 평점"""
        is_valid, error = validate_rating_answer("0")
        assert is_valid is False
        assert "1-5 사이" in error

    def test_rating_answer_out_of_range_high(self):
        """5보다 큰 평점"""
        is_valid, error = validate_rating_answer("6")
        assert is_valid is False
        assert "1-5 사이" in error


class TestCreateValidator:
    """create_validator 래퍼 함수 테스트"""

    def test_create_validator_success(self):
        """검증 성공 케이스"""
        validator = create_validator(validate_email)
        result = validator("user@example.com")
        assert result == "user@example.com"

    def test_create_validator_failure_raises_value_error(self):
        """검증 실패 시 ValueError 발생"""
        validator = create_validator(validate_email)
        with pytest.raises(ValueError, match="유효하지 않은"):
            validator("invalid-email")
