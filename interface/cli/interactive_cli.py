import logging
from pathlib import Path
from domain.entities.user import User
from interface.cli.commands import Commands
from interface.cli.session_manager import SessionManager
from interface.cli.ui_helper import (
    ConsoleUI,
    print_header,
    print_section,
    get_input,
    print_success,
    print_error,
    print_info,
    confirm,
    pause,
)


logger = logging.getLogger(__name__)


class InteractiveCLI:
    """멀티테넌트 인터랙티브 CLI 애플리케이션입니다.

    Attributes:
        commands: 명령어 핸들러
        session_manager: 세션 관리자
        current_user: 현재 로그인한 사용자
        api_key: 현재 세션 API 키
    """

    def __init__(self, data_dir: Path):
        """CLI 애플리케이션을 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.commands = Commands(data_dir)
        self.session_manager = SessionManager()
        self.current_user: User | None = None
        self.api_key: str | None = None
        self.ui = ConsoleUI()

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
                print_info("\n\n프로그램을 종료합니다")
                break
            except Exception:
                logger.exception("예상치 못한 오류가 발생했습니다")
                print_error("예상치 못한 오류가 발생했습니다")
                pause()

    def _try_load_session(self) -> None:
        """저장된 세션을 로드 시도합니다."""
        session_data = self.session_manager.load_session()
        if session_data:
            api_key = session_data["api_key"]
            success, error, user = self.commands.validate_session(api_key)

            if success and user:
                self.current_user = user
                self.api_key = api_key
                print_success(f"{user.username}님으로 자동 로그인되었습니다 (역할: {user.role.value})")
            else:
                print_info(f"세션이 만료되었습니다: {error}")
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
            self._register_tenant_flow()
        elif choice == "2":
            self._list_tenants_flow()
        elif choice == "3":
            self._register_user_flow()
        elif choice == "4":
            self._login_flow()
        elif choice == "0":
            print_info("프로그램을 종료합니다")
            exit(0)
        else:
            print_error("잘못된 선택입니다")
            pause()

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
            menu_handlers[str(item_num)] = self._create_survey_flow
            item_num += 1

        if self.current_user.role.can_create_survey():
            menu_table_items.append((str(item_num), "질문 추가", "기존 설문에 질문을 추가합니다"))
            menu_handlers[str(item_num)] = self._add_question_flow
            item_num += 1

        menu_table_items.append((str(item_num), "설문 조회", "설문의 상세 정보를 확인합니다"))
        menu_handlers[str(item_num)] = self._view_survey_flow
        item_num += 1

        menu_table_items.append((str(item_num), "설문 목록", "모든 설문 목록을 확인합니다"))
        menu_handlers[str(item_num)] = self._list_surveys_flow
        item_num += 1

        menu_table_items.append((str(item_num), "응답 제출", "설문에 응답을 제출합니다"))
        menu_handlers[str(item_num)] = self._submit_response_flow
        item_num += 1

        if self.current_user.role.can_view_results(False):
            menu_table_items.append((str(item_num), "결과 조회", "설문 응답 결과를 확인합니다"))
            menu_handlers[str(item_num)] = self._view_results_flow
            item_num += 1

        menu_table_items.append((str(item_num), "로그아웃", "현재 세션에서 로그아웃합니다"))
        menu_handlers[str(item_num)] = self._logout_flow
        item_num += 1

        menu_table_items.append(("0", "종료", "프로그램을 종료합니다"))

        self.ui.print_menu(menu_table_items)

        choice = self.ui.get_input("선택")

        if choice == "0":
            print_info("프로그램을 종료합니다")
            exit(0)
        elif choice in menu_handlers:
            menu_handlers[choice]()
        else:
            print_error("잘못된 선택입니다")
            pause()

    def _register_tenant_flow(self) -> None:
        """테넌트 등록 플로우를 실행합니다."""
        try:
            print_section("테넌트 등록")

            name = get_input("테넌트 이름 (조직명)")
            if not name:
                print_error("테넌트 이름을 입력해주세요")
                pause()
                return

            tenant_id = self.commands.register_tenant(name)
            print_success(f"테넌트가 등록되었습니다")
            print_info(f"테넌트 ID: {tenant_id}")
            print_info("이제 사용자를 등록해주세요")
            pause()

        except Exception:
            logger.exception("테넌트 등록 중 오류 발생")
            print_error("테넌트 등록 중 오류가 발생했습니다")
            pause()

    def _list_tenants_flow(self) -> None:
        """테넌트 목록 조회 플로우를 실행합니다."""
        try:
            print_section("테넌트 목록")

            tenants = self.commands.list_tenants()
            self.ui.print_tenants_table(tenants)

            self.ui.pause()

        except Exception:
            logger.exception("테넌트 목록 조회 중 오류 발생")
            print_error("테넌트 목록 조회 중 오류가 발생했습니다")
            self.ui.pause()

    def _register_user_flow(self) -> None:
        """사용자 등록 플로우를 실행합니다."""
        try:
            print_section("사용자 등록")

            tenant_id = get_input("테넌트 ID")
            if not tenant_id:
                print_error("테넌트 ID를 입력해주세요")
                pause()
                return

            username = get_input("사용자명 (최소 3자)")
            if not username:
                print_error("사용자명을 입력해주세요")
                pause()
                return

            email = get_input("이메일")
            if not email:
                print_error("이메일을 입력해주세요")
                pause()
                return

            password = get_input("비밀번호")
            if not password:
                print_error("비밀번호를 입력해주세요")
                pause()
                return

            logger.info("\n역할 선택:")
            logger.info("1. TENANT_ADMIN (모든 권한)")
            logger.info("2. SURVEY_MANAGER (설문 관리, 소유 설문 결과 조회)")
            logger.info("3. RESPONDENT (응답 제출만 가능)")

            role_choice = get_input("역할 선택")
            role_map = {
                "1": "tenant_admin",
                "2": "survey_manager",
                "3": "respondent",
            }

            role = role_map.get(role_choice)
            if not role:
                print_error("잘못된 역할 선택입니다")
                pause()
                return

            success, message = self.commands.register_user(tenant_id, username, email, password, role)

            if success:
                print_success("사용자가 등록되었습니다")
                print_info(f"사용자 ID: {message}")
                print_info("이제 로그인해주세요")
            else:
                print_error(f"사용자 등록 실패: {message}")

            pause()

        except Exception:
            logger.exception("사용자 등록 중 오류 발생")
            print_error("사용자 등록 중 오류가 발생했습니다")
            pause()

    def _login_flow(self) -> None:
        """로그인 플로우를 실행합니다."""
        try:
            print_section("로그인")

            tenant_id = get_input("테넌트 ID")
            if not tenant_id:
                print_error("테넌트 ID를 입력해주세요")
                pause()
                return

            username = get_input("사용자명")
            if not username:
                print_error("사용자명을 입력해주세요")
                pause()
                return

            password = get_input("비밀번호")
            if not password:
                print_error("비밀번호를 입력해주세요")
                pause()
                return

            success, message, user = self.commands.login(username, password, tenant_id)

            if success and user:
                self.current_user = user
                self.api_key = message
                session_result = self.commands.auth_service.validate_session(message)
                if session_result.is_success():
                    _, session = session_result.value
                    self.session_manager.save_session(message, user, session)

                print_success(f"{user.username}님 환영합니다!")
                print_info(f"역할: {user.role.value}")
            else:
                print_error(f"로그인 실패: {message}")

            pause()

        except Exception:
            logger.exception("로그인 중 오류 발생")
            print_error("로그인 중 오류가 발생했습니다")
            pause()

    def _logout_flow(self) -> None:
        """로그아웃 플로우를 실행합니다."""
        try:
            if not self.api_key:
                return

            if self.commands.logout(self.api_key):
                self.session_manager.clear_session()
                print_success("로그아웃되었습니다")
                self.current_user = None
                self.api_key = None
            else:
                print_error("로그아웃 실패")

            pause()

        except Exception:
            logger.exception("로그아웃 중 오류 발생")
            print_error("로그아웃 중 오류가 발생했습니다")
            pause()

    def _resolve_survey_choice(self, choice: str, surveys: list[dict[str, str]]) -> str | None:
        """사용자 입력을 설문 ID로 변환합니다."""
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(surveys):
                return surveys[idx - 1]['id']
            return None
        return choice if choice else None

    def _create_survey_flow(self) -> None:
        """설문 생성 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("설문 생성")

            title = get_input("설문 제목")
            if not title:
                print_error("제목을 입력해주세요")
                pause()
                return

            description = get_input("설문 설명")
            if not description:
                print_error("설명을 입력해주세요")
                pause()
                return

            success, message = self.commands.create_survey(self.current_user, title, description)

            if success:
                print_success(f"설문이 생성되었습니다 (ID: {message})")
            else:
                print_error(f"설문 생성 실패: {message}")

            pause()

        except Exception:
            logger.exception("설문 생성 중 오류 발생")
            print_error("설문 생성 중 오류가 발생했습니다")
            pause()

    def _add_question_flow(self) -> None:
        """질문 추가 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("질문 추가")

            surveys = self.commands.list_surveys(self.current_user)
            if not surveys:
                print_error("등록된 설문이 없습니다. 먼저 설문을 생성해주세요")
                pause()
                return

            logger.info("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                owner_marker = " [내 설문]" if survey['owner_id'] == self.current_user.id else ""
                logger.info(f"{idx}. [{survey['id']}] {survey['title']}{owner_marker}")

            choice = get_input("\n설문 번호 또는 ID")
            if not choice:
                print_error("설문 번호 또는 ID를 입력해주세요")
                pause()
                return

            survey_id = self._resolve_survey_choice(choice, surveys)
            if not survey_id:
                print_error("잘못된 번호 또는 ID입니다")
                pause()
                return

            text = get_input("질문 내용")
            if not text:
                print_error("질문 내용을 입력해주세요")
                pause()
                return

            logger.info("\n질문 유형:")
            logger.info("1. 텍스트 (text)")
            logger.info("2. 평점 (rating)")
            logger.info("3. 객관식 (choice)")

            q_type_choice = get_input("유형 선택")
            question_type_map = {
                "1": "text",
                "2": "rating",
                "3": "choice",
            }

            question_type = question_type_map.get(q_type_choice)
            if not question_type:
                print_error("잘못된 유형입니다")
                pause()
                return

            options = None
            if question_type == "choice":
                options_input = get_input("선택지 (|로 구분)")
                if not options_input:
                    print_error("선택지를 입력해주세요")
                    pause()
                    return
                options = [opt.strip() for opt in options_input.split("|") if opt.strip()]
                if len(options) < 2:
                    print_error("선택지는 최소 2개 이상이어야 합니다")
                    pause()
                    return

            success, message = self.commands.add_question(self.current_user, survey_id, text, question_type, options)

            if success:
                print_success(f"질문이 추가되었습니다 (ID: {message})")
            else:
                print_error(f"질문 추가 실패: {message}")

            pause()

        except Exception:
            logger.exception("질문 추가 중 오류 발생")
            print_error("질문 추가 중 오류가 발생했습니다")
            pause()

    def _view_survey_flow(self) -> None:
        """설문 조회 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("설문 조회")

            surveys = self.commands.list_surveys(self.current_user)
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            logger.info("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                owner_marker = " [내 설문]" if survey['owner_id'] == self.current_user.id else ""
                logger.info(f"{idx}. [{survey['id']}] {survey['title']}{owner_marker}")

            choice = get_input("\n설문 번호 또는 ID")
            if not choice:
                print_error("설문 번호 또는 ID를 입력해주세요")
                pause()
                return

            survey_id = self._resolve_survey_choice(choice, surveys)
            if not survey_id:
                print_error("잘못된 번호 또는 ID입니다")
                pause()
                return

            success, error, survey_data = self.commands.get_survey(self.current_user, survey_id)
            if not success or not survey_data:
                print_error(f"설문 조회 실패: {error}")
                self.ui.pause()
                return

            self.ui.console.print(f"\n[bold cyan]제목:[/bold cyan] {survey_data['title']}")
            self.ui.console.print(f"[bold cyan]설명:[/bold cyan] {survey_data['description']}")
            self.ui.console.print(f"[bold cyan]생성일:[/bold cyan] {survey_data['created_at']}")
            self.ui.console.print()

            if survey_data['questions']:
                questions_data = []
                for question in survey_data['questions']:
                    questions_data.append({
                        "text": question['text'],
                        "question_type": question['type'],
                        "options": question.get('options', [])
                    })

                self.ui.print_questions_tree(survey_data['title'], questions_data)
            else:
                self.ui.print_info("질문이 없습니다")

            self.ui.pause()

        except Exception:
            logger.exception("설문 조회 중 오류 발생")
            print_error("설문 조회 중 오류가 발생했습니다")
            pause()

    def _list_surveys_flow(self) -> None:
        """설문 목록 조회 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("설문 목록")

            surveys = self.commands.list_surveys(self.current_user)

            if not surveys:
                self.ui.print_info("등록된 설문이 없습니다")
            else:
                survey_table_data = []
                for survey in surveys:
                    owner_id = survey.get('owner_id', '')
                    owner_marker = " [내 설문]" if owner_id == self.current_user.id else ""

                    owner_user = self.commands.user_repo.find_user_by_id(owner_id)
                    owner_name = owner_user.username if owner_user else "알 수 없음"

                    survey_table_data.append({
                        "id": survey.get('id', ''),
                        "title": survey.get('title', '제목 없음') + owner_marker,
                        "owner": owner_name,
                        "question_count": survey.get('question_count', 0),
                        "created_at": survey.get('created_at', '')
                    })

                self.ui.print_surveys_table(survey_table_data)

            self.ui.pause()

        except Exception:
            logger.exception("설문 목록 조회 중 오류 발생")
            print_error("설문 목록 조회 중 오류가 발생했습니다")
            self.ui.pause()

    def _submit_response_flow(self) -> None:
        """응답 제출 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("응답 제출")

            surveys = self.commands.list_surveys(self.current_user)
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            logger.info("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                logger.info(f"{idx}. [{survey['id']}] {survey['title']}")

            choice = get_input("\n설문 번호 또는 ID")
            if not choice:
                print_error("설문 번호 또는 ID를 입력해주세요")
                pause()
                return

            survey_id = self._resolve_survey_choice(choice, surveys)
            if not survey_id:
                print_error("잘못된 번호 또는 ID입니다")
                pause()
                return

            success, error, survey_data = self.commands.get_survey(self.current_user, survey_id)
            if not success or not survey_data:
                print_error(f"설문 조회 실패: {error}")
                pause()
                return

            logger.info(f"\n설문: {survey_data['title']}")

            if not survey_data['questions']:
                print_error("이 설문에는 질문이 없습니다")
                pause()
                return

            answers = {}
            logger.info("\n각 질문에 답변해주세요:")

            for idx, question in enumerate(survey_data['questions'], 1):
                logger.info(f"\n[{idx}] {question['text']}")
                logger.info(f"    유형: {question['type']}")

                if question['type'] == 'choice':
                    logger.info(f"    선택지: {', '.join(question['options'])}")
                elif question['type'] == 'rating':
                    logger.info("    1-5 사이의 숫자를 입력하세요")

                answer = get_input("답변")
                if not answer:
                    print_error("답변을 입력해주세요")
                    pause()
                    return

                answers[question['id']] = answer

            if confirm("응답을 제출하시겠습니까?"):
                success, error = self.commands.submit_response(self.current_user, survey_id, answers)
                if success:
                    print_success("응답이 제출되었습니다")
                else:
                    print_error(f"응답 제출 실패: {error}")
            else:
                print_info("응답 제출이 취소되었습니다")

            pause()

        except Exception:
            logger.exception("응답 제출 중 오류 발생")
            print_error("응답 제출 중 오류가 발생했습니다")
            pause()

    def _view_results_flow(self) -> None:
        """결과 조회 플로우를 실행합니다."""
        if not self.current_user:
            return

        try:
            print_section("결과 조회")

            surveys = self.commands.list_surveys(self.current_user)
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            logger.info("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                owner_marker = " [내 설문]" if survey['owner_id'] == self.current_user.id else ""
                logger.info(f"{idx}. [{survey['id']}] {survey['title']}{owner_marker}")

            choice = get_input("\n설문 번호 또는 ID")
            if not choice:
                print_error("설문 번호 또는 ID를 입력해주세요")
                pause()
                return

            survey_id = self._resolve_survey_choice(choice, surveys)
            if not survey_id:
                print_error("잘못된 번호 또는 ID입니다")
                pause()
                return

            success, error, results = self.commands.get_results(self.current_user, survey_id)

            if not success or not results:
                print_error(f"결과 조회 실패: {error}")
                self.ui.pause()
                return

            results_data = []
            for question_id, stats in results.items():
                result_item = {
                    "question": stats['question'],
                }

                if 'distribution' in stats:
                    result_item["answer_distribution"] = stats['distribution']
                elif 'answers' in stats:
                    answer_counts = {}
                    for text in stats['answers']:
                        answer_counts[text] = answer_counts.get(text, 0) + 1
                    result_item["answer_distribution"] = answer_counts
                else:
                    result_item["answer_distribution"] = {}

                results_data.append(result_item)

            self.ui.console.print("\n[bold green]설문 결과[/bold green]\n")
            self.ui.print_results_table(results_data)

            self.ui.pause()

        except Exception:
            logger.exception("결과 조회 중 오류 발생")
            print_error("결과 조회 중 오류가 발생했습니다")
            pause()
