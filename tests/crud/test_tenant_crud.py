import uuid
import pytest
from datetime import datetime
from domain.entities.tenant import Tenant


def test_create_tenant(tenant_repo):
    """테넌트 생성 테스트"""
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(
        id=tenant_id,
        name="회사A",
        created_at=datetime.now(),
        is_active=True,
    )

    tenant_repo.save_tenant(tenant)

    found = tenant_repo.find_tenant_by_id(tenant_id)
    assert found is not None
    assert found.id == tenant_id
    assert found.name == "회사A"
    assert found.is_active is True


def test_read_tenant_by_id(tenant_repo, sample_tenant):
    """ID로 테넌트 조회 테스트"""
    found = tenant_repo.find_tenant_by_id(sample_tenant.id)

    assert found is not None
    assert found.id == sample_tenant.id
    assert found.name == sample_tenant.name


def test_read_all_tenants(tenant_repo):
    """모든 테넌트 조회 테스트"""
    tenants = []
    for i in range(3):
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=f"회사{i}",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)
        tenants.append(tenant)

    all_tenants = tenant_repo.find_all_tenants()

    assert len(all_tenants) == 3
    assert all(t.name in [f"회사{i}" for i in range(3)] for t in all_tenants)


def test_update_tenant_name(tenant_repo, sample_tenant):
    """테넌트 이름 수정 테스트"""
    tenant_repo.update_tenant(sample_tenant.id, name="회사B")

    updated = tenant_repo.find_tenant_by_id(sample_tenant.id)

    assert updated is not None
    assert updated.name == "회사B"
    assert updated.id == sample_tenant.id


def test_update_tenant_status(tenant_repo, sample_tenant):
    """테넌트 활성화 상태 변경 테스트"""
    tenant_repo.update_tenant(sample_tenant.id, is_active=False)

    updated = tenant_repo.find_tenant_by_id(sample_tenant.id)

    assert updated is not None
    assert updated.is_active is False


def test_delete_tenant(tenant_repo, sample_tenant):
    """테넌트 삭제 테스트"""
    tenant_repo.delete_tenant(sample_tenant.id)

    found = tenant_repo.find_tenant_by_id(sample_tenant.id)

    assert found is None


def test_delete_tenant_not_found(tenant_repo):
    """존재하지 않는 테넌트 삭제 시도 테스트"""
    with pytest.raises(ValueError, match="테넌트를 찾을 수 없습니다"):
        tenant_repo.delete_tenant("nonexistent_id")


def test_update_tenant_not_found(tenant_repo):
    """존재하지 않는 테넌트 수정 시도 테스트"""
    with pytest.raises(ValueError, match="테넌트를 찾을 수 없습니다"):
        tenant_repo.update_tenant("nonexistent_id", name="새이름")
