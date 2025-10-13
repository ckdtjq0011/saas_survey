import shutil
import tempfile
from pathlib import Path
import pytest
from interface.cli.commands import SurveyCommands


@pytest.fixture
def temp_data_dir():
    """테스트용 임시 데이터 디렉토리를 생성합니다.

    Yields:
        임시 디렉토리 Path 객체

    Raises:
        OSError: 디렉토리 생성/삭제 실패 시
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def survey_commands(temp_data_dir):
    """테스트용 SurveyCommands 인스턴스를 생성합니다.

    Args:
        temp_data_dir: 임시 데이터 디렉토리 픽스처

    Returns:
        SurveyCommands 인스턴스
    """
    return SurveyCommands(temp_data_dir)
