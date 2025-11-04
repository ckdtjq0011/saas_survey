import pytest
from io import StringIO
from datetime import datetime
from interface.cli.ui_helper import (
    ConsoleUI,
    get_ui,
    set_ui,
    print_header,
    print_section,
    print_success,
    print_error,
    print_info,
    get_input,
    confirm,
    pause,
)


@pytest.fixture
def output_stream():
    """출력 스트림 픽스처"""
    return StringIO()


@pytest.fixture
def input_stream():
    """입력 스트림 픽스처"""
    return StringIO()


@pytest.fixture
def console_ui(output_stream, input_stream):
    """ConsoleUI 픽스처"""
    return ConsoleUI(output_stream=output_stream, input_stream=input_stream)


class TestConsoleUIBasicOutput:
    """기본 출력 메서드 테스트"""

    def test_print_header(self, console_ui, output_stream):
        """헤더 출력 테스트"""
        console_ui.print_header("테스트 헤더")

        output = output_stream.getvalue()
        assert "테스트 헤더" in output

    def test_print_section(self, console_ui, output_stream):
        """섹션 출력 테스트"""
        console_ui.print_section("테스트 섹션")

        output = output_stream.getvalue()
        assert "테스트 섹션" in output

    def test_print_success(self, console_ui, output_stream):
        """성공 메시지 출력 테스트"""
        console_ui.print_success("성공했습니다")

        output = output_stream.getvalue()
        assert "성공했습니다" in output

    def test_print_error(self, console_ui, output_stream):
        """에러 메시지 출력 테스트"""
        console_ui.print_error("에러 발생")

        output = output_stream.getvalue()
        assert "에러 발생" in output

    def test_print_info(self, console_ui, output_stream):
        """정보 메시지 출력 테스트"""
        console_ui.print_info("정보입니다")

        output = output_stream.getvalue()
        assert "정보입니다" in output

    def test_print_warning(self, console_ui, output_stream):
        """경고 메시지 출력 테스트"""
        console_ui.print_warning("경고입니다")

        output = output_stream.getvalue()
        assert "경고입니다" in output


class TestConsoleUITableOutput:
    """테이블 출력 메서드 테스트"""

    def test_print_surveys_table_with_data(self, console_ui, output_stream):
        """설문 테이블 출력 - 데이터 있음"""
        surveys = [
            {
                "id": "survey1",
                "title": "설문1",
                "owner": "소유자1",
                "question_count": 5,
                "created_at": datetime(2025, 1, 1, 12, 0, 0)
            }
        ]

        console_ui.print_surveys_table(surveys)

        output = output_stream.getvalue()
        assert "설문1" in output
        assert "소유자1" in output

    def test_print_surveys_table_empty(self, console_ui, output_stream):
        """설문 테이블 출력 - 데이터 없음"""
        console_ui.print_surveys_table([])

        output = output_stream.getvalue()
        assert "설문이 없습니다" in output

    def test_print_questions_tree(self, console_ui, output_stream):
        """질문 트리 출력"""
        questions = [
            {
                "text": "질문1",
                "question_type": "text",
                "options": None
            },
            {
                "text": "질문2",
                "question_type": "multiple_choice",
                "options": ["옵션1", "옵션2"]
            }
        ]

        console_ui.print_questions_tree("테스트 설문", questions)

        output = output_stream.getvalue()
        assert "테스트 설문" in output
        assert "질문1" in output
        assert "질문2" in output

    def test_print_results_table(self, console_ui, output_stream):
        """결과 테이블 출력"""
        results = [
            {
                "question": "질문1",
                "answer_distribution": {"답변1": 5, "답변2": 3}
            }
        ]

        console_ui.print_results_table(results)

        output = output_stream.getvalue()
        assert "질문1" in output

    def test_print_tenants_table_with_data(self, console_ui, output_stream):
        """테넌트 테이블 출력 - 데이터 있음"""
        tenants = [
            {
                "id": "tenant1",
                "name": "회사1",
                "created_at": datetime(2025, 1, 1),
                "is_active": True
            }
        ]

        console_ui.print_tenants_table(tenants)

        output = output_stream.getvalue()
        assert "회사1" in output

    def test_print_tenants_table_empty(self, console_ui, output_stream):
        """테넌트 테이블 출력 - 데이터 없음"""
        console_ui.print_tenants_table([])

        output = output_stream.getvalue()
        assert "테넌트가 없습니다" in output


class TestConsoleUIInput:
    """입력 메서드 테스트"""

    def test_get_input(self, console_ui, input_stream):
        """문자열 입력"""
        input_stream.write("테스트 입력\n")
        input_stream.seek(0)

        result = console_ui.get_input("입력하세요")

        assert result == "테스트 입력"

    def test_get_int_input(self, console_ui, input_stream):
        """정수 입력"""
        input_stream.write("123\n")
        input_stream.seek(0)

        result = console_ui.get_int_input("숫자 입력")

        assert result == 123

    def test_get_choice(self, console_ui, input_stream):
        """선택 입력"""
        input_stream.write("option1\n")
        input_stream.seek(0)

        result = console_ui.get_choice("선택하세요", ["option1", "option2"])

        assert result == "option1"

    def test_get_choice_case_insensitive_uppercase(self, console_ui, input_stream):
        """선택 입력 - 대문자 입력"""
        input_stream.write("Y\n")
        input_stream.seek(0)

        result = console_ui.get_choice("선택하세요", ["y", "n"])

        assert result == "y"

    def test_get_choice_case_insensitive_lowercase(self, console_ui, input_stream):
        """선택 입력 - 소문자 입력"""
        input_stream.write("n\n")
        input_stream.seek(0)

        result = console_ui.get_choice("선택하세요", ["y", "n"])

        assert result == "n"

    def test_get_choice_case_insensitive_mixed(self, console_ui, input_stream):
        """선택 입력 - 대소문자 혼합"""
        input_stream.write("N\n")
        input_stream.seek(0)

        result = console_ui.get_choice("선택하세요", ["y", "n"])

        assert result == "n"

    def test_confirm_yes(self, console_ui, input_stream):
        """확인 입력 - yes"""
        input_stream.write("y\n")
        input_stream.seek(0)

        result = console_ui.confirm("확인하시겠습니까?")

        assert result is True

    def test_confirm_no(self, console_ui, input_stream):
        """확인 입력 - no"""
        input_stream.write("n\n")
        input_stream.seek(0)

        result = console_ui.confirm("확인하시겠습니까?")

        assert result is False

    def test_pause(self, console_ui, input_stream):
        """일시정지"""
        input_stream.write("\n")
        input_stream.seek(0)

        console_ui.pause()


class TestConsoleUIValidatedInput:
    """검증된 입력 테스트"""

    def test_get_validated_input_success(self, console_ui, input_stream):
        """검증 성공

        시나리오:
            1. 유효한 입력 제공
            2. 검증 통과
            3. 입력값 반환
        """
        input_stream.write("valid@example.com\n")
        input_stream.seek(0)

        def email_validator(value):
            if "@" in value:
                return True, ""
            return False, "유효하지 않은 이메일"

        result = console_ui.get_validated_input("이메일 입력", email_validator)

        assert result == "valid@example.com"

    def test_get_validated_input_max_attempts(self, console_ui, input_stream, output_stream):
        """최대 시도 횟수 초과

        시나리오:
            1. 잘못된 입력 3회
            2. ValueError 발생
        """
        input_stream.write("invalid\ninvalid\ninvalid\n")
        input_stream.seek(0)

        def email_validator(value):
            return False, "유효하지 않은 이메일"

        with pytest.raises(ValueError, match="3회 시도 실패"):
            console_ui.get_validated_input("이메일 입력", email_validator)


class TestConsoleUIHelperFunctions:
    """전역 헬퍼 함수 테스트"""

    def test_get_ui_singleton(self):
        """get_ui 싱글톤 패턴

        시나리오:
            1. get_ui 호출
            2. 동일한 인스턴스 반환 확인
        """
        ui1 = get_ui()
        ui2 = get_ui()

        assert ui1 is ui2

    def test_set_ui_changes_default(self):
        """set_ui로 기본 UI 변경

        시나리오:
            1. 커스텀 UI 생성
            2. set_ui로 설정
            3. get_ui로 확인
        """
        custom_ui = ConsoleUI(output_stream=StringIO())
        set_ui(custom_ui)

        assert get_ui() is custom_ui

    def test_backward_compatibility_print_header(self):
        """하위 호환성 - print_header"""
        output_stream = StringIO()
        ui = ConsoleUI(output_stream=output_stream)
        set_ui(ui)

        print_header("테스트")

        assert "테스트" in output_stream.getvalue()

    def test_backward_compatibility_print_section(self):
        """하위 호환성 - print_section"""
        output_stream = StringIO()
        ui = ConsoleUI(output_stream=output_stream)
        set_ui(ui)

        print_section("테스트")

        assert "테스트" in output_stream.getvalue()

    def test_backward_compatibility_print_success(self):
        """하위 호환성 - print_success"""
        output_stream = StringIO()
        ui = ConsoleUI(output_stream=output_stream)
        set_ui(ui)

        print_success("성공")

        assert "성공" in output_stream.getvalue()

    def test_backward_compatibility_print_error(self):
        """하위 호환성 - print_error"""
        output_stream = StringIO()
        ui = ConsoleUI(output_stream=output_stream)
        set_ui(ui)

        print_error("에러")

        assert "에러" in output_stream.getvalue()

    def test_backward_compatibility_print_info(self):
        """하위 호환성 - print_info"""
        output_stream = StringIO()
        ui = ConsoleUI(output_stream=output_stream)
        set_ui(ui)

        print_info("정보")

        assert "정보" in output_stream.getvalue()
