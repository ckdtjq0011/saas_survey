"""사용자 엔티티입니다."""

import re
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
            TypeError: 타입이 잘못된 경우
        """
        if not self.id:
            raise ValueError("사용자 ID는 필수입니다")
        if not self.tenant_id:
            raise ValueError("테넌트 ID는 필수입니다")
        if not self.username or not self.username.strip():
            raise ValueError("사용자명은 필수입니다")
        if len(self.username) < 3:
            raise ValueError("사용자명은 최소 3자 이상이어야 합니다")
        if len(self.username) > 50:
            raise ValueError("사용자명은 50자를 초과할 수 없습니다")
        # VULN-008: 사용자명에 공백이 포함되지 않도록 검증
        if any(c.isspace() for c in self.username):
            raise ValueError("사용자명에 공백이 포함될 수 없습니다")
        # VULN-007: 강화된 이메일 형식 검증
        if not self.email or not self._is_valid_email(self.email):
            raise ValueError("유효한 이메일 형식이 아닙니다")
        if not self.password_hash:
            raise ValueError("비밀번호 해시는 필수입니다")
        # Role 타입 검증
        if not isinstance(self.role, Role):
            raise TypeError("role은 Role enum 타입이어야 합니다")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """이메일 형식이 유효한지 검증합니다.

        Args:
            email: 검증할 이메일 주소

        Returns:
            이메일 형식이 유효하면 True
        """
        # 기본 형식 검증: @가 정확히 하나 있어야 함
        if email.count("@") != 1:
            return False

        local_part, domain = email.rsplit("@", 1)

        # Local part 검증
        if not local_part or len(local_part) > 64:
            return False
        if local_part.startswith(".") or local_part.endswith("."):
            return False
        if ".." in local_part:
            return False
        # Local part는 영숫자, 점, 하이픈, 언더스코어, +, % 허용
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*$", local_part):
            return False

        # Domain part 검증 (국제 도메인 지원)
        if not domain or len(domain) > 255:
            return False
        if ".." in domain:
            return False
        # 도메인은 최소한 하나의 점이 있어야 함 (예: example.com)
        if "." not in domain:
            return False
        # 도메인 각 레이블 검증 (유니코드 문자 허용)
        labels = domain.split(".")
        for label in labels:
            if not label or len(label) > 63:
                return False
            # 각 라벨은 문자나 숫자로 시작/끝나야 함
            if not label[0].isalnum() or not label[-1].isalnum():
                return False

        return True

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
