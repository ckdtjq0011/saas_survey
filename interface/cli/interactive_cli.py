from pathlib import Path
from loguru import logger
from domain.entities.user import User
from interface.cli.commands import Commands
from interface.cli.session_manager import SessionManager
from interface.cli.ui_helper import ConsoleUI, print_header, print_info
from interface.cli.handlers import AuthHandler, SurveyHandler, ResponseHandler


class InteractiveCLI:
    """멀티테넌트 인터랙티브 CLI 애플리케이션입니다.

    Attributes:
        commands: 명령어 핸들러
        session_manager: 세션 관리자
        current_user: 현재 로그인한 사용자
        api_key: 현재 세션 API 키
    """

    def __init__(self, data_dir: Path, debug: bool = False, verbose: bool = False):
        """CLI 애플리케이션을 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
            debug: 디버그 모드 활성화
            verbose: 자세한 출력 모드
        """
        self.commands = Commands(data_dir, debug=debug)
        self.session_manager = SessionManager()
        self.current_user: User | None = None
        self.api_key: str | None = None
        self.ui = ConsoleUI()
        self.debug = debug
        self.verbose = verbose

        self.auth_handler = AuthHandler(self.commands, self.ui)
        self.survey_handler = SurveyHandler(self.commands, self.ui)
        self.response_handler = ResponseHandler(self.commands, self.ui)

    def run(self) -> None:
        """CLI 애플리케이션을 실행합니다."""
        print_header("멀티테넌트 설문조사 플랫폼")

        self._try_load_session()

        while True:
            try:
                if self.current_user:
                    self._show_authenticated_menu()
                else:
                    self._show_guest_menu()

            except KeyboardInterrupt:
                self.ui.print_info("\n\n프로그램을 종료합니다")
                break
            except Exception:
                logger.exception("예상치 못한 오류가 발생했습니다")
                self.ui.print_error("예상치 못한 오류가 발생했습니다")
                self.ui.pause()

    def _try_load_session(self) -> None:
        """저장된 세션을 로드 시도합니다."""
        session_data = self.session_manager.load_session()
        if session_data:
            api_key = session_data["api_key"]
            success, error, user = self.commands.validate_session(api_key)

            if success and user:
                self.current_user = user
                self.api_key = api_key
                self.ui.print_success(f"{user.username}님으로 자동 로그인되었습니다 (역할: {user.role.value})")
            else:
                self.ui.print_info(f"세션이 만료되었습니다: {error}")
                self.session_manager.clear_session()

    def _show_guest_menu(self) -> None:
        """로그인하지 않은 상태의 메뉴를 보여줍니다."""
        menu_items = [
            ("1", "테넌트 등록", "새로운 테넌트(조직)를 등록합니다"),
            ("2", "테넌트 목록 조회", "등록된 테넌트 목록을 확인합니다"),
            ("3", "사용자 등록", "테넌트에 새 사용자를 등록합니다"),
            ("4", "로그인", "사용자 계정으로 로그인합니다"),
            ("0", "종료", "프로그램을 종료합니다"),
        ]
        self.ui.print_menu(menu_items)

        choice = self.ui.get_input("선택")

        if choice == "1":
            self.auth_handler.register_tenant_flow()
        elif choice == "2":
            self._list_tenants_flow()
        elif choice == "3":
            self.auth_handler.register_user_flow()
        elif choice == "4":
            self._login_flow()
        elif choice == "0":
            self.ui.print_info("프로그램을 종료합니다")
            exit(0)
        else:
            self.ui.print_error("잘못된 선택입니다")
            self.ui.pause()

    def _show_authenticated_menu(self) -> None:
        """로그인한 상태의 메뉴를 보여줍니다."""
        if not self.current_user:
            return

        tenant_result = self.commands.tenant_repo.find_tenant_by_id(self.current_user.tenant_id)
        tenant_name = tenant_result.name if tenant_result else "알 수 없음"

        self.ui.print_user_info(
            self.current_user.username,
            self.current_user.role.value,
            tenant_name
        )

        menu_table_items = []
        menu_handlers = {}
        item_num = 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "설문 생성", "새로운 설문을 생성합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.create_survey_flow(self.current_user)
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "질문 추가", "기존 설문에 질문을 추가합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.add_question_flow(self.current_user)
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "설문 수정", "기존 설문의 제목과 설명을 수정합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.update_survey_flow(self.current_user)
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "설문 삭제", "설문과 관련 응답을 삭제합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.delete_survey_flow(self.current_user)
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "질문 수정", "기존 질문의 내용을 수정합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.update_question_flow(self.current_user)
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "질문 삭제", "질문과 관련 응답을 삭제합니다"))
            menu_handlers[str(item_num)] = lambda: self.survey_handler.delete_question_flow(self.current_user)
            item_num += 1

        menu_table_items.append((str(item_num), "설문 조회", "설문의 상세 정보를 확인합니다"))
        menu_handlers[str(item_num)] = lambda: self.survey_handler.view_survey_flow(self.current_user)
        item_num += 1

        menu_table_items.append((str(item_num), "설문 목록", "모든 설문 목록을 확인합니다"))
        menu_handlers[str(item_num)] = lambda: self.survey_handler.list_surveys_flow(self.current_user)
        item_num += 1

        menu_table_items.append((str(item_num), "응답 제출", "설문에 응답을 제출합니다"))
        menu_handlers[str(item_num)] = lambda: self.response_handler.submit_response_flow(self.current_user)
        item_num += 1

        menu_table_items.append((str(item_num), "응답 수정", "제출한 응답을 수정합니다"))
        menu_handlers[str(item_num)] = lambda: self.response_handler.update_response_flow(self.current_user)
        item_num += 1

        menu_table_items.append((str(item_num), "응답 삭제", "제출한 응답을 삭제합니다"))
        menu_handlers[str(item_num)] = lambda: self.response_handler.delete_response_flow(self.current_user)
        item_num += 1

        if self.current_user.role.can_view_results(False):
            menu_table_items.append((str(item_num), "결과 조회", "설문 응답 결과를 확인합니다"))
            menu_handlers[str(item_num)] = lambda: self.response_handler.view_results_flow(self.current_user)
            item_num += 1

        menu_table_items.append((str(item_num), "로그아웃", "현재 세션에서 로그아웃합니다"))
        menu_handlers[str(item_num)] = self._logout_flow
        item_num += 1

        menu_table_items.append(("0", "종료", "프로그램을 종료합니다"))

        self.ui.print_menu(menu_table_items)

        choice = self.ui.get_input("선택")

        if choice == "0":
            self.ui.print_info("프로그램을 종료합니다")
            exit(0)
        elif choice in menu_handlers:
            menu_handlers[choice]()
        else:
            self.ui.print_error("잘못된 선택입니다")
            self.ui.pause()


    def _list_tenants_flow(self) -> None:
        """테넌트 목록 조회 플로우를 실행합니다."""
        try:
            self.ui.print_section("테넌트 목록")
            tenants = self.commands.list_tenants()
            self.ui.print_tenants_table(tenants)
            self.ui.pause()
        except Exception:
            logger.exception("테넌트 목록 조회 중 오류 발생")
            self.ui.print_error("테넌트 목록 조회 중 오류가 발생했습니다")
            self.ui.pause()

    def _login_flow(self) -> None:
        """로그인 플로우를 실행하고 세션을 저장합니다."""
        try:
            success, api_key, user = self.auth_handler.login_flow()
            if success and user and api_key:
                self.current_user = user
                self.api_key = api_key
                session_result = self.commands.auth_service.validate_session(api_key)
                if session_result.is_success():
                    _, session = session_result.value
                    self.session_manager.save_session(api_key, user, session)
        except Exception:
            logger.exception("로그인 중 오류 발생")
            self.ui.print_error("로그인 중 오류가 발생했습니다")
            self.ui.pause()

    def _logout_flow(self) -> None:
        """로그아웃 플로우를 실행하고 세션을 정리합니다."""
        try:
            if not self.api_key:
                return

            if self.auth_handler.logout_flow(self.api_key):
                self.session_manager.clear_session()
                self.current_user = None
                self.api_key = None
        except Exception:
            logger.exception("로그아웃 중 오류 발생")
            self.ui.print_error("로그아웃 중 오류가 발생했습니다")
            self.ui.pause()

