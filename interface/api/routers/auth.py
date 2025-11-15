from fastapi import APIRouter, Depends, status
from loguru import logger

from interface.api.dependencies import (
    get_auth_service,
    get_current_user,
    require_admin,
    container
)
from interface.api.exceptions import handle_result
from interface.api.schemas.auth import (
    TenantCreate,
    TenantResponse,
    UserRegister,
    UserLogin,
    LoginResponse,
    UserResponse,
    UserUpdate
)
from interface.api.schemas.common import IdResponse, MessageResponse
from application.auth_service import AuthService
from domain.entities.user import User
from domain.value_objects.role import Role


router = APIRouter(prefix="/auth", tags=["인증/인가"])


@router.post(
    "/tenants",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="테넌트 등록",
    description="새로운 테넌트를 등록합니다. 테넌트는 조직 또는 병원 단위입니다."
)
async def create_tenant(
    request: TenantCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> TenantResponse:
    """테넌트를 등록합니다.

    Args:
        request: 테넌트 생성 요청
        auth_service: 인증 서비스

    Returns:
        생성된 테넌트 정보
    """
    logger.info(f"테넌트 등록 요청: name={request.name}")

    result = auth_service.register_tenant(request.name)
    tenant = handle_result(result)

    logger.info(f"테넌트 등록 성공: id={tenant.id}, name={tenant.name}")

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        created_at=tenant.created_at,
        is_active=tenant.is_active
    )


@router.get(
    "/tenants",
    response_model=list[TenantResponse],
    summary="테넌트 목록 조회",
    description="모든 테넌트 목록을 조회합니다."
)
async def list_tenants() -> list[TenantResponse]:
    """테넌트 목록을 조회합니다.

    Returns:
        테넌트 목록
    """
    logger.info("테넌트 목록 조회 요청")

    tenant_repo = container.tenant_repository()
    result = tenant_repo.find_all()
    tenants = handle_result(result)

    logger.info(f"테넌트 목록 조회 성공: count={len(tenants)}")

    return [
        TenantResponse(
            id=t.id,
            name=t.name,
            created_at=t.created_at,
            is_active=t.is_active
        )
        for t in tenants
    ]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 등록",
    description="새로운 사용자를 등록합니다. 역할을 지정할 수 있습니다."
)
async def register_user(
    request: UserRegister,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """사용자를 등록합니다.

    Args:
        request: 사용자 등록 요청
        auth_service: 인증 서비스

    Returns:
        생성된 사용자 정보
    """
    logger.info(
        f"사용자 등록 요청: tenant_id={request.tenant_id}, "
        f"username={request.username}, role={request.role}"
    )

    result = auth_service.register_user(
        tenant_id=request.tenant_id,
        username=request.username,
        email=request.email,
        password=request.password,
        role=Role[request.role]
    )
    user = handle_result(result)

    logger.info(f"사용자 등록 성공: id={user.id}, username={user.username}")

    return UserResponse(
        id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        email=user.email,
        role=user.role.name,
        created_at=user.created_at,
        is_active=user.is_active
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="로그인",
    description="사용자 로그인을 수행하고 API 키를 발급합니다. API 키는 X-API-Key 헤더에 사용됩니다."
)
async def login(
    request: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """로그인을 수행합니다.

    Args:
        request: 로그인 요청
        auth_service: 인증 서비스

    Returns:
        로그인 응답 (API 키 포함)
    """
    logger.info(f"로그인 요청: email={request.email}")

    result = auth_service.login(request.email, request.password)
    api_key = handle_result(result)

    validation_result = auth_service.validate_session(api_key)
    user, session = handle_result(validation_result)

    logger.info(
        f"로그인 성공: user_id={user.id}, session_id={session.id}, "
        f"expires_at={session.expires_at}"
    )

    return LoginResponse(
        api_key=api_key,
        user_id=user.id,
        username=user.username,
        role=user.role.name,
        expires_at=session.expires_at,
        message="로그인 성공"
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="로그아웃",
    description="현재 세션을 종료합니다. 이후 해당 API 키는 사용할 수 없습니다."
)
async def logout(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """로그아웃을 수행합니다.

    Args:
        current_user: 현재 사용자
        auth_service: 인증 서비스

    Returns:
        로그아웃 메시지
    """
    logger.info(f"로그아웃 요청: user_id={current_user.id}")

    result = auth_service.logout(current_user.id)
    handle_result(result)

    logger.info(f"로그아웃 성공: user_id={current_user.id}")

    return MessageResponse(message="로그아웃 성공")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="현재 사용자 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다."
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """현재 사용자 정보를 조회합니다.

    Args:
        current_user: 현재 사용자

    Returns:
        사용자 정보
    """
    logger.info(f"현재 사용자 정보 조회: user_id={current_user.id}")

    return UserResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.name,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="사용자 수정 (관리자 전용)",
    description="사용자 정보를 수정합니다. TENANT_ADMIN 권한이 필요합니다."
)
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """사용자 정보를 수정합니다.

    Args:
        user_id: 수정할 사용자 ID
        request: 사용자 수정 요청
        current_user: 현재 사용자 (관리자)
        auth_service: 인증 서비스

    Returns:
        수정된 사용자 정보
    """
    logger.info(
        f"사용자 수정 요청: user_id={user_id}, "
        f"by={current_user.id}"
    )

    user_result = auth_service.user_repo.find_by_id(user_id)
    user = handle_result(user_result, not_found_msg="찾을 수 없")

    if user.tenant_id != current_user.tenant_id:
        logger.warning(
            f"다른 테넌트 사용자 수정 시도: user_id={user_id}, "
            f"tenant_id={user.tenant_id}, current_tenant={current_user.tenant_id}"
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 테넌트의 사용자는 수정할 수 없습니다"
        )

    if request.username is not None:
        user.username = request.username
    if request.email is not None:
        user.email = request.email
    if request.role is not None:
        user.role = Role[request.role]
    if request.is_active is not None:
        user.is_active = request.is_active

    save_result = auth_service.user_repo.save(user)
    updated_user = handle_result(save_result)

    logger.info(f"사용자 수정 성공: user_id={updated_user.id}")

    return UserResponse(
        id=updated_user.id,
        tenant_id=updated_user.tenant_id,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role.name,
        created_at=updated_user.created_at,
        is_active=updated_user.is_active
    )


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="사용자 삭제 (관리자 전용)",
    description="사용자를 비활성화합니다. TENANT_ADMIN 권한이 필요합니다."
)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin()),
    auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """사용자를 비활성화합니다.

    Args:
        user_id: 삭제할 사용자 ID
        current_user: 현재 사용자 (관리자)
        auth_service: 인증 서비스

    Returns:
        삭제 메시지
    """
    logger.info(f"사용자 삭제 요청: user_id={user_id}, by={current_user.id}")

    user_result = auth_service.user_repo.find_by_id(user_id)
    user = handle_result(user_result, not_found_msg="찾을 수 없")

    if user.tenant_id != current_user.tenant_id:
        logger.warning(
            f"다른 테넌트 사용자 삭제 시도: user_id={user_id}, "
            f"tenant_id={user.tenant_id}, current_tenant={current_user.tenant_id}"
        )
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 테넌트의 사용자는 삭제할 수 없습니다"
        )

    user.is_active = False
    save_result = auth_service.user_repo.save(user)
    handle_result(save_result)

    logger.info(f"사용자 삭제 성공: user_id={user_id}")

    return MessageResponse(message="사용자가 비활성화되었습니다")
