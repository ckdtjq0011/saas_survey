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
