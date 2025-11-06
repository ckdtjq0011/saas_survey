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
            elif question_type == QuestionType.MULTI_SELECT.value:
                self.ui.print_info("다중 선택 질문의 선택지를 입력하세요")
                options = self._get_multiple_choice_options()

            category_id = None
            category_choice = self.ui.get_choice(
                "범주를 설정하시겠습니까?",
                choices=["y", "n"],
            )
            if category_choice == "y":
                category_id = self._select_category(user)

            is_required = True
            required_choice = self.ui.get_choice(
                "필수 응답 질문으로 설정하시겠습니까?",
                choices=["y", "n"],
            )
            if required_choice == "n":
                is_required = False

            success, result = self.commands.add_question(
                user, survey_id, text, question_type, options, category_id, is_required
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

    def update_survey_flow(self, user: User) -> None:
        """설문 수정 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 수정")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, survey_data = self.commands.get_survey(user, survey_id)
            if not success or not survey_data:
                self.ui.print_error(f"설문 조회 실패: {error}")
                return

            self.ui.print_info(f"현재 제목: {survey_data['title']}")
            self.ui.print_info(f"현재 설명: {survey_data['description']}")
            self.ui.print_info("")

            title = self.ui.get_validated_input(
                "새 제목 (3-100자)", validate_survey_title
            )
            description = self.ui.get_input("새 설명")

            if self.confirm_operation("설문을 수정하시겠습니까?"):
                success, error = self.commands.update_survey(user, survey_id, title, description)
                if success:
                    self.ui.print_success("설문이 수정되었습니다")
                else:
                    self.ui.print_error(f"설문 수정 실패: {error}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("설문 수정", e)
        finally:
            self.ui.pause()

    def delete_survey_flow(self, user: User) -> None:
        """설문 삭제 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 삭제")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, survey_data = self.commands.get_survey(user, survey_id)
            if not success or not survey_data:
                self.ui.print_error(f"설문 조회 실패: {error}")
                return

            self.ui.print_warning(f"설문: {survey_data['title']}")
            self.ui.print_warning(f"질문 수: {len(survey_data['questions'])}")
            self.ui.print_warning("이 설문과 관련된 모든 응답도 함께 삭제됩니다")
            self.ui.print_info("")

            if self.confirm_operation("정말로 설문을 삭제하시겠습니까?"):
                success, error = self.commands.delete_survey(user, survey_id)
                if success:
                    self.ui.print_success("설문이 삭제되었습니다")
                else:
                    self.ui.print_error(f"설문 삭제 실패: {error}")

        except Exception as e:
            self.handle_error("설문 삭제", e)
        finally:
            self.ui.pause()

    def update_question_flow(self, user: User) -> None:
        """질문 수정 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("질문 수정")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            question_id, question_data = self._select_question(user, survey_id)
            if not question_id:
                return

            self.ui.print_info(f"현재 질문: {question_data['text']}")
            self.ui.print_info(f"현재 유형: {question_data['type']}")
            if question_data.get("options"):
                self.ui.print_info(f"현재 선택지: {', '.join(question_data['options'])}")
            self.ui.print_info("")

            text = self.ui.get_validated_input(
                "새 질문 내용 (5-500자)", validate_question_text
            )

            options = None
            if question_data["type"] == QuestionType.MULTIPLE_CHOICE.value:
                if self.confirm_operation("선택지도 수정하시겠습니까?"):
                    options = self._get_multiple_choice_options()

            if self.confirm_operation("질문을 수정하시겠습니까?"):
                success, error = self.commands.update_question(user, question_id, text, options)
                if success:
                    self.ui.print_success("질문이 수정되었습니다")
                else:
                    self.ui.print_error(f"질문 수정 실패: {error}")

        except ValueError as e:
            self.ui.print_error(str(e))
        except Exception as e:
            self.handle_error("질문 수정", e)
        finally:
            self.ui.pause()

    def delete_question_flow(self, user: User) -> None:
        """질문 삭제 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("질문 삭제")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            question_id, question_data = self._select_question(user, survey_id)
            if not question_id:
                return

            self.ui.print_warning(f"질문: {question_data['text']}")
            self.ui.print_warning("이 질문과 관련된 모든 응답도 함께 삭제됩니다")
            self.ui.print_info("")

            if self.confirm_operation("정말로 질문을 삭제하시겠습니까?"):
                success, error = self.commands.delete_question(user, question_id)
                if success:
                    self.ui.print_success("질문이 삭제되었습니다")
                else:
                    self.ui.print_error(f"질문 삭제 실패: {error}")

        except Exception as e:
            self.handle_error("질문 삭제", e)
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

    def _select_question(self, user: User, survey_id: str) -> tuple[str | None, dict | None]:
        """질문을 선택합니다.

        Args:
            user: 현재 로그인한 사용자
            survey_id: 설문 ID

        Returns:
            (선택된 질문 ID, 질문 데이터) 튜플, 취소 시 (None, None)
        """
        success, error, survey_data = self.commands.get_survey(user, survey_id)
        if not success or not survey_data:
            self.ui.print_error(f"설문 조회 실패: {error}")
            return None, None

        questions = survey_data["questions"]
        if not questions:
            self.ui.print_info("질문이 없습니다")
            return None, None

        questions_display = [
            {
                "text": q["text"],
                "question_type": q["type"],
                "options": q["options"],
            }
            for q in questions
        ]
        self.ui.print_questions_tree(survey_data["title"], questions_display)

        try:
            choice = self.ui.get_int_input("질문 번호", default=1)
            if 1 <= choice <= len(questions):
                return questions[choice - 1]["id"], questions[choice - 1]
            else:
                self.ui.print_error("잘못된 선택입니다")
                return None, None
        except (ValueError, IndexError):
            self.ui.print_error("잘못된 입력입니다")
            return None, None

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

    def _select_category(self, user: User) -> str | None:
        """범주를 선택합니다.

        Args:
            user: 현재 로그인한 사용자

        Returns:
            선택된 범주 ID, 취소 시 None
        """
        success, result = self.commands.list_all_categories(user)

        if not success:
            self.ui.print_error(f"범주 목록 조회 실패: {result}")
            return None

        categories = result

        if not categories:
            self.ui.print_info("범주가 없습니다")
            return None

        choices = []
        for cat in categories:
            if cat.is_top_level():
                choices.append(f"[대범주] {cat.name}")
            else:
                choices.append(f"  [하위범주] {cat.name}")

        selected_choice = self.ui.get_choice("범주 선택", choices=choices + ["선택 안 함"])

        if selected_choice == "선택 안 함":
            return None

        for cat in categories:
            if f"[대범주] {cat.name}" == selected_choice or f"  [하위범주] {cat.name}" == selected_choice:
                return cat.id

        return None
