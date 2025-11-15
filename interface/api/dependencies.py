from datetime import datetime
from typing import Callable
from fastapi import Header, Depends
from loguru import logger

from config import settings
from infrastructure.di.containers import Container
from application.auth_service import AuthService
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.category_service import CategoryService
from application.survey_session_service import SurveySessionService
from domain.entities.user import User
from domain.entities.tenant import Tenant
from domain.entities.session import Session
from domain.value_objects.role import Role
from domain.value_objects.result import Success
from interface.api.exceptions import AuthenticationException, AuthorizationException


container = Container()
container.config.storage_type.from_value(settings.storage_type)
container.config.database_url.from_value(settings.database_url)
container.config.database_echo.from_value(settings.database_echo)
container.config.data_dir.from_value(str(settings.data_dir))
container.config.debug.from_value(settings.environment == "development")


def get_auth_service() -> AuthService:
    """AuthService 인스턴스를 반환합니다.

    Returns:
        AuthService 인스턴스
    """
    return container.auth_service()


def get_survey_service() -> SurveyService:
    """SurveyService 인스턴스를 반환합니다.

    Returns:
        SurveyService 인스턴스
    """
    return container.survey_service()


def get_response_service() -> ResponseService:
    """ResponseService 인스턴스를 반환합니다.

    Returns:
        ResponseService 인스턴스
    """
    return container.response_service()


def get_category_service() -> CategoryService:
    """CategoryService 인스턴스를 반환합니다.

    Returns:
        CategoryService 인스턴스
    """
    return container.category_service()


def get_survey_session_service() -> SurveySessionService:
    """SurveySessionService 인스턴스를 반환합니다.

    Returns:
        SurveySessionService 인스턴스
    """
    return container.survey_session_service()


async def get_current_session(
    x_api_key: str = Header(..., alias="X-API-Key"),
    auth_service: AuthService = Depends(get_auth_service)
) -> Session:
    """현재 세션을 반환합니다.

    Args:
        x_api_key: API 키 헤더
        auth_service: 인증 서비스

    Returns:
        세션 엔티티

    Raises:
        AuthenticationException: 인증 실패 시
    """
    result = auth_service.validate_session(x_api_key)

    if not isinstance(result, Success):
        logger.warning(f"세션 검증 실패: {result.error}")
        raise AuthenticationException(detail=result.error)

    session = result.value

    if session.expires_at < datetime.now():
        logger.warning(f"세션 만료: {session.id}")
        raise AuthenticationException(detail="세션이 만료되었습니다. 다시 로그인하세요.")

    return session


async def get_current_user(
    session: Session = Depends(get_current_session),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """현재 사용자를 반환합니다.

    Args:
        session: 현재 세션
        auth_service: 인증 서비스

    Returns:
        사용자 엔티티

    Raises:
        AuthenticationException: 사용자 조회 실패 시
    """
    result = auth_service.user_repo.find_by_id(session.user_id)

    if not isinstance(result, Success):
        logger.error(f"사용자 조회 실패: {result.error}")
        raise AuthenticationException(detail="사용자를 찾을 수 없습니다")

    user = result.value

    if not user.is_active:
        logger.warning(f"비활성 사용자 접근 시도: {user.id}")
        raise AuthenticationException(detail="비활성화된 사용자입니다")

    return user


async def get_current_tenant(
    user: User = Depends(get_current_user)
) -> Tenant:
    """현재 테넌트를 반환합니다.

    Args:
        user: 현재 사용자

    Returns:
        테넌트 엔티티

    Raises:
        AuthenticationException: 테넌트 조회 실패 시
    """
    tenant_repo = container.tenant_repository()
    result = tenant_repo.find_by_id(user.tenant_id)

    if not isinstance(result, Success):
        logger.error(f"테넌트 조회 실패: {result.error}")
        raise AuthenticationException(detail="테넌트를 찾을 수 없습니다")

    tenant = result.value

    if not tenant.is_active:
        logger.warning(f"비활성 테넌트 접근 시도: {tenant.id}")
        raise AuthenticationException(detail="비활성화된 테넌트입니다")

    return tenant


def require_role(*allowed_roles: Role) -> Callable:
    """특정 역할을 요구하는 의존성을 생성합니다.

    Args:
        allowed_roles: 허용된 역할 목록

    Returns:
        역할 체크 의존성 함수
    """
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        """사용자의 역할을 확인합니다.

        Args:
            user: 현재 사용자

        Returns:
            사용자 엔티티

        Raises:
            AuthorizationException: 권한 부족 시
        """
        if user.role not in allowed_roles:
            logger.warning(
                f"권한 부족: user={user.id}, role={user.role}, "
                f"required={allowed_roles}"
            )
            raise AuthorizationException(
                detail=f"이 작업은 {', '.join(r.name for r in allowed_roles)} 역할이 필요합니다"
            )

        return user

    return role_checker


def require_admin() -> Callable:
    """관리자 권한을 요구하는 의존성을 생성합니다.

    Returns:
        관리자 체크 의존성 함수
    """
    return require_role(Role.TENANT_ADMIN)


def require_manager() -> Callable:
    """관리자 또는 설문 관리자 권한을 요구하는 의존성을 생성합니다.

    Returns:
        관리자/설문 관리자 체크 의존성 함수
    """
    return require_role(Role.TENANT_ADMIN, Role.SURVEY_MANAGER)
