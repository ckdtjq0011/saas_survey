import typer
from pathlib import Path
from rich.console import Console
from loguru import logger
from infrastructure.logging_config import setup_logging
from interface.cli.interactive_cli import InteractiveCLI

app = typer.Typer(
    name="설문조사 시스템",
    help="멀티테넌트 설문조사 플랫폼 CLI",
    add_completion=False
)

console = Console()


@app.command()
def run(
    data_dir: Path = typer.Option(
        Path("data"),
        "--data-dir",
        "-d",
        help="데이터 저장 디렉토리"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="디버그 모드 활성화 (상세 로깅)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="자세한 출력 모드"
    ),
    clear_session: bool = typer.Option(
        False,
        "--clear-session",
        help="저장된 세션 삭제 후 시작"
    ),
):
    """설문조사 시스템을 실행합니다."""

    setup_logging(debug=debug, log_dir=Path("logs"))

    logger.info(f"애플리케이션 시작: data_dir={data_dir}, debug={debug}")

    data_dir.mkdir(parents=True, exist_ok=True)

    if clear_session:
        from interface.cli.session_manager import SessionManager
        SessionManager().clear_session()
        console.print("[green][OK][/green] 세션이 초기화되었습니다.")

    try:
        cli = InteractiveCLI(data_dir, debug=debug, verbose=verbose)
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow][INFO][/yellow] 프로그램이 중단되었습니다.")
    except Exception as e:
        logger.exception("치명적 오류 발생")
        console.print(f"[red][ERROR][/red] 오류 발생: {e}")
        if debug:
            raise


@app.command()
def version():
    """버전 정보를 출력합니다."""
    console.print("[cyan]설문조사 시스템 v1.0.0[/cyan]")
    console.print("Rich 기반 CLI 인터페이스")
    console.print("Loguru 로깅 시스템")


if __name__ == "__main__":
    app()
