from domain.entities.user import User
from interface.cli.handlers.base_handler import BaseHandler
from interface.cli.validators import validate_rating_answer


class ResponseHandler(BaseHandler):
    """응답 관리를 처리하는 Handler입니다."""

    def submit_response_flow(self, user: User) -> None:
        """응답 제출 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("응답 제출")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, survey_data = self.commands.get_survey(user, survey_id)
            if not success or not survey_data:
                self.ui.print_error(f"설문 조회 실패: {error}")
                return

            self.ui.print_info(f"설문: {survey_data['title']}")
            self.ui.print_info(f"설명: {survey_data['description']}")
            self.ui.print_info("")

            answers = self._collect_answers(survey_data["questions"])
            if not answers:
                self.ui.print_warning("응답이 취소되었습니다")
                return

            if self.confirm_operation("응답을 제출하시겠습니까?"):
                success, error = self.commands.submit_response(user, survey_id, answers)
                if success:
                    self.ui.print_success("응답이 제출되었습니다")
                else:
                    self.ui.print_error(f"응답 제출 실패: {error}")

        except Exception as e:
            self.handle_error("응답 제출", e)
        finally:
            self.ui.pause()

    def view_results_flow(self, user: User) -> None:
        """설문 결과 조회 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 결과 조회")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, results = self.commands.get_results(user, survey_id)

            if success and results:
                formatted_results = [
                    {
                        "question": r["question"],
                        "answer_distribution": r["answer_distribution"],
                    }
                    for r in results["results"]
                ]
                self.ui.print_results_table(formatted_results)
            else:
                self.ui.print_error(f"결과 조회 실패: {error}")

        except Exception as e:
            self.handle_error("결과 조회", e)
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

    def _collect_answers(self, questions: list[dict]) -> dict[str, str] | None:
        """질문에 대한 답변을 수집합니다.

        Args:
            questions: 질문 리스트

        Returns:
            질문 ID와 답변 딕셔너리, 취소 시 None
        """
        answers = {}

        for idx, question in enumerate(questions, 1):
            q_id = question["id"]
            q_text = question["text"]
            q_type = question["type"]
            q_options = question.get("options", [])

            self.ui.print_info(f"\n[Q{idx}] {q_text}")

            if q_type == "TEXT":
                answer = self.ui.get_input("답변")
                answers[q_id] = answer

            elif q_type == "MULTIPLE_CHOICE":
                if q_options:
                    for opt_idx, opt in enumerate(q_options, 1):
                        self.ui.print_info(f"  {opt_idx}. {opt}")
                    choice = self.ui.get_int_input("선택", default=1)
                    if 1 <= choice <= len(q_options):
                        answers[q_id] = q_options[choice - 1]
                    else:
                        self.ui.print_warning("잘못된 선택입니다")
                        return None

            elif q_type == "RATING":
                self.ui.print_info("  평점: 1-5")
                answer = self.ui.get_validated_input("평점", validate_rating_answer)
                answers[q_id] = answer

        return answers
