from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Response:
    """설문 응답을 나타내는 엔티티입니다.

    Attributes:
        id: 응답 고유 식별자
        survey_id: 설문 식별자
        question_id: 질문 식별자
        answer: 답변 내용
        respondent_id: 응답자 식별자
        created_at: 응답 일시
    """
    id: str
    survey_id: str
    question_id: str
    answer: str
    respondent_id: str
    created_at: datetime

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "survey_id": self.survey_id,
            "question_id": self.question_id,
            "answer": self.answer,
            "respondent_id": self.respondent_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Response":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Response 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            survey_id=data["survey_id"],
            question_id=data["question_id"],
            answer=data["answer"],
            respondent_id=data["respondent_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )
