from dataclasses import dataclass
from typing import ClassVar
from enum import Enum


class MenuOption(Enum):
    CREATE_SURVEY = "1"
    ADD_QUESTION = "2"
    VIEW_SURVEY = "3"
    LIST_SURVEYS = "4"
    SUBMIT_RESPONSE = "5"
    VIEW_RESULTS = "6"
    EXIT = "0"


@dataclass(frozen=True, slots=True)
class UIConfig:
    LINE_WIDTH: ClassVar[int] = 60
    SEPARATOR: ClassVar[str] = "="


def print_header(title: str) -> None:
    """헤더를 출력합니다.

    Args:
        title: 헤더 제목
    """
    print("\n" + UIConfig.SEPARATOR * UIConfig.LINE_WIDTH)
    print(title.center(UIConfig.LINE_WIDTH))
    print(UIConfig.SEPARATOR * UIConfig.LINE_WIDTH)


def print_section(title: str) -> None:
    """섹션 제목을 출력합니다.

    Args:
        title: 섹션 제목
    """
    print(f"\n{title}")
    print("-" * len(title))


def print_menu() -> None:
    """메인 메뉴를 출력합니다."""
    print_section("메뉴")
    print("1. 설문 생성")
    print("2. 질문 추가")
    print("3. 설문 조회")
    print("4. 설문 목록")
    print("5. 응답 제출")
    print("6. 결과 조회")
    print("0. 종료")
    print()


def get_input(prompt: str) -> str:
    """사용자 입력을 받습니다.

    Args:
        prompt: 입력 프롬프트

    Returns:
        사용자 입력 문자열
    """
    return input(f"{prompt}: ").strip()


def get_multiline_input(prompt: str) -> str:
    """여러 줄 입력을 받습니다.

    Args:
        prompt: 입력 프롬프트

    Returns:
        사용자 입력 문자열
    """
    print(f"{prompt} (종료: 빈 줄 입력)")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    return "\n".join(lines)


def print_success(message: str) -> None:
    """성공 메시지를 출력합니다.

    Args:
        message: 성공 메시지
    """
    print(f"\n[성공] {message}")


def print_error(message: str) -> None:
    """에러 메시지를 출력합니다.

    Args:
        message: 에러 메시지
    """
    print(f"\n[오류] {message}")


def print_info(message: str) -> None:
    """정보 메시지를 출력합니다.

    Args:
        message: 정보 메시지
    """
    print(f"\n[정보] {message}")


def confirm(prompt: str) -> bool:
    """확인을 요청합니다.

    Args:
        prompt: 확인 프롬프트

    Returns:
        True if 확인, False otherwise
    """
    response = get_input(f"{prompt} (y/n)")
    return response.lower() in ("y", "yes")


def pause() -> None:
    """사용자가 엔터를 누를 때까지 대기합니다."""
    input("\n계속하려면 엔터를 누르세요...")
