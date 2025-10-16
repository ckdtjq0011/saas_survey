"""세션 엔티티입니다."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Session:
    """사용자 세션을 나타내는 엔티티입니다.

    Attributes:
        id: 세션 고유 식별자
        user_id: 사용자 식별자
        tenant_id: 테넌트 식별자
        api_key: API 키 (인증용)
        expires_at: 만료 일시
        created_at: 생성 일시
    """
    id: str
    user_id: str
    tenant_id: str
    api_key: str
    expires_at: datetime
    created_at: datetime

    def __post_init__(self) -> None:
        """생성 후 불변 조건을 검증합니다.

        Raises:
            ValueError: 불변 조건 위반 시
        """
        if not self.id:
            raise ValueError("세션 ID는 필수입니다")
        if not self.user_id:
            raise ValueError("사용자 ID는 필수입니다")
        if not self.tenant_id:
            raise ValueError("테넌트 ID는 필수입니다")
        if not self.api_key:
            raise ValueError("API 키는 필수입니다")
        if self.expires_at <= self.created_at:
            raise ValueError("만료 일시는 생성 일시보다 이후여야 합니다")

    def is_expired(self, current_time: datetime) -> bool:
        """세션이 만료되었는지 확인합니다.

        Args:
            current_time: 현재 시각

        Returns:
            만료 여부
        """
        return current_time >= self.expires_at

    def to_dict(self) -> dict[str, str]:
        """엔티티를 딕셔너리로 변환합니다.

        Returns:
            엔티티 정보를 담은 딕셔너리
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "api_key": self.api_key,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Session":
        """딕셔너리로부터 엔티티를 생성합니다.

        Args:
            data: 엔티티 정보를 담은 딕셔너리

        Returns:
            Session 엔티티 인스턴스
        """
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            tenant_id=data["tenant_id"],
            api_key=data["api_key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            created_at=datetime.fromisoformat(data["created_at"]),
        )
