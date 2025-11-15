from domain.entities.user import User
from domain.value_objects.role import Role
from interface.cli.handlers.base_handler import BaseHandler
from interface.cli.validators import (
    validate_tenant_name,
    validate_username,
    validate_email,
    validate_password,
)


class AuthHandler(BaseHandler):
    """인증 및 사용자 관리를 처리하는 Handler입니다."""

    def register_tenant_flow(self) -> None:
        """테넌트 등록 플로우를 실행합니다."""
        try:
            self.ui.print_section("테넌트 등록")

            name = self.ui.get_validated_input(
                "테넌트 이름 (2-50자)", validate_tenant_name
            )

            tenant_id = self.commands.register_tenant(name)
            self.ui.print_success(f"테넌트가 등록되었습니다. ID: {tenant_id}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("테넌트 등록", e)
        finally:
            self.ui.pause()

    def register_user_flow(self) -> None:
        """사용자 등록 플로우를 실행합니다."""
        try:
            self.ui.print_section("사용자 등록")

            tenant_id = self._select_tenant()
            if not tenant_id:
                return

            username = self.ui.get_validated_input(
                "사용자명 (영문 시작, 3-20자)", validate_username
            )
            email = self.ui.get_validated_input(
                "이메일 (예: user@example.com)", validate_email
            )
            password = self.ui.get_validated_input(
                "비밀번호 (8자 이상, 영문+숫자)", validate_password
            )
            role = self.ui.get_choice(
                "역할 선택",
                choices=["tenant_admin", "survey_manager", "respondent"],
            )

            success, result = self.commands.register_user(
                tenant_id, username, email, password, role
            )

            if success:
                self.ui.print_success(f"사용자가 등록되었습니다. ID: {result}")
            else:
                self.ui.print_error(f"사용자 등록 실패: {result}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("사용자 등록", e)
        finally:
            self.ui.pause()

    def login_flow(self) -> tuple[bool, str, User | None]:
        """로그인 플로우를 실행합니다.

        Returns:
            (로그인 성공 여부, API 키, User 엔티티)
        """
        try:
            self.ui.print_section("로그인")

            email = self.ui.get_input("이메일")
            password = self.ui.get_input("비밀번호")

            success, result, user = self.commands.login(email, password)

            if success:
                self.ui.print_success(f"로그인 성공! 환영합니다, {user.username}님")
                return True, result, user
            else:
                self.ui.print_error(f"로그인 실패: {result}")
                return False, "", None

        except Exception as e:
            self.handle_error("로그인", e)
            return False, "", None
        finally:
            self.ui.pause()

    def logout_flow(self, api_key: str) -> bool:
        """로그아웃 플로우를 실행합니다.

        Args:
            api_key: API 키

        Returns:
            로그아웃 성공 여부
        """
        try:
            if self.confirm_operation("로그아웃 하시겠습니까?"):
                success = self.commands.logout(api_key)
                if success:
                    self.ui.print_success("로그아웃되었습니다")
                    return True
                else:
                    self.ui.print_error("로그아웃 실패")
                    return False
            return False

        except Exception as e:
            self.handle_error("로그아웃", e)
            return False

    def _select_tenant(self) -> str | None:
        """테넌트를 선택합니다.

        Returns:
            선택된 테넌트 ID, 취소 시 None
        """
        tenants = self.commands.list_tenants()

        if not tenants:
            self.ui.print_info("등록된 테넌트가 없습니다")
            return None

        self.ui.print_tenants_table(tenants)

        try:
            choice = self.ui.get_int_input("테넌트 번호", default=1)
            if 1 <= choice <= len(tenants):
                return tenants[choice - 1]["id"]
            else:
                self.ui.print_error("잘못된 선택입니다")
                return None
        except (ValueError, IndexError):
            self.ui.print_error("잘못된 입력입니다")
            return None
