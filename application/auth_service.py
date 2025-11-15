import uuid
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from domain.entities.tenant import Tenant
from domain.entities.user import User
from domain.entities.session import Session
from domain.value_objects.role import Role
from domain.value_objects.result import Success, Failure, Result
from domain.repositories.tenant_repository import TenantRepository
from domain.repositories.user_repository import UserRepository
from domain.repositories.session_repository import SessionRepository

if TYPE_CHECKING:
    from application.audit_log_service import AuditLogService


class AuthService:
    """인증 및 인가 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        tenant_repository: 테넌트 저장소
        user_repository: 사용자 저장소
        session_repository: 세션 저장소
        audit_log_service: 감사 로그 서비스 (optional)
    """

    SESSION_EXPIRY_DAYS = 30
    API_KEY_LENGTH = 32

    def __init__(
        self,
        tenant_repository: TenantRepository,
        user_repository: UserRepository,
        session_repository: SessionRepository,
        audit_log_service: "AuditLogService | None" = None,
    ):
        """서비스를 초기화합니다.

        Args:
            tenant_repository: 테넌트 저장소 구현체
            user_repository: 사용자 저장소 구현체
            session_repository: 세션 저장소 구현체
            audit_log_service: 감사 로그 서비스 (optional)
        """
        self.tenant_repository = tenant_repository
        self.user_repository = user_repository
        self.session_repository = session_repository
        self.audit_log_service = audit_log_service

    def register_tenant(self, name: str) -> str:
        """새 테넌트를 등록합니다.

        Args:
            name: 테넌트 이름

        Returns:
            생성된 테넌트 ID
        """
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=name,
            created_at=datetime.now(),
            is_active=True,
        )
        self.tenant_repository.save_tenant(tenant)
        return tenant_id

    def register_user(
        self, tenant_id: str, username: str, email: str, password: str, role: Role
    ) -> Result[str, str]:
        """새 사용자를 등록합니다.

        Args:
            tenant_id: 테넌트 식별자
            username: 사용자명
            email: 이메일
            password: 비밀번호
            role: 사용자 역할

        Returns:
            Success[사용자 ID] 또는 Failure[에러 메시지]
        """
        tenant = self.tenant_repository.find_tenant_by_id(tenant_id)
        if not tenant:
            return Failure(f"테넌트를 찾을 수 없습니다: {tenant_id}")

        if not tenant.is_active:
            return Failure("비활성화된 테넌트입니다")

        existing_email_user = self.user_repository.find_user_by_email(email)
        if existing_email_user:
            return Failure(f"이미 존재하는 이메일입니다: {email}")

        existing_user = self.user_repository.find_user_by_username(username, tenant_id)
        if existing_user:
            return Failure(f"이미 존재하는 사용자명입니다: {username}")

        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=datetime.now(),
            is_active=True,
        )
        self.user_repository.save_user(user)
        return Success(user_id)

    def login(self, email: str, password: str) -> Result[str, str]:
        """사용자 로그인을 처리합니다.

        Args:
            email: 이메일 주소
            password: 비밀번호

        Returns:
            Success[API 키] 또는 Failure[에러 메시지]
        """
        user = self.user_repository.find_user_by_email(email)
        if not user:
            return Failure("이메일 또는 비밀번호가 올바르지 않습니다")

        tenant = self.tenant_repository.find_tenant_by_id(user.tenant_id)
        if not tenant or not tenant.is_active:
            return Failure("비활성화된 테넌트입니다")

        if not user.is_active:
            return Failure("비활성화된 사용자입니다")

        if not self._verify_password(password, user.password_hash):
            return Failure("이메일 또는 비밀번호가 올바르지 않습니다")

        existing_session = self.session_repository.find_session_by_user_id(user.id)
        if existing_session:
            self.session_repository.delete_session(existing_session.id)

        api_key = self._generate_api_key()
        session_id = str(uuid.uuid4())
        now = datetime.now()
        session = Session(
            id=session_id,
            user_id=user.id,
            tenant_id=user.tenant_id,
            api_key=api_key,
            expires_at=now + timedelta(days=self.SESSION_EXPIRY_DAYS),
            created_at=now,
        )
        self.session_repository.save_session(session)
        return Success(api_key)

    def register_super_admin(
        self, system_tenant_id: str, username: str, email: str, password: str
    ) -> Result[str, str]:
        """슈퍼 관리자를 등록합니다.

        Args:
            system_tenant_id: 시스템 테넌트 ID
            username: 사용자명
            email: 이메일
            password: 비밀번호

        Returns:
            Success[사용자 ID] 또는 Failure[에러 메시지]
        """
        return self.register_user(
            tenant_id=system_tenant_id,
            username=username,
            email=email,
            password=password,
            role=Role.SUPER_ADMIN
        )

    def get_all_users(self, admin_user: User) -> Result[list[User], str]:
        """모든 사용자를 조회합니다 (슈퍼 관리자 전용).

        Args:
            admin_user: 관리자 사용자 엔티티

        Returns:
            Success[사용자 목록] 또는 Failure[에러 메시지]
        """
        if not self._is_super_admin(admin_user):
            return Failure("슈퍼 관리자 권한이 필요합니다")

        all_tenants = self.tenant_repository.find_all_tenants()
        all_users = []

        for tenant in all_tenants:
            users = self.user_repository.find_users_by_tenant(tenant.id)
            all_users.extend(users)

        return Success(all_users)

    def logout(self, api_key: str) -> Result[None, str]:
        """사용자 로그아웃을 처리합니다.

        Args:
            api_key: API 키

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        session = self.session_repository.find_session_by_api_key(api_key)
        if not session:
            return Failure("유효하지 않은 세션입니다")

        self.session_repository.delete_session(session.id)
        return Success(None)

    def validate_session(self, api_key: str) -> Result[tuple[User, Session], str]:
        """세션을 검증하고 사용자 정보를 반환합니다.

        Args:
            api_key: API 키

        Returns:
            Success[(User, Session)] 또는 Failure[에러 메시지]
        """
        session = self.session_repository.find_session_by_api_key(api_key)
        if not session:
            return Failure("유효하지 않은 API 키입니다")

        if session.is_expired(datetime.now()):
            self.session_repository.delete_session(session.id)
            return Failure("세션이 만료되었습니다")

        user = self.user_repository.find_user_by_id(session.user_id)
        if not user:
            return Failure("사용자를 찾을 수 없습니다")

        if not user.is_active:
            return Failure("비활성화된 사용자입니다")

        return Success((user, session))

    def check_permission(
        self, user: User, action: str, is_owner: bool = False
    ) -> Result[None, str]:
        """사용자 권한을 확인합니다.

        Args:
            user: 사용자 엔티티
            action: 액션 (create_survey, manage_survey, view_results, manage_users)
            is_owner: 리소스 소유자 여부

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if action == "create_survey":
            if not user.role.can_create_survey():
                return Failure("설문 생성 권한이 없습니다")
        elif action == "manage_survey":
            if not user.role.can_manage_survey(is_owner):
                return Failure("설문 관리 권한이 없습니다")
        elif action == "view_results":
            if not user.role.can_view_results(is_owner):
                return Failure("결과 조회 권한이 없습니다")
        elif action == "manage_users":
            if not user.role.can_manage_users():
                return Failure("사용자 관리 권한이 없습니다")
        else:
            return Failure(f"알 수 없는 액션입니다: {action}")

        return Success(None)

    def _is_super_admin(self, user: User) -> bool:
        """사용자가 슈퍼 관리자인지 확인합니다.

        Args:
            user: 사용자 엔티티

        Returns:
            슈퍼 관리자 여부
        """
        return user.role.can_access_all_tenants()

    def _can_access_tenant(self, user: User, tenant_id: str) -> bool:
        """사용자가 특정 테넌트에 접근 가능한지 확인합니다.

        Args:
            user: 사용자 엔티티
            tenant_id: 테넌트 식별자

        Returns:
            접근 가능 여부
        """
        return self._is_super_admin(user) or user.tenant_id == tenant_id

    def _hash_password(self, password: str) -> str:
        """비밀번호를 해시합니다.

        Args:
            password: 평문 비밀번호

        Returns:
            bcrypt 해시 문자열
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """비밀번호를 검증합니다.

        Args:
            password: 평문 비밀번호
            password_hash: bcrypt 해시

        Returns:
            검증 성공 여부
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def _generate_api_key(self) -> str:
        """API 키를 생성합니다.

        Returns:
            랜덤 API 키 (hex 문자열)
        """
        return secrets.token_hex(self.API_KEY_LENGTH)

    def update_user(self, admin_user: User, user_id: str, **updates) -> Result[None, str]:
        """사용자 정보를 수정합니다.

        Args:
            admin_user: 관리자 사용자 엔티티
            user_id: 수정할 사용자 식별자
            **updates: 수정할 필드 (email, password, role, is_active)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if not admin_user.role.can_manage_users():
            return Failure("사용자 관리 권한이 없습니다")

        target_user = self.user_repository.find_user_by_id(user_id)
        if not target_user:
            return Failure(f"사용자를 찾을 수 없습니다: {user_id}")

        if not self._can_access_tenant(admin_user, target_user.tenant_id):
            return Failure("다른 테넌트의 사용자를 수정할 수 없습니다")

        if "password" in updates:
            updates["password_hash"] = self._hash_password(updates.pop("password"))

        self.user_repository.update_user(user_id, **updates)
        return Success(None)

    def delete_user(self, admin_user: User, user_id: str) -> Result[None, str]:
        """사용자를 삭제합니다.

        Args:
            admin_user: 관리자 사용자 엔티티
            user_id: 삭제할 사용자 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if not admin_user.role.can_manage_users():
            return Failure("사용자 관리 권한이 없습니다")

        target_user = self.user_repository.find_user_by_id(user_id)
        if not target_user:
            return Failure(f"사용자를 찾을 수 없습니다: {user_id}")

        if not self._can_access_tenant(admin_user, target_user.tenant_id):
            return Failure("다른 테넌트의 사용자를 삭제할 수 없습니다")

        session = self.session_repository.find_session_by_user_id(user_id)
        if session:
            self.session_repository.delete_session(session.id)

        self.user_repository.delete_user(user_id)
        return Success(None)

    def update_tenant(self, admin_user: User, tenant_id: str, **updates) -> Result[None, str]:
        """테넌트 정보를 수정합니다.

        Args:
            admin_user: 관리자 사용자 엔티티
            tenant_id: 테넌트 식별자
            **updates: 수정할 필드 (name, is_active)

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if not admin_user.role.can_manage_users():
            return Failure("테넌트 관리 권한이 없습니다")

        if not self._can_access_tenant(admin_user, tenant_id):
            return Failure("다른 테넌트를 수정할 수 없습니다")

        tenant = self.tenant_repository.find_tenant_by_id(tenant_id)
        if not tenant:
            return Failure(f"테넌트를 찾을 수 없습니다: {tenant_id}")

        self.tenant_repository.update_tenant(tenant_id, **updates)
        return Success(None)

    def deactivate_tenant(self, admin_user: User, tenant_id: str) -> Result[None, str]:
        """테넌트를 비활성화합니다.

        Args:
            admin_user: 관리자 사용자 엔티티
            tenant_id: 테넌트 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        if not admin_user.role.can_manage_users():
            return Failure("테넌트 관리 권한이 없습니다")

        if not self._can_access_tenant(admin_user, tenant_id):
            return Failure("다른 테넌트를 비활성화할 수 없습니다")

        tenant = self.tenant_repository.find_tenant_by_id(tenant_id)
        if not tenant:
            return Failure(f"테넌트를 찾을 수 없습니다: {tenant_id}")

        self.tenant_repository.update_tenant(tenant_id, is_active=False)
        return Success(None)
