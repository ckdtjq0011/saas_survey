from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.audit_log import AuditLog
from domain.value_objects.audit_action import AuditAction


class AuditLogRepository(ABC):
    """감사 로그 저장소 인터페이스입니다."""

    @abstractmethod
    def save(self, audit_log: AuditLog) -> None:
        """감사 로그를 저장합니다.

        Args:
            audit_log: 저장할 감사 로그 엔티티
        """
        pass

    @abstractmethod
    def find_by_tenant(
        self,
        tenant_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """테넌트별 감사 로그를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        pass

    @abstractmethod
    def find_by_user(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """사용자별 감사 로그를 조회합니다.

        Args:
            user_id: 사용자 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        pass

    @abstractmethod
    def find_by_action(
        self,
        action: AuditAction,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """액션별 감사 로그를 조회합니다.

        Args:
            action: 액션 타입
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            감사 로그 목록
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """전체 감사 로그 개수를 반환합니다.

        Returns:
            감사 로그 개수
        """
        pass
