from domain.entities.user import User
from domain.value_objects.types import QuestionType
from interface.cli.handlers.base_handler import BaseHandler
from interface.cli.validators import validate_survey_title, validate_question_text


class SurveyHandler(BaseHandler):
    """설문 관리를 처리하는 Handler입니다."""

    def create_survey_flow(self, user: User) -> None:
        """설문 생성 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 생성")

            title = self.ui.get_validated_input(
                "설문 제목 (3-100자)", validate_survey_title
            )
            description = self.ui.get_input("설문 설명")

            success, result = self.commands.create_survey(user, title, description)

            if success:
                self.ui.print_success(f"설문이 생성되었습니다. ID: {result}")
            else:
                self.ui.print_error(f"설문 생성 실패: {result}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("설문 생성", e)
        finally:
            self.ui.pause()

    def add_question_flow(self, user: User) -> None:
        """질문 추가 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("질문 추가")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            text = self.ui.get_validated_input(
                "질문 내용 (5-500자)", validate_question_text
            )

            question_type = self.ui.get_choice(
                "질문 유형",
                choices=QuestionType.get_choices_for_ui(),
            )

            options = None
            if question_type == QuestionType.MULTIPLE_CHOICE.value:
                options = self._get_multiple_choice_options()

            success, result = self.commands.add_question(
                user, survey_id, text, question_type, options
            )

            if success:
                self.ui.print_success(f"질문이 추가되었습니다. ID: {result}")
            else:
                self.ui.print_error(f"질문 추가 실패: {result}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("질문 추가", e)
        finally:
            self.ui.pause()

    def list_surveys_flow(self, user: User) -> None:
        """설문 목록 조회 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 목록")

            surveys = self.commands.list_surveys(user)

            if surveys:
                self.ui.print_surveys_table(surveys)
            else:
                self.ui.print_info("설문이 없습니다")

        except Exception as e:
            self.handle_error("설문 목록 조회", e)
        finally:
            self.ui.pause()

    def view_survey_flow(self, user: User) -> None:
        """설문 상세 조회 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 조회")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, survey_data = self.commands.get_survey(user, survey_id)

            if success and survey_data:
                questions = [
                    {
                        "text": q["text"],
                        "question_type": q["type"],
                        "options": q["options"],
                    }
                    for q in survey_data["questions"]
                ]
                self.ui.print_questions_tree(survey_data["title"], questions)
            else:
                self.ui.print_error(f"설문 조회 실패: {error}")

        except Exception as e:
            self.handle_error("설문 조회", e)
        finally:
            self.ui.pause()

    def _select_survey(self, user: User) -> str | None:
        """설문을 선택합니다.

        Args:
            user: 현재 로그인한 사용자

        Returns:
            선택된 설문 ID, 취소 시 None
        """
        surveys = self.commands.list_surveys(user)

        if not surveys:
            self.ui.print_info("설문이 없습니다")
            return None

        self.ui.print_surveys_table(surveys)

        try:
            choice = self.ui.get_int_input("설문 번호", default=1)
            if 1 <= choice <= len(surveys):
                return surveys[choice - 1]["id"]
            else:
                self.ui.print_error("잘못된 선택입니다")
                return None
        except (ValueError, IndexError):
            self.ui.print_error("잘못된 입력입니다")
            return None

    def _get_multiple_choice_options(self) -> list[str]:
        """객관식 선택지를 입력받습니다.

        Returns:
            선택지 리스트
        """
        self.ui.print_info("선택지를 입력하세요 (빈 줄 입력 시 종료)")
        options = []
        idx = 1

        while True:
            option = self.ui.get_input(f"선택지 {idx}")
            if not option:
                break
            options.append(option)
            idx += 1

        return options
