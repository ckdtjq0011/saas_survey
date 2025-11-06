from enum import Enum


class QuestionType(Enum):
    """질문 유형을 정의하는 열거형입니다.

    Attributes:
        TEXT: 텍스트 답변 질문
        RATING: 평점 답변 질문 (1-5)
        MULTIPLE_CHOICE: 객관식 질문
        DATE: 날짜 입력 질문
        NUMBER: 숫자 입력 질문
        EMAIL: 이메일 입력 질문
        YES_NO: 예/아니오 선택 질문
        SCALE_10: 10점 척도 질문 (1-10)
        MULTI_SELECT: 다중 선택 질문
    """
    TEXT = "text"
    RATING = "rating"
    MULTIPLE_CHOICE = "choice"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    YES_NO = "yes_no"
    SCALE_10 = "scale_10"
    MULTI_SELECT = "multi_select"

    @property
    def display_name(self) -> str:
        """사용자에게 표시할 이름을 반환합니다.

        Returns:
            한글 표시 이름
        """
        display_names = {
            QuestionType.TEXT: "텍스트",
            QuestionType.RATING: "평점 (1-5)",
            QuestionType.MULTIPLE_CHOICE: "객관식",
            QuestionType.DATE: "날짜",
            QuestionType.NUMBER: "숫자",
            QuestionType.EMAIL: "이메일",
            QuestionType.YES_NO: "예/아니오",
            QuestionType.SCALE_10: "10점 척도",
            QuestionType.MULTI_SELECT: "다중 선택",
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
            QuestionType.DATE: "날짜를 선택하여 입력 (YYYY-MM-DD)",
            QuestionType.NUMBER: "숫자를 입력",
            QuestionType.EMAIL: "이메일 주소를 입력",
            QuestionType.YES_NO: "예 또는 아니오를 선택",
            QuestionType.SCALE_10: "1-10점 척도로 평가",
            QuestionType.MULTI_SELECT: "제시된 선택지 중 여러 개를 선택 가능",
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
