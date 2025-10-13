from dataclasses import dataclass
from domain.value_objects.types import QuestionType


@dataclass(frozen=True, slots=True)
class Question:
    """설문의 질문을 나타내는 엔티티입니다.

    Attributes:
        id: 질문 고유 식별자
        survey_id: 소속된 설문 식별자
        text: 질문 내용
        question_type: 질문 유형
        options: 객관식 선택지 (객관식인 경우)
    """
    id: str
    survey_id: str
    text: str
    question_type: QuestionType
    options: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "text": self.text,
            "question_type": self.question_type.value,
            "options": "|".join(self.options) if self.options else "",
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Question":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Question 엔티티 인스턴스
        """
        options_str = data.get("options", "")
        options = tuple(options_str.split("|")) if options_str else None

        return cls(
            id=data["id"],
            survey_id=data["survey_id"],
            text=data["text"],
            question_type=QuestionType(data["question_type"]),
            options=options,
        )
