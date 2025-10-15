from dataclasses import dataclass
from datetime import datetime
from domain.entities.question import Question


@dataclass(frozen=True, slots=True)
class Survey:
    """설문을 나타내는 엔티티입니다.

    Attributes:
        id: 설문 고유 식별자
        title: 설문 제목
        description: 설문 설명
        created_at: 생성 일시
        questions: 설문에 포함된 질문 목록
    """
    id: str
    title: str
    description: str
    created_at: datetime
    questions: tuple[Question, ...] = ()

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("설문 ID는 필수입니다")
        if not self.title or not self.title.strip():
            raise ValueError("설문 제목은 필수입니다")
        if not self.description or not self.description.strip():
            raise ValueError("설문 설명은 필수입니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str], questions: tuple[Question, ...] = ()) -> "Survey":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리
            questions: 설문에 포함된 질문 목록

        Returns:
            Survey 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            questions=questions,
        )
