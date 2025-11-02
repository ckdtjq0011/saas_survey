import pytest
import uuid
import bcrypt
from datetime import datetime, timedelta
from domain.entities.session import Session
from domain.value_objects.role import Role


class TestInactiveTenantUserHandling:
    """비활성 테넌트/사용자 처리 테스트"""

    def test_login_inactive_tenant(self, auth_service, sample_tenant, tenant_repo):
        """비활성 테넌트의 사용자 로그인 시도

        시나리오:
            1. 사용자 등록
            2. 테넌트 비활성화
            3. 로그인 시도
            4. 실패 확인 (비활성 사용자 에러)
        """
        auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="testuser",
            email="test@example.com",
            password="password123",
            role=Role.RESPONDENT
        )

        tenant_repo.update_tenant(sample_tenant.id, is_active=False)

        result = auth_service.login("testuser", "password123", sample_tenant.id)

        assert result.is_failure()
        assert "비활성화된 사용자입니다" in result.error

    def test_login_inactive_user(self, auth_service, sample_tenant, user_repo):
        """비활성 사용자 로그인 시도

        시나리오:
            1. 사용자 등록
            2. 사용자 비활성화
            3. 로그인 시도
            4. 실패 확인
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="inactiveuser",
            email="inactive@example.com",
            password="password123",
            role=Role.RESPONDENT
        )
        user_id = result.value

        user_repo.update_user(user_id, is_active=False)

        login_result = auth_service.login("inactiveuser", "password123", sample_tenant.id)

        assert login_result.is_failure()
        assert "비활성화된 사용자입니다" in login_result.error

    def test_register_user_inactive_tenant(self, auth_service, sample_tenant, tenant_repo):
        """비활성 테넌트에 사용자 등록 시도

        시나리오:
            1. 테넌트 비활성화
            2. 사용자 등록 시도
            3. 실패 확인
        """
        tenant_repo.update_tenant(sample_tenant.id, is_active=False)

        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="newuser",
            email="new@example.com",
            password="password123",
            role=Role.RESPONDENT
        )

        assert result.is_failure()
        assert "비활성화된 테넌트입니다" in result.error

    def test_validate_session_inactive_user(self, auth_service, sample_tenant, user_repo, session_repo):
        """비활성 사용자의 세션 검증

        시나리오:
            1. 사용자 등록 및 로그인
            2. 사용자 비활성화
            3. 세션 검증 시도
            4. 실패 확인
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="sessionuser",
            email="session@example.com",
            password="password123",
            role=Role.RESPONDENT
        )
        user_id = result.value

        login_result = auth_service.login("sessionuser", "password123", sample_tenant.id)
        api_key = login_result.value

        user_repo.update_user(user_id, is_active=False)

        validate_result = auth_service.validate_session(api_key)

        assert validate_result.is_failure()
        assert "비활성화된 사용자입니다" in validate_result.error


class TestSessionManagementExtended:
    """세션 관리 확장 테스트"""

    def test_login_replaces_existing_session(self, auth_service, sample_tenant, session_repo):
        """기존 세션을 대체하는 로그인

        시나리오:
            1. 사용자 등록 및 첫 번째 로그인
            2. 첫 번째 API 키로 세션 검증 성공
            3. 두 번째 로그인
            4. 첫 번째 API 키로 세션 검증 실패
            5. 두 번째 API 키로 세션 검증 성공
        """
        auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="multilogin",
            email="multi@example.com",
            password="password123",
            role=Role.RESPONDENT
        )

        first_login = auth_service.login("multilogin", "password123", sample_tenant.id)
        first_api_key = first_login.value

        first_validate = auth_service.validate_session(first_api_key)
        assert first_validate.is_success()

        second_login = auth_service.login("multilogin", "password123", sample_tenant.id)
        second_api_key = second_login.value

        assert first_api_key != second_api_key

        first_validate_after = auth_service.validate_session(first_api_key)
        assert first_validate_after.is_failure()

        second_validate = auth_service.validate_session(second_api_key)
        assert second_validate.is_success()

    def test_session_cleanup_on_user_delete(self, auth_service, sample_admin_user, sample_tenant):
        """사용자 삭제 시 세션 정리

        시나리오:
            1. 사용자 등록 및 로그인
            2. 세션 검증 성공
            3. 관리자가 사용자 삭제
            4. 기존 API 키로 세션 검증 실패
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="deleteme",
            email="delete@example.com",
            password="password123",
            role=Role.RESPONDENT
        )
        user_id = result.value

        login_result = auth_service.login("deleteme", "password123", sample_tenant.id)
        api_key = login_result.value

        validate_before = auth_service.validate_session(api_key)
        assert validate_before.is_success()

        delete_result = auth_service.delete_user(sample_admin_user, user_id)
        assert delete_result.is_success()

        validate_after = auth_service.validate_session(api_key)
        assert validate_after.is_failure()

    def test_validate_session_exactly_at_expiry(self, auth_service, session_repo, sample_admin_user, sample_tenant):
        """만료 시각 정확히 일치하는 세션 검증

        시나리오:
            1. 만료 시각이 현재 시각과 정확히 일치하는 세션 생성
            2. 세션 검증 시도
            3. 만료로 처리되는지 확인
        """
        now = datetime.now()
        session = Session(
            id=str(uuid.uuid4()),
            user_id=sample_admin_user.id,
            tenant_id=sample_tenant.id,
            api_key="exact_expiry_key",
            expires_at=now,
            created_at=now - timedelta(days=30)
        )
        session_repo.save_session(session)

        result = auth_service.validate_session("exact_expiry_key")

        assert result.is_failure()
        assert "만료" in result.error

    def test_api_key_uniqueness(self, auth_service, sample_tenant):
        """API 키 고유성 검증

        시나리오:
            1. 여러 사용자를 등록하고 로그인
            2. 생성된 API 키들이 모두 고유한지 확인
        """
        api_keys = set()

        for i in range(10):
            result = auth_service.register_user(
                tenant_id=sample_tenant.id,
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123",
                role=Role.RESPONDENT
            )
            assert result.is_success()

            login_result = auth_service.login(f"user{i}", "password123", sample_tenant.id)
            assert login_result.is_success()

            api_key = login_result.value
            assert api_key not in api_keys
            api_keys.add(api_key)

        assert len(api_keys) == 10

    def test_session_expiry_days_constant(self, auth_service, sample_tenant):
        """세션 만료 기간이 올바르게 설정되는지 확인

        시나리오:
            1. 사용자 등록 및 로그인
            2. 생성된 세션의 만료 시각 확인
            3. 30일 후로 설정되었는지 검증
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="expiryuser",
            email="expiry@example.com",
            password="password123",
            role=Role.RESPONDENT
        )

        before_login = datetime.now()
        login_result = auth_service.login("expiryuser", "password123", sample_tenant.id)
        after_login = datetime.now()
        api_key = login_result.value

        session = auth_service.session_repository.find_session_by_api_key(api_key)
        assert session is not None

        expected_min = before_login + timedelta(days=30)
        expected_max = after_login + timedelta(days=30)

        assert expected_min <= session.expires_at <= expected_max


class TestPasswordManagement:
    """비밀번호 관리 테스트"""

    def test_change_password_via_update_user(self, auth_service, sample_admin_user, sample_tenant):
        """update_user를 통한 비밀번호 변경

        시나리오:
            1. 사용자 등록
            2. 첫 번째 비밀번호로 로그인 성공
            3. 관리자가 비밀번호 변경
            4. 이전 비밀번호로 로그인 실패
            5. 새 비밀번호로 로그인 성공
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="pwduser",
            email="pwd@example.com",
            password="oldpassword",
            role=Role.RESPONDENT
        )
        user_id = result.value

        old_login = auth_service.login("pwduser", "oldpassword", sample_tenant.id)
        assert old_login.is_success()

        update_result = auth_service.update_user(
            admin_user=sample_admin_user,
            user_id=user_id,
            password="newpassword"
        )
        assert update_result.is_success()

        old_pwd_login = auth_service.login("pwduser", "oldpassword", sample_tenant.id)
        assert old_pwd_login.is_failure()

        new_pwd_login = auth_service.login("pwduser", "newpassword", sample_tenant.id)
        assert new_pwd_login.is_success()

    def test_password_hash_strength(self, auth_service):
        """비밀번호 해시 강도 검증

        시나리오:
            1. 비밀번호를 해시
            2. bcrypt rounds=12로 해시되었는지 확인
            3. 해시 결과가 원본과 다른지 확인
        """
        password = "testpassword123"
        hashed = auth_service._hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$12$")
        assert len(hashed) == 60

        verified = bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        assert verified is True

    def test_update_user_password_not_plaintext(self, auth_service, sample_admin_user, sample_tenant, user_repo):
        """비밀번호 변경 시 평문이 아닌 해시로 저장되는지 확인

        시나리오:
            1. 사용자 등록
            2. 비밀번호 변경
            3. 저장소에서 사용자 조회
            4. password_hash가 평문이 아닌지 확인
            5. bcrypt 해시 형식인지 확인
        """
        result = auth_service.register_user(
            tenant_id=sample_tenant.id,
            username="hashtest",
            email="hashtest@example.com",
            password="oldpassword",
            role=Role.RESPONDENT
        )
        user_id = result.value

        new_password = "newsecurepassword"
        auth_service.update_user(
            admin_user=sample_admin_user,
            user_id=user_id,
            password=new_password
        )

        updated_user = user_repo.find_user_by_id(user_id)
        assert updated_user is not None
        assert updated_user.password_hash != new_password
        assert updated_user.password_hash.startswith("$2b$12$")
        assert len(updated_user.password_hash) == 60

        verified = bcrypt.checkpw(new_password.encode("utf-8"), updated_user.password_hash.encode("utf-8"))
        assert verified is True
