import platform
import time
from datetime import datetime
from domain.entities.user import User
from domain.value_objects.types import QuestionType
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

            user_agent = f"{platform.system()} {platform.release()} - Python CLI"

            success_session, session_id = self.commands.start_survey_session(user, survey_id, user_agent)
            if not success_session:
                self.ui.print_error(f"세션 시작 실패: {session_id}")
                return

            session_start_time = time.time()

            success, error, survey_data = self.commands.get_survey(user, survey_id)
            if not success or not survey_data:
                self.ui.print_error(f"설문 조회 실패: {error}")
                return

            self.ui.print_info(f"설문: {survey_data['title']}")
            self.ui.print_info(f"설명: {survey_data['description']}")
            self.ui.print_info("")

            answers, time_spent_data = self._collect_answers_with_timing(survey_data["questions"])
            if not answers:
                self.ui.print_warning("응답이 취소되었습니다")
                return

            if self.confirm_operation("응답을 제출하시겠습니까?"):
                total_time_seconds = int(time.time() - session_start_time)

                success, error = self.commands.submit_response(
                    user, survey_id, answers, session_id, time_spent_data
                )

                if success:
                    self.commands.complete_survey_session(session_id, total_time_seconds)
                    self.ui.print_success(f"응답이 제출되었습니다 (소요 시간: {total_time_seconds}초)")
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

    def update_response_flow(self, user: User) -> None:
        """응답 수정 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("응답 수정")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            response_id, response_data = self._select_response(user, survey_id)
            if not response_id:
                return

            self.ui.print_info(f"현재 답변: {response_data['answer']}")
            self.ui.print_info("")

            answer = self.ui.get_input("새 답변")

            if self.confirm_operation("응답을 수정하시겠습니까?"):
                success, error = self.commands.update_response(user, response_id, answer)
                if success:
                    self.ui.print_success("응답이 수정되었습니다")
                else:
                    self.ui.print_error(f"응답 수정 실패: {error}")

        except Exception as e:
            self.handle_error("응답 수정", e)
        finally:
            self.ui.pause()

    def delete_response_flow(self, user: User) -> None:
        """응답 삭제 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("응답 삭제")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            response_id, response_data = self._select_response(user, survey_id)
            if not response_id:
                return

            self.ui.print_warning(f"질문: {response_data['question_text']}")
            self.ui.print_warning(f"답변: {response_data['answer']}")
            self.ui.print_info("")

            if self.confirm_operation("정말로 응답을 삭제하시겠습니까?"):
                success, error = self.commands.delete_response(user, response_id)
                if success:
                    self.ui.print_success("응답이 삭제되었습니다")
                else:
                    self.ui.print_error(f"응답 삭제 실패: {error}")

        except Exception as e:
            self.handle_error("응답 삭제", e)
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

    def _select_response(self, user: User, survey_id: str) -> tuple[str | None, dict | None]:
        """응답을 선택합니다.

        Args:
            user: 현재 로그인한 사용자
            survey_id: 설문 ID

        Returns:
            (선택된 응답 ID, 응답 데이터) 튜플, 취소 시 (None, None)
        """
        success, error, survey_data = self.commands.get_survey(user, survey_id)
        if not success or not survey_data:
            self.ui.print_error(f"설문 조회 실패: {error}")
            return None, None

        user_responses = []
        for question in survey_data["questions"]:
            q_id = question["id"]
            q_text = question["text"]

            responses = self.commands.response_service.response_repository.find_by_question_id(q_id)
            for response in responses:
                if response.respondent_id == user.id:
                    user_responses.append({
                        "id": response.id,
                        "question_text": q_text,
                        "answer": response.answer,
                    })

        if not user_responses:
            self.ui.print_info("제출한 응답이 없습니다")
            return None, None

        self.ui.print_info("제출한 응답 목록:")
        for idx, resp in enumerate(user_responses, 1):
            self.ui.print_info(f"{idx}. {resp['question_text']}: {resp['answer']}")

        try:
            choice = self.ui.get_int_input("응답 번호", default=1)
            if 1 <= choice <= len(user_responses):
                return user_responses[choice - 1]["id"], user_responses[choice - 1]
            else:
                self.ui.print_error("잘못된 선택입니다")
                return None, None
        except (ValueError, IndexError):
            self.ui.print_error("잘못된 입력입니다")
            return None, None

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

            if q_type == QuestionType.TEXT.value:
                answer = self.ui.get_input("답변")
                answers[q_id] = answer

            elif q_type == QuestionType.MULTIPLE_CHOICE.value:
                if q_options:
                    for opt_idx, opt in enumerate(q_options, 1):
                        self.ui.print_info(f"  {opt_idx}. {opt}")
                    choice = self.ui.get_int_input("선택", default=1)
                    if 1 <= choice <= len(q_options):
                        answers[q_id] = q_options[choice - 1]
                    else:
                        self.ui.print_warning("잘못된 선택입니다")
                        return None

            elif q_type == QuestionType.RATING.value:
                self.ui.print_info("  평점: 1-5")
                answer = self.ui.get_validated_input("평점", validate_rating_answer)
                answers[q_id] = answer

        return answers

    def _collect_answers_with_timing(self, questions: list[dict]) -> tuple[dict[str, str], dict[str, int]] | tuple[None, None]:
        """질문에 대한 답변을 수집하며 각 질문별 소요 시간을 측정합니다.

        Args:
            questions: 질문 리스트

        Returns:
            (질문 ID와 답변 딕셔너리, 질문 ID와 소요 시간 딕셔너리), 취소 시 (None, None)
        """
        answers = {}
        time_spent_data = {}
        total_questions = len(questions)

        for idx, question in enumerate(questions, 1):
            q_id = question["id"]
            q_text = question["text"]
            q_type = question["type"]
            q_options = question.get("options", [])

            progress = int((idx - 1) / total_questions * 100)
            self.ui.print_info(f"\n진행률: {progress}% ({idx-1}/{total_questions})")
            self.ui.print_info(f"[Q{idx}] {q_text}")

            question_start_time = time.time()

            if q_type == QuestionType.TEXT.value:
                answer = self.ui.get_input("답변")
                answers[q_id] = answer

            elif q_type == QuestionType.MULTIPLE_CHOICE.value:
                if q_options:
                    for opt_idx, opt in enumerate(q_options, 1):
                        self.ui.print_info(f"  {opt_idx}. {opt}")
                    choice = self.ui.get_int_input("선택", default=1)
                    if 1 <= choice <= len(q_options):
                        answers[q_id] = q_options[choice - 1]
                    else:
                        self.ui.print_warning("잘못된 선택입니다")
                        return None, None

            elif q_type == QuestionType.RATING.value:
                self.ui.print_info("  평점: 1-5")
                answer = self.ui.get_validated_input("평점", validate_rating_answer)
                answers[q_id] = answer

            question_end_time = time.time()
            time_spent_seconds = int(question_end_time - question_start_time)
            time_spent_data[q_id] = time_spent_seconds

        self.ui.print_info(f"\n진행률: 100% ({total_questions}/{total_questions})")
        return answers, time_spent_data

    def export_results_flow(self, user: User) -> None:
        """설문 결과를 CSV로 내보내는 플로우를 실행합니다.

        Args:
            user: 현재 로그인한 사용자
        """
        try:
            self.ui.print_section("설문 결과 CSV 내보내기")

            survey_id = self._select_survey(user)
            if not survey_id:
                return

            success, error, results_data = self.commands.get_survey(user, survey_id)
            if not success or not results_data:
                self.ui.print_error(f"설문 조회 실패: {error}")
                return

            self.ui.print_info(f"설문: {results_data['title']}")
            self.ui.print_info("")

            if self.confirm_operation("설문 결과를 CSV 파일로 내보내시겠습니까?"):
                success, error, file_paths = self.commands.export_results(user, survey_id)

                if success and file_paths:
                    raw_path, summary_path = file_paths
                    self.ui.print_success("설문 결과가 CSV 파일로 내보내졌습니다")
                    self.ui.print_info("")
                    self.ui.print_info(f"Raw Data CSV: {raw_path}")
                    self.ui.print_info(f"Summary CSV: {summary_path}")
                else:
                    self.ui.print_error(f"결과 내보내기 실패: {error}")

        except Exception as e:
            self.handle_error("결과 내보내기", e)
        finally:
            self.ui.pause()
