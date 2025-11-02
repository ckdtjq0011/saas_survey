from typing import Optional, TextIO, Any
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.text import Text
from rich import box


DEFAULT_WIDTH = 80
PANEL_WIDTH = 70


class ConsoleUI:
    """Rich 기반 콘솔 UI 클래스

    입출력 주입이 가능하여 테스트 가능한 구조입니다.
    """

    def __init__(
        self,
        output_stream: Optional[TextIO] = None,
        input_stream: Optional[TextIO] = None,
        width: int = DEFAULT_WIDTH
    ):
        """ConsoleUI를 초기화합니다.

        Args:
            output_stream: 출력 스트림 (None이면 stdout)
            input_stream: 입력 스트림 (None이면 stdin)
            width: 콘솔 너비
        """
        self.console = Console(file=output_stream, width=width)
        self.input_stream = input_stream

    def print_header(self, title: str) -> None:
        """헤더를 출력합니다.

        Args:
            title: 헤더 제목
        """
        self.console.print()
        self.console.print(
            Panel(
                Text(title, justify="center", style="bold cyan"),
                box=box.DOUBLE,
                style="cyan",
                width=PANEL_WIDTH
            )
        )

    def print_section(self, title: str) -> None:
        """섹션 제목을 출력합니다.

        Args:
            title: 섹션 제목
        """
        self.console.print()
        self.console.rule(f"[bold blue]{title}[/bold blue]", style="blue")

    def print_success(self, message: str) -> None:
        """성공 메시지를 출력합니다.

        Args:
            message: 성공 메시지
        """
        self.console.print(f"[green][OK][/green] {message}")

    def print_error(self, message: str) -> None:
        """에러 메시지를 출력합니다.

        Args:
            message: 에러 메시지
        """
        self.console.print(f"[red][ERROR][/red] {message}")

    def print_info(self, message: str) -> None:
        """정보 메시지를 출력합니다.

        Args:
            message: 정보 메시지
        """
        self.console.print(f"[blue][INFO][/blue] {message}")

    def print_warning(self, message: str) -> None:
        """경고 메시지를 출력합니다.

        Args:
            message: 경고 메시지
        """
        self.console.print(f"[yellow][WARN][/yellow] {message}")

    def print_menu(self, items: list[tuple[str, str, str]]) -> None:
        """메뉴를 테이블 형태로 출력합니다.

        Args:
            items: (번호, 기능명, 설명) 튜플 리스트
        """
        table = Table(
            title="메뉴",
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=True
        )

        table.add_column("번호", justify="center", style="cyan", width=6)
        table.add_column("기능", style="green", width=20)
        table.add_column("설명", style="white", width=40)

        for number, name, description in items:
            table.add_row(number, name, description)

        self.console.print(table)

    def print_user_info(self, username: str, role: str, tenant_name: str) -> None:
        """로그인 사용자 정보를 패널로 출력합니다.

        Args:
            username: 사용자명
            role: 역할
            tenant_name: 테넌트명
        """
        info_text = Text()
        info_text.append("사용자: ", style="bold")
        info_text.append(f"{username}\n", style="cyan")
        info_text.append("역할: ", style="bold")
        info_text.append(f"{role}\n", style="green")
        info_text.append("테넌트: ", style="bold")
        info_text.append(tenant_name, style="yellow")

        panel = Panel(
            info_text,
            title="로그인 정보",
            border_style="green",
            box=box.ROUNDED,
            width=50
        )
        self.console.print(panel)

    def print_surveys_table(self, surveys: list[dict[str, Any]]) -> None:
        """설문 목록을 테이블로 출력합니다.

        Args:
            surveys: 설문 정보 딕셔너리 리스트
                    (id, title, owner, question_count, created_at 포함)
        """
        if not surveys:
            self.print_info("설문이 없습니다.")
            return

        table = Table(
            title="설문 목록",
            box=box.ROUNDED,
            header_style="bold cyan",
            show_header=True,
            show_lines=False
        )

        table.add_column("번호", justify="center", style="cyan", width=6)
        table.add_column("제목", style="green", width=25)
        table.add_column("소유자", style="yellow", width=15)
        table.add_column("질문 수", justify="center", style="magenta", width=8)
        table.add_column("생성일", style="white", width=18)

        for idx, survey in enumerate(surveys, 1):
            created_at = survey.get("created_at", "")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M")
            elif isinstance(created_at, str) and len(created_at) > 19:
                created_at = created_at[:19]

            table.add_row(
                str(idx),
                survey.get("title", "제목 없음"),
                survey.get("owner", "알 수 없음"),
                str(survey.get("question_count", 0)),
                created_at
            )

        self.console.print(table)

    def print_questions_tree(self, survey_title: str, questions: list[dict[str, Any]]) -> None:
        """질문 목록을 트리 형태로 출력합니다.

        Args:
            survey_title: 설문 제목
            questions: 질문 정보 딕셔너리 리스트
                      (text, question_type, options 포함)
        """
        tree = Tree(f"[bold cyan]{survey_title}[/bold cyan]")

        for idx, question in enumerate(questions, 1):
            q_type = question.get("question_type", "TEXT")
            q_text = question.get("text", "질문 없음")

            question_node = tree.add(f"[green]Q{idx}.[/green] {q_text} [yellow]({q_type})[/yellow]")

            if q_type == "MULTIPLE_CHOICE" and question.get("options"):
                options_node = question_node.add("[magenta]선택지:[/magenta]")
                for opt in question.get("options", []):
                    options_node.add(f"• {opt}")
            elif q_type == "RATING":
                question_node.add("[magenta]평점: 1-5[/magenta]")

        self.console.print(tree)

    def print_results_table(self, results: list[dict[str, Any]]) -> None:
        """설문 결과를 테이블로 출력합니다.

        Args:
            results: 결과 정보 딕셔너리 리스트
                    (question, answer_distribution 포함)
        """
        for result in results:
            question = result.get("question", "질문 없음")
            distribution = result.get("answer_distribution", {})

            self.console.print(f"\n[bold cyan]질문:[/bold cyan] {question}")

            if not distribution:
                self.console.print("  [yellow]응답이 없습니다.[/yellow]")
                continue

            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold magenta"
            )

            table.add_column("답변", style="green", width=30)
            table.add_column("응답 수", justify="right", style="cyan", width=10)
            table.add_column("비율", justify="right", style="yellow", width=10)

            total = sum(distribution.values())
            for answer, count in distribution.items():
                percentage = (count / total * 100) if total > 0 else 0
                table.add_row(
                    str(answer),
                    str(count),
                    f"{percentage:.1f}%"
                )

            self.console.print(table)

    def print_tenants_table(self, tenants: list[dict[str, Any]]) -> None:
        """테넌트 목록을 테이블로 출력합니다.

        Args:
            tenants: 테넌트 정보 딕셔너리 리스트
                    (id, name, created_at, is_active 포함)
        """
        if not tenants:
            self.print_info("테넌트가 없습니다.")
            return

        table = Table(
            title="테넌트 목록",
            box=box.ROUNDED,
            header_style="bold cyan",
            show_header=True
        )

        table.add_column("번호", justify="center", style="cyan", width=6)
        table.add_column("ID", style="yellow", width=36)
        table.add_column("이름", style="green", width=20)
        table.add_column("생성일", style="white", width=18)
        table.add_column("상태", justify="center", style="magenta", width=8)

        for idx, tenant in enumerate(tenants, 1):
            created_at = tenant.get("created_at", "")
            if isinstance(created_at, datetime):
                created_at = created_at.strftime("%Y-%m-%d %H:%M")
            elif isinstance(created_at, str) and len(created_at) > 19:
                created_at = created_at[:19]

            is_active = tenant.get("is_active", True)
            status = "[green]활성[/green]" if is_active else "[red]비활성[/red]"

            table.add_row(
                str(idx),
                tenant.get("id", "알 수 없음"),
                tenant.get("name", "이름 없음"),
                created_at,
                status
            )

        self.console.print(table)

    def get_input(self, prompt: str, default: str = "") -> str:
        """사용자 입력을 받습니다.

        Args:
            prompt: 입력 프롬프트
            default: 기본값

        Returns:
            사용자 입력 문자열
        """
        if self.input_stream:
            line = self.input_stream.readline()
            return line.strip() if line else default

        if default:
            return Prompt.ask(f"[bold]{prompt}[/bold]", default=default, console=self.console)
        return Prompt.ask(f"[bold]{prompt}[/bold]", console=self.console)

    def get_int_input(self, prompt: str, default: Optional[int] = None) -> int:
        """정수 입력을 받습니다.

        Args:
            prompt: 입력 프롬프트
            default: 기본값

        Returns:
            입력받은 정수
        """
        if self.input_stream:
            line = self.input_stream.readline()
            return int(line.strip()) if line.strip() else (default or 0)

        if default is not None:
            return IntPrompt.ask(f"[bold]{prompt}[/bold]", default=default, console=self.console)
        return IntPrompt.ask(f"[bold]{prompt}[/bold]", console=self.console)

    def get_choice(self, prompt: str, choices: list[str]) -> str:
        """선택 입력을 받습니다.

        Args:
            prompt: 입력 프롬프트
            choices: 선택지 리스트

        Returns:
            선택된 값
        """
        if self.input_stream:
            line = self.input_stream.readline()
            return line.strip()

        return Prompt.ask(
            f"[bold]{prompt}[/bold]",
            choices=choices,
            console=self.console
        )

    def confirm(self, prompt: str, default: bool = False) -> bool:
        """확인을 요청합니다.

        Args:
            prompt: 확인 프롬프트
            default: 기본값

        Returns:
            True if 확인, False otherwise
        """
        if self.input_stream:
            line = self.input_stream.readline()
            response = line.strip().lower()
            return response in ("y", "yes")

        return Confirm.ask(f"[bold]{prompt}[/bold]", default=default, console=self.console)

    def pause(self) -> None:
        """사용자가 엔터를 누를 때까지 대기합니다."""
        if self.input_stream:
            self.input_stream.readline()
            return

        self.console.print()
        Prompt.ask("[dim]계속하려면 엔터를 누르세요[/dim]", default="", show_default=False, console=self.console)

    def clear(self) -> None:
        """콘솔을 클리어합니다."""
        self.console.clear()


_default_ui: Optional[ConsoleUI] = None


def get_ui() -> ConsoleUI:
    """기본 UI 인스턴스를 반환합니다.

    Returns:
        ConsoleUI 인스턴스
    """
    global _default_ui
    if _default_ui is None:
        _default_ui = ConsoleUI()
    return _default_ui


def set_ui(ui: ConsoleUI) -> None:
    """기본 UI 인스턴스를 설정합니다.

    Args:
        ui: ConsoleUI 인스턴스
    """
    global _default_ui
    _default_ui = ui


def print_header(title: str) -> None:
    """헤더를 출력합니다 (하위 호환성)."""
    get_ui().print_header(title)


def print_section(title: str) -> None:
    """섹션 제목을 출력합니다 (하위 호환성)."""
    get_ui().print_section(title)


def print_success(message: str) -> None:
    """성공 메시지를 출력합니다 (하위 호환성)."""
    get_ui().print_success(message)


def print_error(message: str) -> None:
    """에러 메시지를 출력합니다 (하위 호환성)."""
    get_ui().print_error(message)


def print_info(message: str) -> None:
    """정보 메시지를 출력합니다 (하위 호환성)."""
    get_ui().print_info(message)


def get_input(prompt: str) -> str:
    """사용자 입력을 받습니다 (하위 호환성)."""
    return get_ui().get_input(prompt)


def confirm(prompt: str) -> bool:
    """확인을 요청합니다 (하위 호환성)."""
    return get_ui().confirm(prompt)


def pause() -> None:
    """사용자가 엔터를 누를 때까지 대기합니다 (하위 호환성)."""
    get_ui().pause()
