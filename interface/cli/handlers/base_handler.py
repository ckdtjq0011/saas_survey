from abc import ABC
from loguru import logger
from interface.cli.ui_helper import ConsoleUI
from interface.cli.commands import Commands


class BaseHandler(ABC):
    """Handler 기본 클래스

    모든 Handler는 이 클래스를 상속받습니다.
    UI와 Commands에 대한 일관된 접근을 제공합니다.
    """

    def __init__(self, commands: Commands, ui: ConsoleUI):
        """Handler를 초기화합니다.

        Args:
            commands: CLI 명령어 처리 객체
            ui: 콘솔 UI 객체
        """
        self.commands = commands
        self.ui = ui
        self.logger = logger

    def handle_error(self, operation: str, error: Exception) -> None:
        """에러를 일관되게 처리합니다.

        Args:
            operation: 수행 중이던 작업명
            error: 발생한 예외
        """
        self.logger.exception(f"{operation} 중 오류 발생")
        self.ui.print_error(f"{operation} 중 오류가 발생했습니다")
        self.ui.pause()

    def confirm_operation(self, message: str) -> bool:
        """사용자에게 작업 확인을 요청합니다.

        Args:
            message: 확인 메시지

        Returns:
            사용자 확인 여부
        """
        return self.ui.confirm(message)
