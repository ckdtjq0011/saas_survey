"""사용자 엔티티입니다."""

from dataclasses import dataclass
from datetime import datetime
from domain.value_objects.role import Role


@dataclass(frozen=True, slots=True)
class User:
    """사용자를 나타내는 엔티티입니다.

    Attributes:
        id: 사용자 고유 식별자
        tenant_id: 소속 테넌트 식별자
        username: 사용자명 (로그인용, 고유)
        email: 이메일
        password_hash: 비밀번호 해시 (bcrypt)
        role: 사용자 역할
        created_at: 생성 일시
        is_active: 활성화 상태
    """
    id: str
    tenant_id: str
    username: str
    email: str
    password_hash: str
    role: Role
    created_at: datetime
    is_active: bool = True

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("사용자 ID는 필수입니다")
        if not self.tenant_id:
            raise ValueError("테넌트 ID는 필수입니다")
        if not self.username or not self.username.strip():
            raise ValueError("사용자명은 필수입니다")
        if len(self.username) < 3:
            raise ValueError("사용자명은 최소 3자 이상이어야 합니다")
        if not self.email or "@" not in self.email:
            raise ValueError("유효한 이메일 주소가 필요합니다")
        if not self.password_hash:
            raise ValueError("비밀번호 해시는 필수입니다")

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role.value,
            "created_at": self.created_at.isoformat(),
            "is_active": str(self.is_active),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "User":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            User 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            tenant_id=data["tenant_id"],
            username=data["username"],
            email=data["email"],
            password_hash=data["password_hash"],
            role=Role(data["role"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            is_active=data["is_active"].lower() == "true",
        )
