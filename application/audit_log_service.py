"""감사 로그 서비스"""

import json
import uuid
from datetime import datetime

from loguru import logger

from domain.entities.audit_log import AuditLog
from domain.repositories.audit_log_repository import AuditLogRepository
from domain.value_objects.audit_action import AuditAction
from domain.value_objects.result import Success, Failure, Result


class AuditLogService:
    """감사 로그 서비스입니다.

    시스템의 모든 중요한 이벤트를 기록하고 조회합니다.
    """

    def __init__(self, audit_log_repository: AuditLogRepository):
        """감사 로그 서비스를 초기화합니다.

        Args:
            audit_log_repository: 감사 로그 저장소
        """
        self.audit_log_repository = audit_log_repository

    def log_event(
        self,
        tenant_id: str,
        action: AuditAction,
        resource_type: str,
        result: str,
        user_id: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        details: dict | None = None
    ) -> Result[None, str]:
        """감사 이벤트를 기록합니다.

        Args:
            tenant_id: 테넌트 식별자
            action: 액션 타입
            resource_type: 리소스 타입 (survey, user, session 등)
            result: 결과 (success, failure, denied)
            user_id: 사용자 식별자 (시스템 이벤트는 None)
            resource_id: 리소스 식별자
            ip_address: IP 주소
            details: 추가 상세 정보 딕셔너리

        Returns:
            성공 시 None, 실패 시 에러 메시지
        """
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                result=result,
                ip_address=ip_address,
                details=json.dumps(details, ensure_ascii=False) if details else None
            )

            self.audit_log_repository.save(audit_log)
            logger.debug(
                f"감사 로그 기록: action={action.value}, "
                f"user={user_id}, result={result}"
            )
            return Success(None)

        except Exception as e:
            logger.exception(f"감사 로그 기록 실패: {str(e)}")
            return Failure(f"감사 로그 기록 실패: {str(e)}")

    def get_tenant_logs(
        self,
        tenant_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> Result[list[AuditLog], str]:
        """테넌트별 감사 로그를 조회합니다.

        Args:
            tenant_id: 테넌트 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            성공 시 감사 로그 목록, 실패 시 에러 메시지
        """
        try:
            logs = self.audit_log_repository.find_by_tenant(
                tenant_id, start_date, end_date, limit
            )
            return Success(logs)

        except Exception as e:
            logger.exception(f"테넌트 감사 로그 조회 실패: {str(e)}")
            return Failure(f"감사 로그 조회 실패: {str(e)}")

    def get_user_logs(
        self,
        user_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> Result[list[AuditLog], str]:
        """사용자별 감사 로그를 조회합니다.

        Args:
            user_id: 사용자 식별자
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            성공 시 감사 로그 목록, 실패 시 에러 메시지
        """
        try:
            logs = self.audit_log_repository.find_by_user(
                user_id, start_date, end_date, limit
            )
            return Success(logs)

        except Exception as e:
            logger.exception(f"사용자 감사 로그 조회 실패: {str(e)}")
            return Failure(f"감사 로그 조회 실패: {str(e)}")

    def get_action_logs(
        self,
        action: AuditAction,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> Result[list[AuditLog], str]:
        """액션별 감사 로그를 조회합니다.

        Args:
            action: 액션 타입
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수

        Returns:
            성공 시 감사 로그 목록, 실패 시 에러 메시지
        """
        try:
            logs = self.audit_log_repository.find_by_action(
                action, start_date, end_date, limit
            )
            return Success(logs)

        except Exception as e:
            logger.exception(f"액션별 감사 로그 조회 실패: {str(e)}")
            return Failure(f"감사 로그 조회 실패: {str(e)}")

    def get_total_count(self) -> int:
        """전체 감사 로그 개수를 반환합니다.

        Returns:
            감사 로그 개수
        """
        try:
            return self.audit_log_repository.count()
        except Exception as e:
            logger.exception(f"감사 로그 개수 조회 실패: {str(e)}")
            return 0
