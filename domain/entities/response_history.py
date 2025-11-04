from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResponseHistory:
    """응답 수정 이력을 나타내는 엔티티입니다.

    Attributes:
        id: 이력 고유 식별자
        response_id: 응답 식별자
        old_answer: 수정 전 답변
        new_answer: 수정 후 답변
        updated_at: 수정 일시
        updated_by: 수정한 사용자 ID
    """
    id: str
    response_id: str
    old_answer: str
    new_answer: str
    updated_at: datetime
    updated_by: str

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("이력 ID는 필수입니다")
        if not self.response_id:
            raise ValueError("응답 ID는 필수입니다")
        if not self.old_answer or not self.old_answer.strip():
            raise ValueError("수정 전 답변은 필수입니다")
        if not self.new_answer or not self.new_answer.strip():
            raise ValueError("수정 후 답변은 필수입니다")
        if not self.updated_by:
            raise ValueError("수정자 ID는 필수입니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "response_id": self.response_id,
            "old_answer": self.old_answer,
            "new_answer": self.new_answer,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ResponseHistory":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            ResponseHistory 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            response_id=data["response_id"],
            old_answer=data["old_answer"],
            new_answer=data["new_answer"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=data["updated_by"],
        )
