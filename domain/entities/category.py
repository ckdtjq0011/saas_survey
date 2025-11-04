from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Category:
    """질문 범주를 나타내는 엔티티입니다.

    Attributes:
        id: 범주 고유 식별자
        tenant_id: 소속 테넌트 식별자
        name: 범주 이름
        description: 범주 설명
        parent_id: 상위 범주 식별자 (None이면 최상위 범주)
        order: 표시 순서
        is_active: 활성화 여부
        created_at: 생성 일시
    """
    id: str
    tenant_id: str
    name: str
    description: str
    parent_id: str | None
    order: int
    is_active: bool
    created_at: datetime

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("범주 ID는 필수입니다")
        if not self.tenant_id:
            raise ValueError("테넌트 ID는 필수입니다")
        if not self.name or not self.name.strip():
            raise ValueError("범주 이름은 필수입니다")
        if not self.description or not self.description.strip():
            raise ValueError("범주 설명은 필수입니다")
        if self.order < 0:
            raise ValueError("표시 순서는 0 이상이어야 합니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id if self.parent_id else "",
            "order": str(self.order),
            "is_active": str(self.is_active),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Category":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Category 엔티티 인스턴스
        """
        parent_id = data.get("parent_id", "")
        return cls(
            id=data["id"],
            tenant_id=data["tenant_id"],
            name=data["name"],
            description=data["description"],
            parent_id=parent_id if parent_id else None,
            order=int(data["order"]),
            is_active=data["is_active"].lower() == "true",
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def is_top_level(self) -> bool:
        """최상위 범주인지 확인합니다.

        Returns:
            최상위 범주이면 True, 하위 범주이면 False
        """
        return self.parent_id is None
