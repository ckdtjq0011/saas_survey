import pytest
from domain.value_objects.types import QuestionType


class TestQuestionTypeEnum:
    """QuestionType enum 테스트"""

    def test_get_all_values(self):
        """모든 enum value 반환 테스트

        시나리오:
            1. get_all_values() 호출
            2. 모든 질문 유형 value가 포함되어 있는지 검증
        """
        values = QuestionType.get_all_values()

        assert isinstance(values, list)
        assert len(values) == 3
        assert "text" in values
        assert "rating" in values
        assert "choice" in values

    def test_get_choices_for_ui(self):
        """UI 선택지 생성 테스트

        시나리오:
            1. get_choices_for_ui() 호출
            2. UI에서 사용할 수 있는 선택지 리스트 검증
        """
        choices = QuestionType.get_choices_for_ui()

        assert isinstance(choices, list)
        assert len(choices) == 3
        assert all(isinstance(choice, str) for choice in choices)

    def test_from_value_valid(self):
        """유효한 값으로부터 QuestionType 생성 테스트

        시나리오:
            1. 각 유효한 값("text", "rating", "choice")으로 from_value() 호출
            2. 올바른 QuestionType enum 멤버가 반환되는지 검증
        """
        text_type = QuestionType.from_value("text")
        assert text_type == QuestionType.TEXT

        rating_type = QuestionType.from_value("rating")
        assert rating_type == QuestionType.RATING

        choice_type = QuestionType.from_value("choice")
        assert choice_type == QuestionType.MULTIPLE_CHOICE

    def test_from_value_invalid(self):
        """잘못된 값으로부터 QuestionType 생성 시 예외 발생 테스트

        시나리오:
            1. 잘못된 값으로 from_value() 호출
            2. ValueError 예외 발생 검증
        """
        with pytest.raises(ValueError):
            QuestionType.from_value("invalid_type")

        with pytest.raises(ValueError):
            QuestionType.from_value("TEXT")

        with pytest.raises(ValueError):
            QuestionType.from_value("")

    def test_display_name(self):
        """표시 이름 반환 테스트

        시나리오:
            1. 각 QuestionType의 display_name 프로퍼티 호출
            2. 올바른 한글 이름이 반환되는지 검증
        """
        assert QuestionType.TEXT.display_name == "텍스트"
        assert QuestionType.RATING.display_name == "평점"
        assert QuestionType.MULTIPLE_CHOICE.display_name == "객관식"

    def test_description(self):
        """설명 반환 테스트

        시나리오:
            1. 각 QuestionType의 description 프로퍼티 호출
            2. 올바른 설명이 반환되는지 검증
        """
        assert QuestionType.TEXT.description == "자유롭게 텍스트로 답변"
        assert QuestionType.RATING.description == "1-5점 척도로 평가"
        assert QuestionType.MULTIPLE_CHOICE.description == "제시된 선택지 중 하나를 선택"

    def test_enum_value(self):
        """Enum value 속성 테스트

        시나리오:
            1. 각 QuestionType의 value 속성 확인
            2. 올바른 문자열 값이 할당되어 있는지 검증
        """
        assert QuestionType.TEXT.value == "text"
        assert QuestionType.RATING.value == "rating"
        assert QuestionType.MULTIPLE_CHOICE.value == "choice"

    def test_enum_equality(self):
        """Enum 동등성 비교 테스트

        시나리오:
            1. 동일한 QuestionType끼리 비교
            2. 다른 QuestionType끼리 비교
            3. 올바르게 동등성 판단이 되는지 검증
        """
        assert QuestionType.TEXT == QuestionType.TEXT
        assert QuestionType.RATING == QuestionType.RATING
        assert QuestionType.MULTIPLE_CHOICE == QuestionType.MULTIPLE_CHOICE

        assert QuestionType.TEXT != QuestionType.RATING
        assert QuestionType.TEXT != QuestionType.MULTIPLE_CHOICE
        assert QuestionType.RATING != QuestionType.MULTIPLE_CHOICE

    def test_enum_iteration(self):
        """Enum 순회 테스트

        시나리오:
            1. QuestionType의 모든 멤버 순회
            2. 3개의 멤버가 존재하는지 검증
        """
        members = list(QuestionType)
        assert len(members) == 3
        assert QuestionType.TEXT in members
        assert QuestionType.RATING in members
        assert QuestionType.MULTIPLE_CHOICE in members
