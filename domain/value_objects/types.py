from enum import Enum


class QuestionType(Enum):
    """질문 유형을 정의하는 열거형입니다.

    Attributes:
        TEXT: 텍스트 답변 질문
        RATING: 평점 답변 질문 (1-5)
        MULTIPLE_CHOICE: 객관식 질문
    """
    TEXT = "text"
    RATING = "rating"
    MULTIPLE_CHOICE = "choice"

    @property
    def display_name(self) -> str:
        """사용자에게 표시할 이름을 반환합니다.

        Returns:
            한글 표시 이름
        """
        display_names = {
            QuestionType.TEXT: "텍스트",
            QuestionType.RATING: "평점",
            QuestionType.MULTIPLE_CHOICE: "객관식",
        }
        return display_names[self]

    @property
    def description(self) -> str:
        """질문 유형의 설명을 반환합니다.

        Returns:
            유형 설명
        """
        descriptions = {
            QuestionType.TEXT: "자유롭게 텍스트로 답변",
            QuestionType.RATING: "1-5점 척도로 평가",
            QuestionType.MULTIPLE_CHOICE: "제시된 선택지 중 하나를 선택",
        }
        return descriptions[self]

    @classmethod
    def get_all_values(cls) -> list[str]:
        """모든 enum value를 리스트로 반환합니다.

        Returns:
            모든 value의 리스트
        """
        return [member.value for member in cls]

    @classmethod
    def get_choices_for_ui(cls) -> list[str]:
        """UI 선택지로 사용할 value 리스트를 반환합니다.

        Returns:
            UI 선택지 리스트
        """
        return cls.get_all_values()

    @classmethod
    def from_value(cls, value: str) -> "QuestionType":
        """문자열 값으로부터 QuestionType을 생성합니다.

        Args:
            value: 질문 유형 값

        Returns:
            QuestionType enum 멤버

        Raises:
            ValueError: 유효하지 않은 값인 경우
        """
        return cls(value)
