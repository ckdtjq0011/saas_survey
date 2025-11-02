from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint
import json


console = Console()


def print_debug_info(title: str, data: Any) -> None:
    """디버그 정보를 출력합니다.

    Args:
        title: 디버그 정보 제목
        data: 출력할 데이터
    """
    console.print(f"\n[dim cyan]DEBUG: {title}[/dim cyan]")

    if isinstance(data, dict):
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
        console.print(syntax)
    else:
        rprint(data)

    console.print("[dim cyan]" + "=" * 60 + "[/dim cyan]")


def print_timing(operation: str, duration_ms: float) -> None:
    """작업 소요 시간을 출력합니다.

    Args:
        operation: 작업명
        duration_ms: 소요 시간 (밀리초)
    """
    color = "green" if duration_ms < 100 else "yellow" if duration_ms < 500 else "red"
    console.print(f"[dim]TIMING: {operation}: [{color}]{duration_ms:.2f}ms[/{color}][/dim]")


def print_api_call(method: str, params: dict) -> None:
    """API 호출 정보를 출력합니다.

    Args:
        method: 메서드명
        params: 파라미터
    """
    console.print(f"\n[dim blue]API CALL: {method}[/dim blue]")
    if params:
        print_debug_info("Parameters", params)
