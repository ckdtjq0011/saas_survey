"""테넌트 엔티티입니다."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Tenant:
    """테넌트(조직/회사)를 나타내는 엔티티입니다.

    Attributes:
        id: 테넌트 고유 식별자
        name: 테넌트 이름
        created_at: 생성 일시
        is_active: 활성화 상태
    """
    id: str
    name: str
    created_at: datetime
    is_active: bool = True

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("테넌트 ID는 필수입니다")
        if not self.name or not self.name.strip():
            raise ValueError("테넌트 이름은 필수입니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "is_active": str(self.is_active),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Tenant":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Tenant 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            is_active=data["is_active"].lower() == "true",
        )
