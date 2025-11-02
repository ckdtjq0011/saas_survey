import uuid
import pytest
from datetime import datetime
from domain.entities.user import User
from domain.value_objects.role import Role


def test_create_user_tenant_admin(user_repo, sample_tenant):
    """TENANT_ADMIN 생성 테스트"""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        tenant_id=sample_tenant.id,
        username="admin",
        email="admin@test.com",
        password_hash="hashed_password",
        role=Role.TENANT_ADMIN,
        created_at=datetime.now(),
        is_active=True,
    )

    user_repo.save_user(user)

    found = user_repo.find_user_by_id(user_id)
    assert found is not None
    assert found.username == "admin"
    assert found.role == Role.TENANT_ADMIN


def test_create_user_survey_manager(user_repo, sample_tenant):
    """SURVEY_MANAGER 생성 테스트"""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        tenant_id=sample_tenant.id,
        username="manager",
        email="manager@test.com",
        password_hash="hashed_password",
        role=Role.SURVEY_MANAGER,
        created_at=datetime.now(),
        is_active=True,
    )

    user_repo.save_user(user)

    found = user_repo.find_user_by_id(user_id)
    assert found is not None
    assert found.role == Role.SURVEY_MANAGER


def test_create_user_respondent(user_repo, sample_tenant):
    """RESPONDENT 생성 테스트"""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        tenant_id=sample_tenant.id,
        username="respondent",
        email="respondent@test.com",
        password_hash="hashed_password",
        role=Role.RESPONDENT,
        created_at=datetime.now(),
        is_active=True,
    )

    user_repo.save_user(user)

    found = user_repo.find_user_by_id(user_id)
    assert found is not None
    assert found.role == Role.RESPONDENT


def test_read_user_by_id(user_repo, sample_admin_user):
    """ID로 사용자 조회 테스트"""
    found = user_repo.find_user_by_id(sample_admin_user.id)

    assert found is not None
    assert found.id == sample_admin_user.id
    assert found.username == sample_admin_user.username


def test_read_user_by_username(user_repo, sample_admin_user, sample_tenant):
    """username으로 사용자 조회 테스트"""
    found = user_repo.find_user_by_username("admin", sample_tenant.id)

    assert found is not None
    assert found.username == "admin"


def test_read_users_by_tenant(user_repo, sample_tenant):
    """테넌트별 사용자 목록 조회 테스트"""
    for i in range(3):
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=sample_tenant.id,
            username=f"user{i}",
            email=f"user{i}@test.com",
            password_hash="hashed_password",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True,
        )
        user_repo.save_user(user)

    users = user_repo.find_users_by_tenant(sample_tenant.id)

    assert len(users) == 3
    assert all(u.tenant_id == sample_tenant.id for u in users)


def test_update_user_email(user_repo, sample_admin_user):
    """이메일 변경 테스트"""
    user_repo.update_user(sample_admin_user.id, email="newemail@test.com")

    updated = user_repo.find_user_by_id(sample_admin_user.id)

    assert updated is not None
    assert updated.email == "newemail@test.com"


def test_update_user_password(user_repo, sample_admin_user):
    """비밀번호 변경 테스트"""
    user_repo.update_user(sample_admin_user.id, password_hash="new_hashed_password")

    updated = user_repo.find_user_by_id(sample_admin_user.id)

    assert updated is not None
    assert updated.password_hash == "new_hashed_password"


def test_update_user_role(user_repo, sample_admin_user):
    """역할 변경 테스트"""
    user_repo.update_user(sample_admin_user.id, role=Role.SURVEY_MANAGER.value)

    updated = user_repo.find_user_by_id(sample_admin_user.id)

    assert updated is not None
    assert updated.role == Role.SURVEY_MANAGER


def test_update_user_status(user_repo, sample_admin_user):
    """활성화 상태 변경 테스트"""
    user_repo.update_user(sample_admin_user.id, is_active=False)

    updated = user_repo.find_user_by_id(sample_admin_user.id)

    assert updated is not None
    assert updated.is_active is False


def test_delete_user(user_repo, sample_admin_user):
    """사용자 삭제 테스트"""
    user_repo.delete_user(sample_admin_user.id)

    found = user_repo.find_user_by_id(sample_admin_user.id)

    assert found is None


def test_delete_user_not_found(user_repo):
    """존재하지 않는 사용자 삭제 시도 테스트"""
    with pytest.raises(ValueError, match="사용자를 찾을 수 없습니다"):
        user_repo.delete_user("nonexistent_id")


def test_update_user_not_found(user_repo):
    """존재하지 않는 사용자 수정 시도 테스트"""
    with pytest.raises(ValueError, match="사용자를 찾을 수 없습니다"):
        user_repo.update_user("nonexistent_id", email="new@test.com")
