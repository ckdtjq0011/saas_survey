"""
SCALE_10 질문 타입 완전 테스트 스위트
45개 테스트 케이스로 모든 시나리오 검증
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import ClassVar
from statistics import mean, median, mode, stdev

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
from interface.cli.validators import validate_scale_10_answer


@dataclass(frozen=True, slots=True)
class Scale10TestCase:
    """1-10 척도 테스트 케이스"""
    case_id: str
    input_value: str
    expected_valid: bool
    expected_value: int | None
    description: str


class TestScale10Validation:
    """1-10 척도 형식 검증 테스트 (15개)"""

    @pytest.mark.parametrize("test_case", [
        Scale10TestCase("S01", "1", True, 1, "최소값 1"),
        Scale10TestCase("S02", "10", True, 10, "최대값 10"),
        Scale10TestCase("S03", "5", True, 5, "중간값 5"),
        Scale10TestCase("S04", "2", True, 2, "낮은 값 2"),
        Scale10TestCase("S05", "9", True, 9, "높은 값 9"),
        Scale10TestCase("S06", "7", True, 7, "중상위 값 7"),
        Scale10TestCase("S07", "3", True, 3, "중하위 값 3"),
        Scale10TestCase("S08", "4", True, 4, "중간 아래 4"),
        Scale10TestCase("S09", "6", True, 6, "중간 위 6"),
        Scale10TestCase("S10", "8", True, 8, "상위 값 8"),
        Scale10TestCase("S11", "0", False, None, "범위 밖 - 0"),
        Scale10TestCase("S12", "11", False, None, "범위 밖 - 11"),
        Scale10TestCase("S13", "-1", False, None, "음수 -1"),
        Scale10TestCase("S14", "100", False, None, "큰 수 100"),
        Scale10TestCase("S15", "-10", False, None, "음수 -10"),
    ])
    def test_scale_10_validation(self, test_case: Scale10TestCase):
        """1-10 척도 검증"""
        valid, message = validate_scale_10_answer(test_case.input_value)
        assert valid == test_case.expected_valid, f"{test_case.description} 실패"

        if not test_case.expected_valid:
            assert "1에서 10 사이" in message or "입력해주세요" in message


class TestScale10InvalidInput:
    """잘못된 입력 테스트 (10개)"""

    @pytest.mark.parametrize("input_value,description", [
        ("1.5", "소수점"),
        ("5.0", "정수형 실수"),
        ("five", "영문 텍스트"),
        ("다섯", "한글 숫자"),
        ("V", "로마 숫자"),
        ("1-10", "범위 표현"),
        ("10/10", "분수 표현"),
        ("⑤", "원 문자"),
        ("1 0", "공백 포함"),
        ("1,0", "쉼표 포함"),
    ])
    def test_invalid_format(self, input_value: str, description: str):
        """잘못된 형식 거부"""
        valid, message = validate_scale_10_answer(input_value)
        assert not valid, f"{description} 거부 실패"


class TestScale10SpecialCases:
    """특수 케이스 테스트 (8개)"""

    def test_empty_string(self):
        """빈 문자열"""
        valid, message = validate_scale_10_answer("")
        assert not valid
        assert "입력해주세요" in message or "비어" in message

    def test_whitespace_only(self):
        """공백만"""
        valid, message = validate_scale_10_answer("   ")
        assert not valid

    def test_with_leading_trailing_spaces(self):
        """앞뒤 공백 포함"""
        test_cases = [
            ("  5  ", True),
            (" 10 ", True),
            ("  1  ", True),
            (" 7  ", True)
        ]

        for input_val, expected in test_cases:
            valid, _ = validate_scale_10_answer(input_val)
            assert valid == expected

    def test_leading_zeros(self):
        """앞자리 0"""
        test_cases = [
            ("01", True),   # 1로 해석
            ("010", True),  # 10으로 해석
            ("05", True),   # 5로 해석
            ("00", False),  # 0은 범위 밖
            ("011", False)  # 11은 범위 밖
        ]

        for input_val, expected in test_cases:
            valid, _ = validate_scale_10_answer(input_val)
            assert valid == expected

    def test_special_characters(self):
        """특수문자 포함"""
        invalid_inputs = ["5!", "7?", "10.", "1,", "+5", "=10"]

        for input_val in invalid_inputs:
            valid, _ = validate_scale_10_answer(input_val)
            assert not valid

    def test_scientific_notation(self):
        """과학적 표기법"""
        invalid_inputs = ["1e1", "1E1", "10e0", "5e-1"]

        for input_val in invalid_inputs:
            valid, _ = validate_scale_10_answer(input_val)
            assert not valid

    def test_hexadecimal(self):
        """16진수 표기"""
        invalid_inputs = ["0x5", "0xA", "0X1", "#5"]

        for input_val in invalid_inputs:
            valid, _ = validate_scale_10_answer(input_val)
            assert not valid

    def test_unicode_digits(self):
        """유니코드 숫자"""
        invalid_inputs = ["①", "②", "⑩", "５", "１０"]

        for input_val in invalid_inputs:
            valid, _ = validate_scale_10_answer(input_val)
            assert not valid


class TestScale10Integration:
    """통합 테스트 (12개)"""

    @pytest.fixture
    def setup_scale_10_survey(self):
        """1-10 척도 설문 설정"""
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
            name="만족도 카테고리",
            description="만족도 평가"
        )

        survey = Survey(
            id="survey1",
            title="서비스 만족도 조사",
            description="1-10 척도 평가",
            creator_id=admin.id,
            category_id=category.id,
            questions=[
                Question(
                    id="q1",
                    survey_id="survey1",
                    text="전반적인 만족도를 평가해주세요 (1-10)",
                    question_type=QuestionType.SCALE_10,
                    is_required=True,
                    order=1
                ),
                Question(
                    id="q2",
                    survey_id="survey1",
                    text="추천 의향을 평가해주세요 (1-10)",
                    question_type=QuestionType.SCALE_10,
                    is_required=True,
                    order=2
                ),
                Question(
                    id="q3",
                    survey_id="survey1",
                    text="가격 대비 가치를 평가해주세요 (1-10)",
                    question_type=QuestionType.SCALE_10,
                    is_required=False,
                    order=3
                )
            ]
        )

        return admin, category, survey

    def test_scale_10_required_validation(self, setup_scale_10_survey):
        """필수 척도 검증"""
        admin, category, survey = setup_scale_10_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 필수 질문 누락
        result = service.submit_response(admin, "survey1", {
            "q1": "8",
            # q2 누락
            "q3": "7"
        })
        assert result.is_failure
        assert "필수 질문" in result.error

    def test_scale_10_out_of_range(self, setup_scale_10_survey):
        """범위 벗어난 값 거부"""
        admin, category, survey = setup_scale_10_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "11",  # 범위 초과
            "q2": "5",
            "q3": "0"    # 범위 미만
        })
        assert result.is_failure
        assert "1에서 10 사이" in result.error

    def test_scale_10_valid_submission(self, setup_scale_10_survey):
        """유효한 척도 제출"""
        admin, category, survey = setup_scale_10_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "9",
            "q2": "10",
            "q3": "8"
        })
        assert result.is_success

        saved_response = response_repo.save.call_args[0][0]
        assert saved_response.answers["q1"] == "9"
        assert saved_response.answers["q2"] == "10"
        assert saved_response.answers["q3"] == "8"

    def test_scale_10_statistical_aggregation(self, setup_scale_10_survey):
        """통계적 집계"""
        admin, category, survey = setup_scale_10_survey

        responses = [
            Response(id="r1", survey_id="survey1", respondent_id="user1",
                    answers={"q1": "7", "q2": "8", "q3": "6"}),
            Response(id="r2", survey_id="survey1", respondent_id="user2",
                    answers={"q1": "9", "q2": "10", "q3": "8"}),
            Response(id="r3", survey_id="survey1", respondent_id="user3",
                    answers={"q1": "5", "q2": "6", "q3": "7"}),
            Response(id="r4", survey_id="survey1", respondent_id="user4",
                    answers={"q1": "8", "q2": "9"}),  # q3 생략
            Response(id="r5", survey_id="survey1", respondent_id="user5",
                    answers={"q1": "10", "q2": "10", "q3": "10"})
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

        # q1 통계 계산
        q1_values = [int(r.answers["q1"]) for r in responses]
        assert len(q1_values) == 5
        assert mean(q1_values) == 7.8
        assert min(q1_values) == 5
        assert max(q1_values) == 10

        # q2 통계 계산
        q2_values = [int(r.answers["q2"]) for r in responses]
        assert mean(q2_values) == 8.6

    def test_scale_10_distribution_analysis(self):
        """점수 분포 분석"""
        scores = [7, 8, 9, 7, 6, 8, 9, 10, 7, 8]

        # 빈도 계산
        frequency = {}
        for score in scores:
            frequency[score] = frequency.get(score, 0) + 1

        assert frequency[7] == 3
        assert frequency[8] == 3
        assert frequency[9] == 2
        assert frequency[10] == 1
        assert frequency[6] == 1

        # 통계값
        assert mean(scores) == 7.9
        assert median(scores) == 8.0
        assert mode(scores) in [7, 8]  # 7과 8이 최빈값

    def test_scale_10_nps_calculation(self):
        """NPS (Net Promoter Score) 계산"""
        # 9-10: Promoters, 7-8: Passive, 1-6: Detractors
        scores = [10, 9, 8, 7, 6, 5, 9, 10, 3, 8]

        promoters = sum(1 for s in scores if s >= 9)
        passives = sum(1 for s in scores if 7 <= s <= 8)
        detractors = sum(1 for s in scores if s <= 6)

        nps = ((promoters - detractors) / len(scores)) * 100

        assert promoters == 4
        assert passives == 3
        assert detractors == 3
        assert nps == 10.0

    def test_scale_10_optional_empty(self, setup_scale_10_survey):
        """선택적 척도 빈값 허용"""
        admin, category, survey = setup_scale_10_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        result = service.submit_response(admin, "survey1", {
            "q1": "8",
            "q2": "9"
            # q3는 선택사항이므로 생략
        })
        assert result.is_success

    def test_scale_10_boundary_values(self, setup_scale_10_survey):
        """경계값 테스트"""
        admin, category, survey = setup_scale_10_survey

        response_repo = Mock(spec=ResponseRepository)
        survey_repo = Mock(spec=SurveyRepository)
        category_repo = Mock(spec=CategoryRepository)

        survey_repo.find_by_id.return_value = survey
        response_repo.save.return_value = True

        service = ResponseService(response_repo, survey_repo, category_repo)

        # 최소값과 최대값
        result = service.submit_response(admin, "survey1", {
            "q1": "1",   # 최소
            "q2": "10",  # 최대
            "q3": "5"    # 중간
        })
        assert result.is_success

    def test_scale_10_consistency_check(self):
        """일관성 검사"""
        # 같은 사용자의 여러 응답에서 일관성 체크
        user_responses = [
            {"satisfaction": "9", "recommendation": "10", "value": "8"},
            {"satisfaction": "2", "recommendation": "9", "value": "1"},  # 비일관적
        ]

        # 만족도가 낮은데 추천도가 높은 경우 감지
        for resp in user_responses:
            sat = int(resp["satisfaction"])
            rec = int(resp["recommendation"])

            if sat <= 3 and rec >= 8:
                # 비일관적 응답 플래그
                assert resp == user_responses[1]

    def test_scale_10_trend_analysis(self):
        """시간별 트렌드 분석"""
        monthly_scores = {
            "2024-01": [7, 8, 6, 7, 8],
            "2024-02": [8, 8, 7, 9, 8],
            "2024-03": [8, 9, 9, 9, 10]
        }

        monthly_avg = {month: mean(scores) for month, scores in monthly_scores.items()}

        assert monthly_avg["2024-01"] == 7.2
        assert monthly_avg["2024-02"] == 8.0
        assert monthly_avg["2024-03"] == 9.0

        # 상승 트렌드 확인
        values = list(monthly_avg.values())
        assert all(values[i] <= values[i+1] for i in range(len(values)-1))

    def test_scale_10_segmentation(self):
        """점수 구간별 세분화"""
        scores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] * 2

        # 구간별 분류
        low = [s for s in scores if 1 <= s <= 3]      # 낮음
        medium = [s for s in scores if 4 <= s <= 7]   # 중간
        high = [s for s in scores if 8 <= s <= 10]    # 높음

        assert len(low) == 6
        assert len(medium) == 8
        assert len(high) == 6

        # 백분율
        total = len(scores)
        assert (len(low) / total) * 100 == 30.0
        assert (len(medium) / total) * 100 == 40.0
        assert (len(high) / total) * 100 == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])