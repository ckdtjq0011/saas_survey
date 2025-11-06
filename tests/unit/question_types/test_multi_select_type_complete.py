"""
MULTI_SELECT 질문 타입 완전 테스트 스위트
50개 테스트 케이스로 모든 시나리오 검증
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
from interface.cli.validators import validate_multi_select_answer


@dataclass(frozen=True, slots=True)
class MultiSelectTestCase:
    """다중 선택 테스트 케이스"""
    case_id: str
    input_value: str
    options: list[str] | None
    expected_valid: bool
    expected_selections: list[str] | None
    description: str


class TestMultiSelectValidation:
    """다중 선택 형식 검증 테스트 (20개)"""

    @pytest.mark.parametrize("test_case", [
        MultiSelectTestCase("MS01", "1,2", ["옵션1", "옵션2", "옵션3"], True, ["1", "2"], "정상적인 복수 선택"),
        MultiSelectTestCase("MS02", "1", ["옵션1", "옵션2", "옵션3"], True, ["1"], "단일 선택"),
        MultiSelectTestCase("MS03", "1,2,3", ["옵션1", "옵션2", "옵션3"], True, ["1", "2", "3"], "모든 옵션 선택"),
        MultiSelectTestCase("MS04", "3,1,2", ["옵션1", "옵션2", "옵션3"], True, ["3", "1", "2"], "순서 바뀐 선택"),
        MultiSelectTestCase("MS05", "1, 2", ["옵션1", "옵션2", "옵션3"], True, ["1", "2"], "공백 포함"),
        MultiSelectTestCase("MS06", "  1,2  ", ["옵션1", "옵션2", "옵션3"], True, ["1", "2"], "앞뒤 공백"),
        MultiSelectTestCase("MS07", "2", ["A", "B", "C", "D", "E"], True, ["2"], "5개 옵션 중 선택"),
        MultiSelectTestCase("MS08", "1,3,5", ["A", "B", "C", "D", "E"], True, ["1", "3", "5"], "띄엄띄엄 선택"),
        MultiSelectTestCase("MS09", "0", ["옵션1", "옵션2"], False, None, "0번 선택 (잘못된 번호)"),
        MultiSelectTestCase("MS10", "4", ["옵션1", "옵션2", "옵션3"], False, None, "범위 초과 선택"),
        MultiSelectTestCase("MS11", "1,1", ["옵션1", "옵션2"], False, None, "중복 선택"),
        MultiSelectTestCase("MS12", "1,2,2", ["옵션1", "옵션2", "옵션3"], False, None, "부분 중복"),
        MultiSelectTestCase("MS13", "-1", ["옵션1", "옵션2"], False, None, "음수 선택"),
        MultiSelectTestCase("MS14", "1.5", ["옵션1", "옵션2"], False, None, "소수점 선택"),
        MultiSelectTestCase("MS15", "a,b", ["옵션1", "옵션2"], False, None, "문자 선택"),
        MultiSelectTestCase("MS16", "1-3", ["옵션1", "옵션2", "옵션3"], False, None, "범위 표현"),
        MultiSelectTestCase("MS17", "1;2", ["옵션1", "옵션2"], False, None, "세미콜론 구분"),
        MultiSelectTestCase("MS18", "1 2", ["옵션1", "옵션2"], False, None, "공백 구분"),
        MultiSelectTestCase("MS19", "1/2", ["옵션1", "옵션2"], False, None, "슬래시 구분"),
        MultiSelectTestCase("MS20", "1+2", ["옵션1", "옵션2"], False, None, "플러스 구분")
    ])
    def test_multi_select_validation(self, test_case: MultiSelectTestCase):
        """다중 선택 형식 검증"""
        valid, message = validate_multi_select_answer(test_case.input_value, test_case.options)
        assert valid == test_case.expected_valid, f"{test_case.description} 실패"

        if not test_case.expected_valid:
            assert "유효" in message or "쉼표" in message or "중복" in message


class TestMultiSelectSpecialCases:
    """특수 케이스 테스트 (15개)"""

    def test_empty_string(self):
        """빈 문자열"""
        valid, message = validate_multi_select_answer("", ["옵션1", "옵션2"])
        assert not valid
        assert "입력해주세요" in message or "비어" in message

    def test_whitespace_only(self):
        """공백만"""
        valid, message = validate_multi_select_answer("   ", ["옵션1", "옵션2"])
        assert not valid

    def test_comma_only(self):
        """쉼표만"""
        valid, message = validate_multi_select_answer(",", ["옵션1", "옵션2"])
        assert not valid

    def test_multiple_commas(self):
        """연속된 쉼표"""
        valid, message = validate_multi_select_answer("1,,2", ["옵션1", "옵션2", "옵션3"])
        assert not valid

    def test_trailing_comma(self):
        """끝에 쉼표"""
        valid, message = validate_multi_select_answer("1,2,", ["옵션1", "옵션2", "옵션3"])
        assert not valid

    def test_leading_comma(self):
        """앞에 쉼표"""
        valid, message = validate_multi_select_answer(",1,2", ["옵션1", "옵션2", "옵션3"])
        assert not valid

    def test_no_options_provided(self):
        """옵션 없이 검증"""
        valid, message = validate_multi_select_answer("1,2", None)
        # 옵션이 없으면 검증 불가
        assert not valid

    def test_empty_options_list(self):
        """빈 옵션 리스트"""
        valid, message = validate_multi_select_answer("1", [])
        assert not valid

    def test_large_option_set(self):
        """많은 옵션"""
        options = [f"옵션{i}" for i in range(1, 21)]  # 20개 옵션
        valid, _ = validate_multi_select_answer("1,5,10,15,20", options)
        assert valid

    def test_all_options_selected(self):
        """모든 옵션 선택"""
        options = ["A", "B", "C", "D", "E"]
        valid, _ = validate_multi_select_answer("1,2,3,4,5", options)
        assert valid

    def test_special_characters_in_input(self):
        """특수문자 포함 입력"""
        invalid_inputs = [
            "1&2",
            "1|2",
            "1*2",
            "1#2",
            "1@2"
        ]

        options = ["옵션1", "옵션2", "옵션3"]
        for input_val in invalid_inputs:
            valid, _ = validate_multi_select_answer(input_val, options)
            assert not valid

    def test_mixed_valid_invalid(self):
        """유효/무효 혼합"""
        options = ["옵션1", "옵션2", "옵션3"]
        valid, message = validate_multi_select_answer("1,2,4", options)  # 4는 범위 초과
        assert not valid
        assert "유효" in message

    def test_korean_number_input(self):
        """한글 숫자 입력"""
        options = ["옵션1", "옵션2", "옵션3"]
        korean_inputs = ["일,이", "하나,둘", "첫째,둘째"]

        for input_val in korean_inputs:
            valid, _ = validate_multi_select_answer(input_val, options)
            assert not valid

    def test_roman_numerals(self):
        """로마 숫자"""
        options = ["옵션1", "옵션2", "옵션3"]
        valid, _ = validate_multi_select_answer("I,II,III", options)
        assert not valid

    def test_unicode_digits(self):
        """유니코드 숫자"""
        options = ["옵션1", "옵션2", "옵션3"]
        valid, _ = validate_multi_select_answer("①,②", options)
        assert not valid


class TestMultiSelectIntegration:
    """통합 테스트 (15개)"""

    @pytest.fixture
    def setup_multi_select_survey(self):
        """다중 선택 설문 설정"""
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
            name="선호도 카테고리",
            description="다중 선택 선호도"
        )

        survey = Survey(
            id="survey1",
            title="기능 선호도 조사",
            description="원하는 기능 선택",
            creator_id=admin.id,
            category_id=category.id,
            questions=[
                Question(
                    id="q1",
                    survey_id="survey1",
                    text="선호하는 기능을 모두 선택하세요",
                    question_type=QuestionType.MULTI_SELECT,
                    options=["검색", "필터", "정렬", "내보내기", "가져오기"],
                    is_required=True,
                    order=1
                ),
                Question(
                    id="q2",
                    survey_id="survey1",
                    text="사용 중인 브라우저를 모두 선택하세요",
                    question_type=QuestionType.MULTI_SELECT,
                    options=["Chrome", "Firefox", "Safari", "Edge"],
                    is_required=False,
                    order=2
                ),
                Question(
                    id="q3",
                    survey_id="survey1",
                    text="관심 분야를 선택하세요",
                    question_type=QuestionType.MULTI_SELECT,
                    options=["개발", "디자인", "마케팅", "영업", "운영"],
                    is_required=True,
                    order=3
                )
            ]
        )

        return admin, category, survey

    def test_multi_select_required_validation(self, setup_multi_select_survey):
        """필수 다중 선택 검증"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 필수 질문 누락
        result = service.submit_response(admin, "survey1", {
            "q1": "1,2",
            # q3 누락
        })
        assert result.is_failure
        assert "필수 질문" in result.error

    def test_multi_select_invalid_option(self, setup_multi_select_survey):
        """잘못된 옵션 번호"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "1,6",  # 6번 옵션은 없음
            "q2": "1,2",
            "q3": "1"
        })
        assert result.is_failure
        assert "유효" in result.error

    def test_multi_select_duplicate_selection(self, setup_multi_select_survey):
        """중복 선택 거부"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "1,2,1",  # 1번 중복
            "q2": "1",
            "q3": "3"
        })
        assert result.is_failure
        assert "중복" in result.error

    def test_multi_select_valid_submission(self, setup_multi_select_survey):
        """유효한 다중 선택 제출"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "1,3,5",
            "q2": "1,2,4",
            "q3": "2,3"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        assert saved_response.answers["q1"] == "1,3,5"
        assert saved_response.answers["q2"] == "1,2,4"
        assert saved_response.answers["q3"] == "2,3"

    def test_multi_select_single_choice(self, setup_multi_select_survey):
        """단일 선택도 허용"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "2",  # 단일 선택
            "q2": "3",
            "q3": "1"
        })
        assert result.is_success

    def test_multi_select_optional_empty(self, setup_multi_select_survey):
        """선택적 다중 선택 빈값 허용"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "1,2",
            # q2는 선택사항이므로 생략
            "q3": "4,5"
        })
        assert result.is_success

    def test_multi_select_all_options(self, setup_multi_select_survey):
        """모든 옵션 선택"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "1,2,3,4,5",  # 모든 옵션
            "q2": "1,2,3,4",    # 모든 옵션
            "q3": "1,2,3,4,5"   # 모든 옵션
        })
        assert result.is_success

    def test_multi_select_aggregation(self, setup_multi_select_survey):
        """다중 선택 응답 집계"""
        admin, category, survey = setup_multi_select_survey

        responses = [
            Response(id="r1", survey_id="survey1", respondent_id="user1",
                    answers={"q1": "1,2", "q2": "1", "q3": "2,3"}),
            Response(id="r2", survey_id="survey1", respondent_id="user2",
                    answers={"q1": "2,3", "q3": "1,2"}),  # q2 생략
            Response(id="r3", survey_id="survey1", respondent_id="user3",
                    answers={"q1": "1,3,5", "q2": "2,3", "q3": "3,4"}),
            Response(id="r4", survey_id="survey1", respondent_id="user4",
                    answers={"q1": "2", "q2": "1,4", "q3": "5"})
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

        # q1 선택 빈도 분석
        q1_responses = results["questions"]["q1"]["responses"]
        assert len(q1_responses) == 4

        # 각 옵션별 선택 횟수 계산
        option_counts = {}
        for response_str in q1_responses.values():
            for opt in response_str.split(","):
                opt = opt.strip()
                option_counts[opt] = option_counts.get(opt, 0) + 1

        assert option_counts.get("1") == 2  # 옵션1: 2번 선택
        assert option_counts.get("2") == 3  # 옵션2: 3번 선택
        assert option_counts.get("3") == 2  # 옵션3: 2번 선택

    def test_multi_select_frequency_analysis(self):
        """선택 빈도 분석"""
        responses = [
            "1,2,3",
            "2,3",
            "1,3,4",
            "2,4,5",
            "1,2,3,4,5"
        ]

        # 옵션별 선택 빈도
        frequency = {}
        for response in responses:
            for option in response.split(","):
                option = option.strip()
                frequency[option] = frequency.get(option, 0) + 1

        assert frequency["1"] == 3
        assert frequency["2"] == 3
        assert frequency["3"] == 4
        assert frequency["4"] == 3
        assert frequency["5"] == 2

        # 가장 인기 있는 옵션
        most_popular = max(frequency, key=frequency.get)
        assert most_popular == "3"

    def test_multi_select_combination_analysis(self):
        """조합 분석"""
        responses = [
            "1,2",
            "1,2",
            "2,3",
            "1,3",
            "1,2,3"
        ]

        # 조합 빈도
        combinations = {}
        for response in responses:
            combinations[response] = combinations.get(response, 0) + 1

        assert combinations["1,2"] == 2
        assert combinations["2,3"] == 1
        assert combinations["1,3"] == 1
        assert combinations["1,2,3"] == 1

        # 가장 흔한 조합
        most_common = max(combinations, key=combinations.get)
        assert most_common == "1,2"

    def test_multi_select_order_preservation(self, setup_multi_select_survey):
        """선택 순서 보존"""
        admin, category, survey = setup_multi_select_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "3,1,2",  # 특정 순서
            "q2": "4,2,1",
            "q3": "5,3,1"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        # 순서가 보존되어야 함
        assert saved_response.answers["q1"] == "3,1,2"
        assert saved_response.answers["q2"] == "4,2,1"
        assert saved_response.answers["q3"] == "5,3,1"

    def test_multi_select_with_mixed_types(self):
        """다른 질문 타입과 혼합"""
        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        survey = Survey(
            id="survey1",
            title="혼합 설문",
            description="다양한 타입",
            creator_id=admin.id,
            questions=[
                Question(id="q1", survey_id="survey1", text="이름", question_type=QuestionType.TEXT, is_required=True, order=1),
                Question(id="q2", survey_id="survey1", text="선호 기능", question_type=QuestionType.MULTI_SELECT,
                        options=["A", "B", "C"], is_required=True, order=2),
                Question(id="q3", survey_id="survey1", text="만족도", question_type=QuestionType.SCALE_10, is_required=True, order=3)
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
            "q2": "1,3",
            "q3": "8"
        })
        assert result.is_success

    def test_multi_select_percentage_calculation(self):
        """선택 비율 계산"""
        total_responses = 100
        option_selections = {
            "1": 75,  # 75% 선택
            "2": 60,  # 60% 선택
            "3": 45,  # 45% 선택
            "4": 30,  # 30% 선택
            "5": 15   # 15% 선택
        }

        percentages = {opt: (count/total_responses)*100
                      for opt, count in option_selections.items()}

        assert percentages["1"] == 75.0
        assert percentages["2"] == 60.0
        assert percentages["3"] == 45.0
        assert percentages["4"] == 30.0
        assert percentages["5"] == 15.0

        # 총합이 100%를 초과 (다중 선택이므로)
        total_percentage = sum(percentages.values())
        assert total_percentage > 100

    def test_multi_select_correlation_analysis(self):
        """선택 간 상관관계 분석"""
        # 옵션1을 선택한 사람이 옵션2도 선택하는 경향
        responses = [
            {"options": "1,2,3"},
            {"options": "1,2"},
            {"options": "1,3"},
            {"options": "2,3"},
            {"options": "1,2,4"}
        ]

        # 옵션1 선택자 중 옵션2도 선택한 비율
        opt1_users = [r for r in responses if "1" in r["options"]]
        opt1_and_2 = [r for r in opt1_users if "2" in r["options"]]

        correlation = len(opt1_and_2) / len(opt1_users) if opt1_users else 0
        assert correlation == 0.75  # 75% 상관관계


if __name__ == "__main__":
    pytest.main([__file__, "-v"])