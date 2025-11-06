"""
EMAIL 질문 타입 완전 테스트 스위트
60개 테스트 케이스로 모든 시나리오 검증
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import ClassVar

from domain.entities.user import User
from domain.value_objects.role import Role
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.category import Category
from domain.value_objects.types import QuestionType
from domain.repositories.survey_repository import SurveyRepository
from domain.repositories.response_repository import ResponseRepository
from domain.repositories.category_repository import CategoryRepository

from application.survey_service import SurveyService
from application.response_service import ResponseService
from interface.cli.validators import validate_email_answer


@dataclass(frozen=True, slots=True)
class EmailTestCase:
    """이메일 테스트 케이스"""
    case_id: str
    input_value: str
    expected_valid: bool
    description: str
    error_message: str | None = None


class TestEmailValidation:
    """이메일 형식 검증 테스트 (25개)"""

    @pytest.mark.parametrize("test_case", [
        EmailTestCase("E001", "user@example.com", True, "표준 이메일 형식"),
        EmailTestCase("E002", "user.name@example.com", True, "점이 포함된 사용자명"),
        EmailTestCase("E003", "user+tag@example.com", True, "플러스 태그 포함"),
        EmailTestCase("E004", "user_name@example.com", True, "언더스코어 포함"),
        EmailTestCase("E005", "user-name@example.com", True, "하이픈 포함"),
        EmailTestCase("E006", "123@example.com", True, "숫자로만 구성된 사용자명"),
        EmailTestCase("E007", "user@subdomain.example.com", True, "서브도메인 포함"),
        EmailTestCase("E008", "user@example.co.kr", True, "국가 도메인"),
        EmailTestCase("E009", "very.long.email.address@very.long.domain.name.com", True, "긴 이메일 주소"),
        EmailTestCase("E010", "a@b.co", True, "최소 길이 이메일"),
        EmailTestCase("E011", "user", False, "@ 기호 없음", "유효하지 않은 이메일 형식"),
        EmailTestCase("E012", "@example.com", False, "사용자명 없음", "유효하지 않은 이메일 형식"),
        EmailTestCase("E013", "user@", False, "도메인 없음", "유효하지 않은 이메일 형식"),
        EmailTestCase("E014", "user@.com", False, "도메인명 없음", "유효하지 않은 이메일 형식"),
        EmailTestCase("E015", "user@domain", False, "TLD 없음", "유효하지 않은 이메일 형식"),
        EmailTestCase("E016", "user name@example.com", False, "사용자명에 공백", "유효하지 않은 이메일 형식"),
        EmailTestCase("E017", "user@exam ple.com", False, "도메인에 공백", "유효하지 않은 이메일 형식"),
        EmailTestCase("E018", "user@@example.com", False, "@ 기호 중복", "유효하지 않은 이메일 형식"),
        EmailTestCase("E019", "user.@example.com", False, "사용자명이 점으로 끝남", "유효하지 않은 이메일 형식"),
        EmailTestCase("E020", ".user@example.com", False, "사용자명이 점으로 시작", "유효하지 않은 이메일 형식"),
        EmailTestCase("E021", "user..name@example.com", False, "연속된 점", "유효하지 않은 이메일 형식"),
        EmailTestCase("E022", "user#name@example.com", False, "허용되지 않는 특수문자 #", "유효하지 않은 이메일 형식"),
        EmailTestCase("E023", "user%name@example.com", False, "허용되지 않는 특수문자 %", "유효하지 않은 이메일 형식"),
        EmailTestCase("E024", "user&name@example.com", False, "허용되지 않는 특수문자 &", "유효하지 않은 이메일 형식"),
        EmailTestCase("E025", "user*name@example.com", False, "허용되지 않는 특수문자 *", "유효하지 않은 이메일 형식"),
    ])
    def test_email_format_validation(self, test_case: EmailTestCase):
        """이메일 형식 검증"""
        valid, message = validate_email_answer(test_case.input_value)
        assert valid == test_case.expected_valid, f"{test_case.description} 실패"
        if not test_case.expected_valid:
            assert test_case.error_message in message


class TestEmailSpecialCases:
    """특수 케이스 테스트 (15개)"""

    @pytest.mark.parametrize("test_case", [
        EmailTestCase("ES01", "", False, "빈 문자열", "이메일 주소를 입력해주세요"),
        EmailTestCase("ES02", "   ", False, "공백만", "이메일 주소를 입력해주세요"),
        EmailTestCase("ES03", "  user@example.com  ", True, "앞뒤 공백 (자동 trim)"),
        EmailTestCase("ES04", "USER@EXAMPLE.COM", True, "모두 대문자"),
        EmailTestCase("ES05", "User@Example.Com", True, "대소문자 혼합"),
        EmailTestCase("ES06", "한글@example.com", False, "한글 사용자명", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES07", "user@한글.com", False, "한글 도메인", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES08", "user@example.c", False, "TLD가 1자", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES09", "user@example.museum", True, "긴 TLD"),
        EmailTestCase("ES10", "user@localhost", False, "로컬호스트", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES11", "user@127.0.0.1", False, "IP 주소", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES12", "user@[192.168.1.1]", False, "대괄호 IP", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES13", '"user name"@example.com', False, "따옴표 사용", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES14", "user\\@example.com", False, "이스케이프 문자", "유효하지 않은 이메일 형식"),
        EmailTestCase("ES15", "user@example..com", False, "도메인에 연속된 점", "유효하지 않은 이메일 형식"),
    ])
    def test_email_special_cases(self, test_case: EmailTestCase):
        """특수 케이스 처리"""
        valid, message = validate_email_answer(test_case.input_value)
        assert valid == test_case.expected_valid, f"{test_case.description} 실패"
        if not test_case.expected_valid and test_case.error_message:
            assert test_case.error_message in message


class TestEmailIntegration:
    """통합 테스트 (10개)"""

    @pytest.fixture
    def setup_email_survey(self):
        """이메일 타입 설문 설정"""
        admin = User(
            id="admin1",
            tenant_id="tenant1",
            username="admin",
            email="admin@example.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.TENANT_ADMIN,
            created_at=datetime.now()
        )

        category = Category(
            id="cat1",
            name="이메일 카테고리",
            description="이메일 수집용"
        )

        survey = Survey(
            id="survey1",
            title="이메일 수집 설문",
            description="이메일 정보 수집",
            creator_id=admin.id,
            category_id=category.id,
            questions=[
                Question(
                    id="q1",
                    survey_id="survey1",
                    text="이메일 주소를 입력하세요",
                    question_type=QuestionType.EMAIL,
                    is_required=True,
                    order=1
                ),
                Question(
                    id="q2",
                    survey_id="survey1",
                    text="선택적 이메일",
                    question_type=QuestionType.EMAIL,
                    is_required=False,
                    order=2
                )
            ]
        )

        return admin, category, survey

    def test_email_required_validation(self, setup_email_survey):
        """필수 이메일 검증"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 필수 이메일 누락
        result = service.submit_response(admin, "survey1", {"q2": "optional@example.com"})
        assert result.is_failure
        assert "필수 질문" in result.error

    def test_email_invalid_format_rejection(self, setup_email_survey):
        """잘못된 이메일 형식 거부"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 잘못된 이메일 형식
        result = service.submit_response(admin, "survey1", {
            "q1": "invalid.email",
            "q2": "also@invalid"
        })
        assert result.is_failure
        assert "올바른 이메일 형식" in result.error

    def test_email_valid_submission(self, setup_email_survey):
        """유효한 이메일 제출"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "valid@example.com",
            "q2": "another@example.org"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        assert saved_response.answers["q1"] == "valid@example.com"
        assert saved_response.answers["q2"] == "another@example.org"

    def test_email_optional_empty(self, setup_email_survey):
        """선택적 이메일 빈값 허용"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "required@example.com"
            # q2는 선택사항이므로 생략
        })
        assert result.is_success

    def test_email_case_preservation(self, setup_email_survey):
        """이메일 대소문자 보존"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "User.Name@Example.COM"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        # 대소문자가 보존되어야 함
        assert saved_response.answers["q1"] == "User.Name@Example.COM"

    def test_email_trimming(self, setup_email_survey):
        """이메일 앞뒤 공백 제거"""
        admin, category, survey = setup_email_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "  trimmed@example.com  "
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        assert saved_response.answers["q1"] == "trimmed@example.com"

    def test_email_multiple_questions(self, setup_email_survey):
        """여러 이메일 질문 처리"""
        admin, category, survey = setup_email_survey

        # 추가 이메일 질문 추가
        survey.questions.append(
            Question(
                id="q3",
                survey_id="survey1",
                text="백업 이메일",
                question_type=QuestionType.EMAIL,
                is_required=True,
                order=3
            )
        )

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "primary@example.com",
            "q2": "secondary@example.com",
            "q3": "backup@example.com"
        })
        assert result.is_success

    def test_email_with_mixed_types(self):
        """이메일과 다른 타입 혼합"""
        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        survey = Survey(
            id="survey1",
            title="혼합 설문",
            description="다양한 타입",
            creator_id=admin.id,
            questions=[
                Question(id="q1", survey_id="survey1", text="이름", question_type=QuestionType.TEXT, is_required=True, order=1),
                Question(id="q2", survey_id="survey1", text="이메일", question_type=QuestionType.EMAIL, is_required=True, order=2),
                Question(id="q3", survey_id="survey1", text="나이", question_type=QuestionType.NUMBER, is_required=True, order=3)
            ]
        )

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "홍길동",
            "q2": "hong@example.com",
            "q3": "25"
        })
        assert result.is_success

    def test_email_internationalized_domains(self):
        """국제화 도메인 테스트"""
        # 다양한 국가 도메인 테스트
        test_emails = [
            ("user@example.co.uk", True),
            ("user@example.co.jp", True),
            ("user@example.com.au", True),
            ("user@example.gov.us", True),
            ("user@example.ac.kr", True)
        ]

        for email, expected in test_emails:
            valid, _ = validate_email_answer(email)
            assert valid == expected, f"{email} 검증 실패"

    def test_email_aggregation(self):
        """이메일 응답 집계"""
        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        survey = Survey(
            id="survey1",
            title="이메일 수집",
            description="이메일 집계 테스트",
            creator_id=admin.id,
            questions=[
                Question(id="q1", survey_id="survey1", text="업무 이메일", question_type=QuestionType.EMAIL, is_required=True, order=1),
                Question(id="q2", survey_id="survey1", text="개인 이메일", question_type=QuestionType.EMAIL, is_required=False, order=2)
            ]
        )

        responses = [
            Response(id="r1", survey_id="survey1", respondent_id="user1",
                    answers={"q1": "user1@company.com", "q2": "user1@personal.com"}),
            Response(id="r2", survey_id="survey1", respondent_id="user2",
                    answers={"q1": "user2@company.com"}),
            Response(id="r3", survey_id="survey1", respondent_id="user3",
                    answers={"q1": "user3@company.com", "q2": "user3@gmail.com"})
        ]

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.find_by_survey_id.return_value = responses

        service = ResponseService(response_repo, survey_repo, category_repo)
        result = service.get_survey_results(admin, "survey1")

        assert result.is_success
        results = result.value

        # 이메일 도메인 분석
        q1_emails = results["questions"]["q1"]["responses"]
        assert len(q1_emails) == 3
        assert all("@company.com" in email for email in q1_emails.values())

        q2_emails = results["questions"]["q2"]["responses"]
        assert len(q2_emails) == 2  # 2명만 응답


class TestEmailEdgeCases:
    """극단적 케이스 테스트 (10개)"""

    def test_email_max_length(self):
        """최대 길이 이메일"""
        # RFC 5321: 로컬 파트 64자, 도메인 255자
        long_local = "a" * 64
        long_domain = "sub." * 50 + "example.com"

        valid, _ = validate_email_answer(f"{long_local}@{long_domain}")
        # 너무 긴 이메일은 실용적이지 않으므로 거부될 수 있음
        assert not valid or len(f"{long_local}@{long_domain}") > 320

    def test_email_min_length(self):
        """최소 길이 이메일"""
        valid, _ = validate_email_answer("a@b.co")
        assert valid

    def test_email_unicode_rejection(self):
        """유니코드 문자 거부"""
        unicode_emails = [
            "用户@example.com",
            "user@例え.com",
            "مستخدم@example.com",
            "user@домен.com"
        ]

        for email in unicode_emails:
            valid, message = validate_email_answer(email)
            assert not valid
            assert "올바른 이메일 형식" in message

    def test_email_special_valid_chars(self):
        """허용되는 특수문자"""
        valid_emails = [
            "user.name@example.com",
            "user+tag@example.com",
            "user_name@example.com",
            "user-name@example.com"
        ]

        for email in valid_emails:
            valid, _ = validate_email_answer(email)
            assert valid, f"{email}은(는) 유효해야 함"

    def test_email_injection_attempt(self):
        """인젝션 공격 시도"""
        injection_attempts = [
            "user@example.com\r\nBcc: attacker@evil.com",
            "user@example.com; DROP TABLE users;--",
            "user@example.com<script>alert('xss')</script>",
            "user@example.com' OR '1'='1"
        ]

        for attempt in injection_attempts:
            valid, _ = validate_email_answer(attempt)
            assert not valid

    def test_email_null_byte(self):
        """널 바이트 처리"""
        valid, _ = validate_email_answer("user\x00@example.com")
        assert not valid

    def test_email_control_characters(self):
        """제어 문자 처리"""
        control_chars = ["\n", "\r", "\t", "\b", "\f"]

        for char in control_chars:
            valid, _ = validate_email_answer(f"user{char}@example.com")
            assert not valid

    def test_email_homograph_attack(self):
        """호모그래프 공격"""
        # 시각적으로 유사한 문자 사용
        homograph_emails = [
            "user@examp1e.com",  # l을 1로
            "user@examρle.com",  # p를 그리스 문자 ρ로
        ]

        for email in homograph_emails:
            # 실제로는 다른 도메인이므로 유효성 검사는 통과할 수 있음
            valid, _ = validate_email_answer(email)
            # 기본 ASCII만 허용한다면 두 번째는 실패해야 함
            if "ρ" in email:
                assert not valid

    def test_email_subdomain_depth(self):
        """깊은 서브도메인"""
        deep_subdomain = "user@a.b.c.d.e.f.g.h.i.j.k.example.com"
        valid, _ = validate_email_answer(deep_subdomain)
        assert valid

    def test_email_numeric_tld(self):
        """숫자 TLD"""
        # 현재 숫자만으로 된 TLD는 없음
        valid, _ = validate_email_answer("user@example.123")
        assert not valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])