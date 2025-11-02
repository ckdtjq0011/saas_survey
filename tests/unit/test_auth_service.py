import pytest
from datetime import datetime, timedelta
from domain.value_objects.role import Role


def test_register_tenant_success(auth_service, tenant_repo):
    """테넌트 등록 성공 테스트"""
    tenant_id = auth_service.register_tenant("회사A")

    assert tenant_id is not None
    tenant = tenant_repo.find_tenant_by_id(tenant_id)
    assert tenant is not None
    assert tenant.name == "회사A"
    assert tenant.is_active is True


def test_register_user_success(auth_service, user_repo, sample_tenant):
    """사용자 등록 성공 테스트"""
    result = auth_service.register_user(
        tenant_id=sample_tenant.id,
        username="newuser",
        email="newuser@test.com",
        password="password123",
        role=Role.SURVEY_MANAGER
    )

    assert result.is_success()
    user_id = result.value
    user = user_repo.find_user_by_id(user_id)
    assert user is not None
    assert user.username == "newuser"
    assert user.role == Role.SURVEY_MANAGER


def test_register_user_duplicate_username(auth_service, sample_tenant, sample_admin_user):
    """중복 사용자명 테스트"""
    result = auth_service.register_user(
        tenant_id=sample_tenant.id,
        username="admin",
        email="another@test.com",
        password="password123",
        role=Role.RESPONDENT
    )

    assert result.is_failure()
    assert "이미 존재하는 사용자명입니다" in result.error


def test_register_user_nonexistent_tenant(auth_service):
    """존재하지 않는 테넌트 테스트"""
    result = auth_service.register_user(
        tenant_id="nonexistent",
        username="user",
        email="user@test.com",
        password="password123",
        role=Role.RESPONDENT
    )

    assert result.is_failure()
    assert "테넌트를 찾을 수 없습니다" in result.error


def test_login_success(auth_service, sample_tenant):
    """로그인 성공 테스트"""
    auth_service.register_user(
        tenant_id=sample_tenant.id,
        username="loginuser",
        email="login@test.com",
        password="password123",
        role=Role.RESPONDENT
    )

    result = auth_service.login("loginuser", "password123", sample_tenant.id)

    assert result.is_success()
    api_key = result.value
    assert api_key is not None
    assert len(api_key) > 0


def test_login_wrong_password(auth_service, sample_tenant):
    """잘못된 비밀번호 테스트"""
    auth_service.register_user(
        tenant_id=sample_tenant.id,
        username="loginuser2",
        email="login2@test.com",
        password="password123",
        role=Role.RESPONDENT
    )

    result = auth_service.login("loginuser2", "wrongpassword", sample_tenant.id)

    assert result.is_failure()
    assert "올바르지 않습니다" in result.error


def test_login_user_not_found(auth_service, sample_tenant):
    """존재하지 않는 사용자 로그인 테스트"""
    result = auth_service.login("nonexistent", "password123", sample_tenant.id)

    assert result.is_failure()
    assert "올바르지 않습니다" in result.error


def test_logout_success(auth_service, sample_tenant):
    """로그아웃 성공 테스트"""
    auth_service.register_user(
        tenant_id=sample_tenant.id,
        username="logoutuser",
        email="logout@test.com",
        password="password123",
        role=Role.RESPONDENT
    )

    login_result = auth_service.login("logoutuser", "password123", sample_tenant.id)
    api_key = login_result.value

    result = auth_service.logout(api_key)

    assert result.is_success()


def test_logout_invalid_api_key(auth_service):
    """잘못된 API 키로 로그아웃 시도 테스트"""
    result = auth_service.logout("invalid_api_key")

    assert result.is_failure()
    assert "유효하지 않은 세션입니다" in result.error


def test_validate_session_success(auth_service, session_repo, sample_admin_user, sample_tenant):
    """유효한 세션 검증 테스트"""
    from domain.entities.session import Session
    import uuid

    session = Session(
        id=str(uuid.uuid4()),
        user_id=sample_admin_user.id,
        tenant_id=sample_tenant.id,
        api_key="valid_key_123",
        expires_at=datetime.now() + timedelta(days=1),
        created_at=datetime.now(),
    )
    session_repo.save_session(session)

    result = auth_service.validate_session("valid_key_123")

    assert result.is_success()
    user, sess = result.value
    assert user.id == sample_admin_user.id
    assert sess.api_key == "valid_key_123"


def test_validate_session_expired(auth_service, session_repo, sample_admin_user, sample_tenant):
    """만료된 세션 검증 테스트"""
    from domain.entities.session import Session
    import uuid
    import time

    past_time = datetime.now() - timedelta(days=2)
    session = Session(
        id=str(uuid.uuid4()),
        user_id=sample_admin_user.id,
        tenant_id=sample_tenant.id,
        api_key="expired_key_123",
        expires_at=past_time + timedelta(hours=1),
        created_at=past_time,
    )
    session_repo.save_session(session)

    result = auth_service.validate_session("expired_key_123")

    assert result.is_failure()
    assert "세션이 만료되었습니다" in result.error


def test_validate_session_not_found(auth_service):
    """존재하지 않는 세션 검증 테스트"""
    result = auth_service.validate_session("nonexistent_key")

    assert result.is_failure()
    assert "유효하지 않은 API 키입니다" in result.error


def test_check_permission_tenant_admin_create_survey(sample_admin_user, auth_service):
    """TENANT_ADMIN 설문 생성 권한 테스트"""
    result = auth_service.check_permission(sample_admin_user, "create_survey")

    assert result.is_success()


def test_check_permission_respondent_create_survey(sample_respondent_user, auth_service):
    """RESPONDENT 설문 생성 권한 없음 테스트"""
    result = auth_service.check_permission(sample_respondent_user, "create_survey")

    assert result.is_failure()
    assert "권한이 없습니다" in result.error


def test_update_user_success(auth_service, sample_admin_user, sample_manager_user):
    """사용자 정보 수정 성공 테스트"""
    result = auth_service.update_user(
        admin_user=sample_admin_user,
        user_id=sample_manager_user.id,
        email="newemail@test.com"
    )

    assert result.is_success()


def test_update_user_no_permission(auth_service, sample_respondent_user, sample_manager_user):
    """권한 없는 사용자 정보 수정 시도 테스트"""
    result = auth_service.update_user(
        admin_user=sample_respondent_user,
        user_id=sample_manager_user.id,
        email="newemail@test.com"
    )

    assert result.is_failure()
    assert "권한이 없습니다" in result.error


def test_delete_user_success(auth_service, sample_admin_user, sample_manager_user):
    """사용자 삭제 성공 테스트"""
    result = auth_service.delete_user(
        admin_user=sample_admin_user,
        user_id=sample_manager_user.id
    )

    assert result.is_success()


def test_delete_user_no_permission(auth_service, sample_manager_user, sample_respondent_user):
    """권한 없는 사용자 삭제 시도 테스트"""
    result = auth_service.delete_user(
        admin_user=sample_manager_user,
        user_id=sample_respondent_user.id
    )

    assert result.is_failure()
    assert "권한이 없습니다" in result.error
