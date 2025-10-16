from abc import ABC, abstractmethod
from domain.entities.tenant import Tenant


class TenantRepository(ABC):
    """테넌트 저장소 인터페이스입니다."""

    @abstractmethod
    def save_tenant(self, tenant: Tenant) -> None:
        """테넌트를 저장합니다.

        Args:
            tenant: 저장할 테넌트 엔티티
        """
        pass

    @abstractmethod
    def find_tenant_by_id(self, tenant_id: str) -> Tenant | None:
        """ID로 테넌트를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자

        Returns:
            테넌트 엔티티 또는 None
        """
        pass

    @abstractmethod
    def find_all_tenants(self) -> list[Tenant]:
        """모든 테넌트를 조회합니다.

        Returns:
            테넌트 엔티티 목록
        """
        pass
