from enum import Enum


class AuditAction(Enum):
    """감사 로그 액션 타입입니다.

    감사 로그에 기록되는 모든 액션 타입을 정의합니다.
    """

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"

    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ROLE_CHANGED = "user_role_changed"

    SURVEY_CREATED = "survey_created"
    SURVEY_UPDATED = "survey_updated"
    SURVEY_DELETED = "survey_deleted"

    RESPONSE_SUBMITTED = "response_submitted"
    RESPONSE_UPDATED = "response_updated"
    RESPONSE_DELETED = "response_deleted"

    ACCESS_DENIED = "access_denied"
    CROSS_TENANT_ACCESS_ATTEMPT = "cross_tenant_access_attempt"

    SESSION_CLEANUP = "session_cleanup"
