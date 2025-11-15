from dataclasses import dataclass
from datetime import datetime

from domain.value_objects.audit_action import AuditAction


@dataclass(frozen=True, slots=True)
class AuditLog:
    """감사 로그 엔티티입니다.

    시스템의 모든 중요한 이벤트를 기록합니다.

    Attributes:
        id: 감사 로그 고유 식별자
        timestamp: 이벤트 발생 시각
        tenant_id: 테넌트 식별자
        user_id: 사용자 식별자 (시스템 이벤트는 None)
        action: 액션 타입
        resource_type: 리소스 타입 (예: survey, user, session)
        resource_id: 리소스 식별자
        result: 결과 (success, failure, denied)
        ip_address: IP 주소 (API 요청만 해당)
        details: 추가 상세 정보 (JSON 문자열)
    """

    id: str
    timestamp: datetime
    tenant_id: str
    user_id: str | None
    action: AuditAction
    resource_type: str
    resource_id: str | None
    result: str
    ip_address: str | None
    details: str | None
