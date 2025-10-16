"""사용자 역할을 정의하는 값 객체입니다."""

from enum import Enum


class Role(Enum):
    """사용자 역할을 나타내는 Enum입니다.

    Attributes:
        TENANT_ADMIN: 테넌트 관리자 (모든 권한)
        SURVEY_MANAGER: 설문 관리자 (설문 CRUD, 결과 조회)
        RESPONDENT: 응답자 (응답 제출만 가능)
    """
    TENANT_ADMIN = "tenant_admin"
    SURVEY_MANAGER = "survey_manager"
    RESPONDENT = "respondent"

    def can_create_survey(self) -> bool:
        """설문 생성 권한이 있는지 확인합니다.

        Returns:
            True if 권한 있음, False otherwise
        """
        return self in (Role.TENANT_ADMIN, Role.SURVEY_MANAGER)

    def can_manage_survey(self, is_owner: bool) -> bool:
        """설문 관리 권한이 있는지 확인합니다.

        Args:
            is_owner: 설문 소유자 여부

        Returns:
            True if 권한 있음, False otherwise
        """
        if self == Role.TENANT_ADMIN:
            return True
        if self == Role.SURVEY_MANAGER and is_owner:
            return True
        return False

    def can_submit_response(self) -> bool:
        """응답 제출 권한이 있는지 확인합니다.

        Returns:
            True if 권한 있음, False otherwise
        """
        return True  # 모든 역할이 응답 가능

    def can_view_results(self, is_owner: bool) -> bool:
        """결과 조회 권한이 있는지 확인합니다.

        Args:
            is_owner: 설문 소유자 여부

        Returns:
            True if 권한 있음, False otherwise
        """
        if self == Role.TENANT_ADMIN:
            return True
        if self == Role.SURVEY_MANAGER and is_owner:
            return True
        return False

    def can_manage_users(self) -> bool:
        """사용자 관리 권한이 있는지 확인합니다.

        Returns:
            True if 권한 있음, False otherwise
        """
        return self == Role.TENANT_ADMIN
