import logging
from pathlib import Path
from interface.cli.commands import SurveyCommands
from interface.cli.ui_helper import (
    MenuOption,
    print_header,
    print_menu,
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
    """인터랙티브 CLI 애플리케이션 클래스입니다.

    Attributes:
        commands: 설문 명령어 핸들러
    """

    def __init__(self, data_dir: Path):
        """CLI 애플리케이션을 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.commands = SurveyCommands(data_dir)

    def run(self) -> None:
        """CLI 애플리케이션을 실행합니다."""
        print_header("병원 만족도 설문조사 플랫폼")

        while True:
            try:
                print_menu()
                choice = get_input("선택")

                if choice == MenuOption.EXIT.value:
                    print_info("프로그램을 종료합니다")
                    break

                self._handle_menu_choice(choice)

            except KeyboardInterrupt:
                print_info("\n\n프로그램을 종료합니다")
                break
            except Exception:
                logger.exception("예상치 못한 오류가 발생했습니다")
                print_error("예상치 못한 오류가 발생했습니다")
                pause()

    def _handle_menu_choice(self, choice: str) -> None:
        """메뉴 선택을 처리합니다.

        Args:
            choice: 메뉴 선택 번호
        """
        if choice == MenuOption.CREATE_SURVEY.value:
            self._create_survey_flow()
        elif choice == MenuOption.ADD_QUESTION.value:
            self._add_question_flow()
        elif choice == MenuOption.VIEW_SURVEY.value:
            self._view_survey_flow()
        elif choice == MenuOption.LIST_SURVEYS.value:
            self._list_surveys_flow()
        elif choice == MenuOption.SUBMIT_RESPONSE.value:
            self._submit_response_flow()
        elif choice == MenuOption.VIEW_RESULTS.value:
            self._view_results_flow()
        else:
            print_error("잘못된 선택입니다")
            pause()

    def _create_survey_flow(self) -> None:
        """설문 생성 플로우를 실행합니다."""
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

            survey_id = self.commands.create_survey(title, description)
            print_success(f"설문이 생성되었습니다 (ID: {survey_id})")
            pause()

        except Exception:
            logger.exception("설문 생성 중 오류가 발생했습니다")
            print_error("설문 생성 중 오류가 발생했습니다")
            pause()

    def _add_question_flow(self) -> None:
        """질문 추가 플로우를 실행합니다."""
        try:
            print_section("질문 추가")

            surveys = self.commands.list_surveys()
            if not surveys:
                print_error("등록된 설문이 없습니다. 먼저 설문을 생성해주세요")
                pause()
                return

            print("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                print(f"{idx}. [{survey['id']}] {survey['title']}")

            survey_id = get_input("\n설문 ID")
            if not survey_id:
                print_error("설문 ID를 입력해주세요")
                pause()
                return

            text = get_input("질문 내용")
            if not text:
                print_error("질문 내용을 입력해주세요")
                pause()
                return

            print("\n질문 유형:")
            print("1. 텍스트 (text)")
            print("2. 평점 (rating)")
            print("3. 객관식 (choice)")

            q_type_choice = get_input("유형 선택")
            question_type_map = {
                "1": "text",
                "2": "rating",
                "3": "choice",
            }

            question_type = question_type_map.get(q_type_choice)
            if not question_type:
                print_error("잘못된 유형입니다. 1, 2, 3 중 하나를 선택해주세요")
                pause()
                return

            options = None
            if question_type == "choice":
                options_input = get_input("선택지 (|로 구분, 예: 선택1|선택2|선택3)")
                if not options_input:
                    print_error("선택지를 입력해주세요")
                    pause()
                    return
                options = [opt.strip() for opt in options_input.split("|") if opt.strip()]
                if len(options) < 2:
                    print_error("선택지는 최소 2개 이상이어야 합니다")
                    pause()
                    return

            question_id = self.commands.add_question(survey_id, text, question_type, options)
            print_success(f"질문이 추가되었습니다 (ID: {question_id})")
            pause()

        except ValueError as e:
            logger.exception("질문 추가 중 오류가 발생했습니다")
            print_error(f"질문 추가 실패: {str(e)}")
            pause()
        except Exception:
            logger.exception("질문 추가 중 오류가 발생했습니다")
            print_error("질문 추가 중 예상치 못한 오류가 발생했습니다")
            pause()

    def _view_survey_flow(self) -> None:
        """설문 조회 플로우를 실행합니다."""
        try:
            print_section("설문 조회")

            surveys = self.commands.list_surveys()
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            print("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                print(f"{idx}. [{survey['id']}] {survey['title']}")

            survey_id = get_input("\n설문 ID")
            if not survey_id:
                print_error("설문 ID를 입력해주세요")
                pause()
                return

            survey_data = self.commands.get_survey(survey_id)

            print(f"\n제목: {survey_data['title']}")
            print(f"설명: {survey_data['description']}")
            print(f"생성일: {survey_data['created_at']}")
            print(f"\n질문 목록 (총 {len(survey_data['questions'])}개):")

            for idx, question in enumerate(survey_data['questions'], 1):
                print(f"\n[{idx}] {question['text']}")
                print(f"    ID: {question['id']}")
                print(f"    유형: {question['type']}")
                if question['options']:
                    print(f"    선택지: {', '.join(question['options'])}")

            pause()

        except ValueError as e:
            logger.exception("설문 조회 중 오류가 발생했습니다")
            print_error(f"설문 조회 실패: {str(e)}")
            pause()
        except Exception:
            logger.exception("설문 조회 중 오류가 발생했습니다")
            print_error("설문 조회 중 예상치 못한 오류가 발생했습니다")
            pause()

    def _list_surveys_flow(self) -> None:
        """설문 목록 조회 플로우를 실행합니다."""
        try:
            print_section("설문 목록")

            surveys = self.commands.list_surveys()

            if not surveys:
                print_info("등록된 설문이 없습니다")
            else:
                print(f"\n총 {len(surveys)}개의 설문:")
                for idx, survey in enumerate(surveys, 1):
                    print(f"\n[{idx}] {survey['title']}")
                    print(f"    ID: {survey['id']}")
                    print(f"    설명: {survey['description']}")
                    print(f"    질문 수: {survey['question_count']}개")

            pause()

        except Exception:
            logger.exception("설문 목록 조회 중 오류가 발생했습니다")
            print_error("설문 목록 조회 중 오류가 발생했습니다")
            pause()

    def _submit_response_flow(self) -> None:
        """응답 제출 플로우를 실행합니다."""
        try:
            print_section("응답 제출")

            surveys = self.commands.list_surveys()
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            print("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                print(f"{idx}. [{survey['id']}] {survey['title']}")

            survey_id = get_input("\n설문 ID")
            if not survey_id:
                print_error("설문 ID를 입력해주세요")
                pause()
                return

            survey_data = self.commands.get_survey(survey_id)
            print(f"\n설문: {survey_data['title']}")

            if not survey_data['questions']:
                print_error("이 설문에는 질문이 없습니다. 먼저 질문을 추가해주세요")
                pause()
                return

            respondent_id = get_input("응답자 ID")
            if not respondent_id:
                print_error("응답자 ID를 입력해주세요")
                pause()
                return

            answers = {}
            print("\n각 질문에 답변해주세요:")

            for idx, question in enumerate(survey_data['questions'], 1):
                print(f"\n[{idx}] {question['text']}")
                print(f"    유형: {question['type']}")

                if question['type'] == 'choice':
                    print(f"    선택지: {', '.join(question['options'])}")
                elif question['type'] == 'rating':
                    print("    1-5 사이의 숫자를 입력하세요")

                answer = get_input("답변")
                if not answer:
                    print_error("답변을 입력해주세요")
                    pause()
                    return

                answers[question['id']] = answer

            if confirm("응답을 제출하시겠습니까?"):
                self.commands.submit_response(survey_id, respondent_id, answers)
                print_success("응답이 제출되었습니다")
            else:
                print_info("응답 제출이 취소되었습니다")

            pause()

        except ValueError as e:
            logger.exception("응답 제출 중 오류가 발생했습니다")
            print_error(f"응답 제출 실패: {str(e)}")
            pause()
        except Exception:
            logger.exception("응답 제출 중 오류가 발생했습니다")
            print_error("응답 제출 중 예상치 못한 오류가 발생했습니다")
            pause()

    def _view_results_flow(self) -> None:
        """결과 조회 플로우를 실행합니다."""
        try:
            print_section("결과 조회")

            surveys = self.commands.list_surveys()
            if not surveys:
                print_error("등록된 설문이 없습니다")
                pause()
                return

            print("\n사용 가능한 설문:")
            for idx, survey in enumerate(surveys, 1):
                print(f"{idx}. [{survey['id']}] {survey['title']}")

            survey_id = get_input("\n설문 ID")
            if not survey_id:
                print_error("설문 ID를 입력해주세요")
                pause()
                return

            results = self.commands.get_results(survey_id)

            if not results:
                print_info("아직 응답이 없습니다")
                pause()
                return

            print("\n설문 결과:")
            for question_id, stats in results.items():
                print(f"\n질문 ID: {question_id}")
                print(f"총 응답 수: {stats['total_responses']}개")

                if 'average_rating' in stats:
                    print(f"평균 평점: {stats['average_rating']:.2f}")

                if 'distribution' in stats:
                    print("응답 분포:")
                    for answer, count in stats['distribution'].items():
                        print(f"  {answer}: {count}개")

                if 'text_responses' in stats:
                    print("텍스트 응답:")
                    for text in stats['text_responses']:
                        print(f"  - {text}")

            pause()

        except ValueError as e:
            logger.exception("결과 조회 중 오류가 발생했습니다")
            print_error(f"결과 조회 실패: {str(e)}")
            pause()
        except Exception:
            logger.exception("결과 조회 중 오류가 발생했습니다")
            print_error("결과 조회 중 예상치 못한 오류가 발생했습니다")
            pause()
