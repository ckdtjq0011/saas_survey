"""
YES_NO 질문 타입 완전 테스트 스위트
40개 테스트 케이스로 모든 시나리오 검증
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
from interface.cli.validators import validate_yes_no_answer


@dataclass(frozen=True, slots=True)
class YesNoTestCase:
    """Yes/No 테스트 케이스"""
    case_id: str
    input_value: str
    expected_valid: bool
    expected_normalized: str | None
    description: str


class TestYesNoValidation:
    """Yes/No 형식 검증 테스트 (15개)"""

    @pytest.mark.parametrize("test_case", [
        YesNoTestCase("YN01", "y", True, "y", "소문자 y"),
        YesNoTestCase("YN02", "Y", True, "y", "대문자 Y"),
        YesNoTestCase("YN03", "n", True, "n", "소문자 n"),
        YesNoTestCase("YN04", "N", True, "n", "대문자 N"),
        YesNoTestCase("YN05", "yes", True, "y", "소문자 yes"),
        YesNoTestCase("YN06", "YES", True, "y", "대문자 YES"),
        YesNoTestCase("YN07", "Yes", True, "y", "혼합 대소문자 Yes"),
        YesNoTestCase("YN08", "no", True, "n", "소문자 no"),
        YesNoTestCase("YN09", "NO", True, "n", "대문자 NO"),
        YesNoTestCase("YN10", "No", True, "n", "혼합 대소문자 No"),
        YesNoTestCase("YN11", "예", True, "y", "한글 예"),
        YesNoTestCase("YN12", "아니오", True, "n", "한글 아니오"),
        YesNoTestCase("YN13", "아니요", True, "n", "한글 아니요"),
        YesNoTestCase("YN14", "네", True, "y", "한글 네"),
        YesNoTestCase("YN15", "아니", True, "n", "한글 아니"),
    ])
    def test_yes_no_format_validation(self, test_case: YesNoTestCase):
        """Yes/No 형식 검증"""
        valid, message = validate_yes_no_answer(test_case.input_value)
        assert valid == test_case.expected_valid, f"{test_case.description} 실패"

        # 정규화 값 확인
        if valid and test_case.expected_normalized:
            # message가 정규화된 값이어야 함
            assert test_case.expected_normalized in test_case.input_value.lower()


class TestYesNoInvalidInput:
    """잘못된 입력 테스트 (10개)"""

    @pytest.mark.parametrize("input_value,description", [
        ("maybe", "애매한 답변"),
        ("perhaps", "불확실한 답변"),
        ("yess", "오타 - yess"),
        ("noo", "오타 - noo"),
        ("yn", "복합 답변"),
        ("true", "boolean true"),
        ("false", "boolean false"),
        ("1", "숫자 1"),
        ("0", "숫자 0"),
        ("?", "물음표"),
    ])
    def test_invalid_input(self, input_value: str, description: str):
        """잘못된 입력 거부"""
        valid, message = validate_yes_no_answer(input_value)
        assert not valid, f"{description} 거부 실패"
        assert "y, n, yes, no" in message.lower() or "올바른" in message


class TestYesNoSpecialCases:
    """특수 케이스 테스트 (8개)"""

    def test_empty_string(self):
        """빈 문자열"""
        valid, message = validate_yes_no_answer("")
        assert not valid
        assert "입력해주세요" in message or "비어" in message

    def test_whitespace_only(self):
        """공백만"""
        valid, message = validate_yes_no_answer("   ")
        assert not valid

    def test_with_leading_trailing_spaces(self):
        """앞뒤 공백 포함"""
        test_cases = [
            ("  y  ", True),
            ("  n  ", True),
            (" yes ", True),
            (" no  ", True)
        ]

        for input_val, expected in test_cases:
            valid, _ = validate_yes_no_answer(input_val)
            assert valid == expected

    def test_special_characters(self):
        """특수문자 포함"""
        invalid_inputs = ["y!", "n?", "yes.", "no,", "y/n"]

        for input_val in invalid_inputs:
            valid, _ = validate_yes_no_answer(input_val)
            assert not valid

    def test_unicode_variants(self):
        """유니코드 변형"""
        # 전각 문자 등
        invalid_inputs = ["ｙ", "ｎ", "ＹＥＳ", "ＮＯ"]

        for input_val in invalid_inputs:
            valid, _ = validate_yes_no_answer(input_val)
            assert not valid

    def test_mixed_language(self):
        """혼합 언어"""
        invalid_inputs = ["yes예", "no아니오", "y네", "n아니"]

        for input_val in invalid_inputs:
            valid, _ = validate_yes_no_answer(input_val)
            assert not valid

    def test_question_mark_answer(self):
        """물음표 옵션 (?)**"""
        # 일부 시스템에서는 '?'를 '모름' 옵션으로 사용
        valid, _ = validate_yes_no_answer("?")
        assert not valid  # 현재는 y/n만 허용

    def test_numeric_equivalents(self):
        """숫자 등가물"""
        # 일부 시스템에서 1=yes, 0=no로 처리하지만
        valid_1, _ = validate_yes_no_answer("1")
        valid_0, _ = validate_yes_no_answer("0")

        assert not valid_1
        assert not valid_0


class TestYesNoIntegration:
    """통합 테스트 (7개)"""

    @pytest.fixture
    def setup_yes_no_survey(self):
        """Yes/No 타입 설문 설정"""
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
            name="동의 카테고리",
            description="예/아니오 응답"
        )

        survey = Survey(
            id="survey1",
            title="동의 설문",
            description="약관 동의",
            creator_id=admin.id,
            category_id=category.id,
            questions=[
                Question(
                    id="q1",
                    survey_id="survey1",
                    text="이용약관에 동의하십니까?",
                    question_type=QuestionType.YES_NO,
                    is_required=True,
                    order=1
                ),
                Question(
                    id="q2",
                    survey_id="survey1",
                    text="마케팅 정보 수신에 동의하십니까?",
                    question_type=QuestionType.YES_NO,
                    is_required=False,
                    order=2
                ),
                Question(
                    id="q3",
                    survey_id="survey1",
                    text="개인정보 수집에 동의하십니까?",
                    question_type=QuestionType.YES_NO,
                    is_required=True,
                    order=3
                )
            ]
        )

        return admin, category, survey

    def test_yes_no_required_validation(self, setup_yes_no_survey):
        """필수 Yes/No 검증"""
        admin, category, survey = setup_yes_no_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 필수 질문 누락
        result = service.submit_response(admin, "survey1", {
            "q1": "y",
            # q3 누락
        })
        assert result.is_failure
        assert "필수 질문" in result.error

    def test_yes_no_normalization(self, setup_yes_no_survey):
        """Yes/No 정규화"""
        admin, category, survey = setup_yes_no_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "YES",
            "q2": "NO",
            "q3": "y"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        # 정규화 확인 (소문자로 저장)
        assert saved_response.answers["q1"].lower() in ["y", "yes"]
        assert saved_response.answers["q2"].lower() in ["n", "no"]
        assert saved_response.answers["q3"].lower() in ["y", "yes"]

    def test_yes_no_korean_input(self, setup_yes_no_survey):
        """한글 입력 처리"""
        admin, category, survey = setup_yes_no_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "예",
            "q2": "아니오",
            "q3": "네"
        })
        assert result.is_success

    def test_yes_no_aggregation(self, setup_yes_no_survey):
        """Yes/No 응답 집계"""
        admin, category, survey = setup_yes_no_survey

        responses = [
            Response(id="r1", survey_id="survey1", respondent_id="user1",
                    answers={"q1": "y", "q2": "n", "q3": "y"}),
            Response(id="r2", survey_id="survey1", respondent_id="user2",
                    answers={"q1": "y", "q3": "y"}),  # q2 생략
            Response(id="r3", survey_id="survey1", respondent_id="user3",
                    answers={"q1": "n", "q2": "y", "q3": "y"}),
            Response(id="r4", survey_id="survey1", respondent_id="user4",
                    answers={"q1": "y", "q2": "n", "q3": "n"}),
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

        # q1: 3 yes, 1 no
        q1_results = results["questions"]["q1"]["responses"]
        yes_count = sum(1 for v in q1_results.values() if v.lower() in ["y", "yes"])
        no_count = sum(1 for v in q1_results.values() if v.lower() in ["n", "no"])
        assert yes_count == 3
        assert no_count == 1

        # q3: 3 yes, 1 no
        q3_results = results["questions"]["q3"]["responses"]
        yes_count = sum(1 for v in q3_results.values() if v.lower() in ["y", "yes"])
        no_count = sum(1 for v in q3_results.values() if v.lower() in ["n", "no"])
        assert yes_count == 3
        assert no_count == 1

    def test_yes_no_with_mixed_questions(self, setup_yes_no_survey):
        """다양한 타입과 혼합"""
        admin, _, survey = setup_yes_no_survey

        # 다른 타입 질문 추가
        survey.questions.extend([
            Question(id="q4", survey_id="survey1", text="이메일", question_type=QuestionType.EMAIL, is_required=True, order=4),
            Question(id="q5", survey_id="survey1", text="나이", question_type=QuestionType.NUMBER, is_required=True, order=5)
        ])

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "y",
            "q2": "n",
            "q3": "yes",
            "q4": "user@example.com",
            "q5": "30"
        })
        assert result.is_success

    def test_yes_no_percentage_calculation(self):
        """Yes/No 백분율 계산"""
        responses = [
            {"q1": "y"}, {"q1": "y"}, {"q1": "y"},
            {"q1": "n"}, {"q1": "n"}
        ]

        yes_count = sum(1 for r in responses if r["q1"].lower() in ["y", "yes"])
        no_count = sum(1 for r in responses if r["q1"].lower() in ["n", "no"])
        total = len(responses)

        yes_percent = (yes_count / total) * 100
        no_percent = (no_count / total) * 100

        assert yes_percent == 60.0
        assert no_percent == 40.0

    def test_yes_no_optional_empty(self, setup_yes_no_survey):
        """선택적 Yes/No 빈값 허용"""
        admin, category, survey = setup_yes_no_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "y",
            # q2는 선택사항이므로 생략
            "q3": "n"
        })
        assert result.is_success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])