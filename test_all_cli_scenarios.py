"""모든 CLI 시나리오를 테스트하는 통합 테스트 모듈입니다."""

import logging
from pathlib import Path
from interface.cli.commands import SurveyCommands


def setup_test_logging() -> None:
    """테스트용 로깅을 설정합니다. 기존 로그 파일을 지우고 새로 작성합니다."""
    log_file = Path("test_scenarios.log")

    if log_file.exists():
        log_file.unlink()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True
    )


logger = logging.getLogger(__name__)


class TestScenarioRunner:
    """CLI 시나리오 테스트를 실행하는 클래스입니다."""

    def __init__(self, data_dir: Path):
        """테스트 러너를 초기화합니다.

        Args:
            data_dir: 데이터 디렉토리 경로
        """
        self.commands = SurveyCommands(data_dir)
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0

    def print_test_header(self, test_name: str) -> None:
        """테스트 헤더를 출력합니다.

        Args:
            test_name: 테스트 이름
        """
        self.test_count += 1
        logger.info(f"\n{'='*70}")
        logger.info(f"테스트 #{self.test_count}: {test_name}")
        logger.info(f"{'='*70}")

    def print_test_result(self, passed: bool, message: str) -> None:
        """테스트 결과를 출력합니다.

        Args:
            passed: 테스트 통과 여부
            message: 결과 메시지
        """
        if passed:
            self.passed_count += 1
            logger.info(f"[PASS] {message}")
        else:
            self.failed_count += 1
            logger.error(f"[FAIL] {message}")

    def run_all_tests(self) -> None:
        """모든 테스트를 실행합니다."""
        logger.info("\n" + "="*70)
        logger.info("CLI 시나리오 통합 테스트 시작")
        logger.info("="*70)

        self.test_create_survey_success()
        self.test_create_survey_empty_title()
        self.test_create_survey_empty_description()
        self.test_list_surveys()
        self.test_add_rating_question_success()
        self.test_add_text_question_success()
        self.test_add_choice_question_success()
        self.test_add_question_invalid_survey_id()
        self.test_add_choice_question_insufficient_options()
        self.test_view_survey_success()
        self.test_view_survey_invalid_id()
        self.test_submit_response_success()
        self.test_submit_response_invalid_survey_id()
        self.test_view_results_success()
        self.test_view_results_no_responses()
        self.test_view_results_invalid_survey_id()

        self.print_summary()

    def test_create_survey_success(self) -> None:
        """설문 생성 성공 케이스를 테스트합니다."""
        self.print_test_header("설문 생성 - 정상 케이스")

        try:
            survey_id = self.commands.create_survey("테스트 설문", "테스트 설명")

            if survey_id:
                self.print_test_result(True, f"설문 생성 성공 (ID: {survey_id})")
                setattr(self, "test_survey_id", survey_id)
            else:
                self.print_test_result(False, "설문 ID가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_create_survey_empty_title(self) -> None:
        """빈 제목으로 설문 생성 실패 케이스를 테스트합니다."""
        self.print_test_header("설문 생성 - 빈 제목")

        try:
            survey_id = self.commands.create_survey("", "테스트 설명")
            self.print_test_result(False, "빈 제목으로 설문이 생성되었음")
        except ValueError as e:
            self.print_test_result(True, f"예상된 검증 오류 발생: {str(e)}")
        except Exception as e:
            self.print_test_result(False, f"예상치 못한 예외 발생: {str(e)}")

    def test_create_survey_empty_description(self) -> None:
        """빈 설명으로 설문 생성 실패 케이스를 테스트합니다."""
        self.print_test_header("설문 생성 - 빈 설명")

        try:
            survey_id = self.commands.create_survey("테스트 제목", "")
            self.print_test_result(False, "빈 설명으로 설문이 생성되었음")
        except ValueError as e:
            self.print_test_result(True, f"예상된 검증 오류 발생: {str(e)}")
        except Exception as e:
            self.print_test_result(False, f"예상치 못한 예외 발생: {str(e)}")

    def test_list_surveys(self) -> None:
        """설문 목록 조회를 테스트합니다."""
        self.print_test_header("설문 목록 조회")

        try:
            surveys = self.commands.list_surveys()

            if isinstance(surveys, list):
                self.print_test_result(True, f"설문 목록 조회 성공 (총 {len(surveys)}개)")
                for survey in surveys[:3]:
                    logger.info(f"  - {survey['title']} (ID: {survey['id']})")
            else:
                self.print_test_result(False, "설문 목록 형식이 올바르지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_add_rating_question_success(self) -> None:
        """평점형 질문 추가 성공 케이스를 테스트합니다."""
        self.print_test_header("질문 추가 - 평점형 (정상)")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            question_id = self.commands.add_question(
                self.test_survey_id,
                "서비스 만족도를 평가해주세요",
                "rating"
            )

            if question_id:
                self.print_test_result(True, f"평점형 질문 추가 성공 (ID: {question_id})")
                setattr(self, "test_rating_question_id", question_id)
            else:
                self.print_test_result(False, "질문 ID가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_add_text_question_success(self) -> None:
        """텍스트형 질문 추가 성공 케이스를 테스트합니다."""
        self.print_test_header("질문 추가 - 텍스트형 (정상)")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            question_id = self.commands.add_question(
                self.test_survey_id,
                "개선이 필요한 사항을 자유롭게 작성해주세요",
                "text"
            )

            if question_id:
                self.print_test_result(True, f"텍스트형 질문 추가 성공 (ID: {question_id})")
                setattr(self, "test_text_question_id", question_id)
            else:
                self.print_test_result(False, "질문 ID가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_add_choice_question_success(self) -> None:
        """객관식 질문 추가 성공 케이스를 테스트합니다."""
        self.print_test_header("질문 추가 - 객관식 (정상)")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            question_id = self.commands.add_question(
                self.test_survey_id,
                "가장 만족스러웠던 부분은 무엇입니까?",
                "choice",
                ["의료진 친절도", "대기 시간", "시설 청결도", "진료 결과"]
            )

            if question_id:
                self.print_test_result(True, f"객관식 질문 추가 성공 (ID: {question_id})")
                setattr(self, "test_choice_question_id", question_id)
            else:
                self.print_test_result(False, "질문 ID가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_add_question_invalid_survey_id(self) -> None:
        """존재하지 않는 설문 ID로 질문 추가 실패 케이스를 테스트합니다."""
        self.print_test_header("질문 추가 - 잘못된 설문 ID")

        try:
            question_id = self.commands.add_question(
                "invalid-survey-id",
                "테스트 질문",
                "rating"
            )

            if question_id is None:
                self.print_test_result(True, "잘못된 설문 ID로 질문 추가 실패 (예상된 동작)")
            else:
                self.print_test_result(False, "잘못된 설문 ID로 질문이 추가되었음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_add_choice_question_insufficient_options(self) -> None:
        """선택지가 부족한 객관식 질문 추가 실패 케이스를 테스트합니다."""
        self.print_test_header("질문 추가 - 객관식 (선택지 부족)")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            question_id = self.commands.add_question(
                self.test_survey_id,
                "선택지가 부족한 질문",
                "choice",
                ["선택1"]
            )
            self.print_test_result(False, "선택지가 부족한 객관식 질문이 추가되었음")
        except ValueError as e:
            self.print_test_result(True, f"예상된 검증 오류 발생: {str(e)}")
        except Exception as e:
            self.print_test_result(False, f"예상치 못한 예외 발생: {str(e)}")

    def test_view_survey_success(self) -> None:
        """설문 조회 성공 케이스를 테스트합니다."""
        self.print_test_header("설문 조회 - 정상 케이스")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            survey_data = self.commands.get_survey(self.test_survey_id)

            if survey_data:
                self.print_test_result(
                    True,
                    f"설문 조회 성공 (제목: {survey_data['title']}, 질문 수: {len(survey_data['questions'])}개)"
                )
                logger.info(f"  제목: {survey_data['title']}")
                logger.info(f"  설명: {survey_data['description']}")
                logger.info(f"  질문 수: {len(survey_data['questions'])}개")
            else:
                self.print_test_result(False, "설문 데이터가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_view_survey_invalid_id(self) -> None:
        """존재하지 않는 설문 ID로 조회 실패 케이스를 테스트합니다."""
        self.print_test_header("설문 조회 - 잘못된 ID")

        try:
            survey_data = self.commands.get_survey("invalid-survey-id")

            if survey_data is None:
                self.print_test_result(True, "잘못된 설문 ID로 조회 실패 (예상된 동작)")
            else:
                self.print_test_result(False, "잘못된 설문 ID로 데이터가 반환되었음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_submit_response_success(self) -> None:
        """응답 제출 성공 케이스를 테스트합니다."""
        self.print_test_header("응답 제출 - 정상 케이스")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        if not all(hasattr(self, attr) for attr in ["test_rating_question_id", "test_text_question_id", "test_choice_question_id"]):
            self.print_test_result(False, "테스트 질문 ID가 없음")
            return

        try:
            answers = {
                self.test_rating_question_id: "5",
                self.test_text_question_id: "모든 것이 완벽했습니다",
                self.test_choice_question_id: "의료진 친절도",
            }

            success = self.commands.submit_response(
                self.test_survey_id,
                "test-respondent-001",
                answers
            )

            if success:
                self.print_test_result(True, "응답 제출 성공")
            else:
                self.print_test_result(False, "응답 제출 실패")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_submit_response_invalid_survey_id(self) -> None:
        """존재하지 않는 설문 ID로 응답 제출 실패 케이스를 테스트합니다."""
        self.print_test_header("응답 제출 - 잘못된 설문 ID")

        try:
            answers = {"question-id": "answer"}
            success = self.commands.submit_response(
                "invalid-survey-id",
                "test-respondent-002",
                answers
            )

            if not success:
                self.print_test_result(True, "잘못된 설문 ID로 응답 제출 실패 (예상된 동작)")
            else:
                self.print_test_result(False, "잘못된 설문 ID로 응답이 제출되었음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_view_results_success(self) -> None:
        """결과 조회 성공 케이스를 테스트합니다."""
        self.print_test_header("결과 조회 - 정상 케이스")

        if not hasattr(self, "test_survey_id"):
            self.print_test_result(False, "테스트 설문 ID가 없음")
            return

        try:
            results = self.commands.get_results(self.test_survey_id)

            if results:
                self.print_test_result(True, f"결과 조회 성공 (질문 {len(results)}개)")
                for question_id, stats in list(results.items())[:2]:
                    logger.info(f"  질문 ID: {question_id}")
                    logger.info(f"  응답 수: {stats.get('count', 0)}개")
                    if 'average' in stats:
                        logger.info(f"  평균: {stats['average']}")
            else:
                self.print_test_result(False, "결과 데이터가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_view_results_no_responses(self) -> None:
        """응답이 없는 설문의 결과 조회를 테스트합니다."""
        self.print_test_header("결과 조회 - 응답 없음")

        try:
            survey_id = self.commands.create_survey("응답 없는 설문", "테스트용")
            self.commands.add_question(survey_id, "테스트 질문", "rating")

            results = self.commands.get_results(survey_id)

            if results:
                has_responses = any(stats.get('count', 0) > 0 for stats in results.values())
                if not has_responses:
                    self.print_test_result(True, "응답 없는 설문 결과 조회 성공 (응답 수: 0)")
                else:
                    self.print_test_result(False, "응답이 없어야 하는데 있음")
            else:
                self.print_test_result(False, "결과 데이터가 반환되지 않음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def test_view_results_invalid_survey_id(self) -> None:
        """존재하지 않는 설문 ID로 결과 조회 실패 케이스를 테스트합니다."""
        self.print_test_header("결과 조회 - 잘못된 설문 ID")

        try:
            results = self.commands.get_results("invalid-survey-id")

            if results is None:
                self.print_test_result(True, "잘못된 설문 ID로 결과 조회 실패 (예상된 동작)")
            else:
                self.print_test_result(False, "잘못된 설문 ID로 결과가 반환되었음")
        except Exception as e:
            self.print_test_result(False, f"예외 발생: {str(e)}")

    def print_summary(self) -> None:
        """테스트 결과 요약을 출력합니다."""
        logger.info("\n" + "="*70)
        logger.info("테스트 결과 요약")
        logger.info("="*70)
        logger.info(f"총 테스트 수: {self.test_count}개")
        logger.info(f"통과: {self.passed_count}개")
        logger.info(f"실패: {self.failed_count}개")

        if self.failed_count == 0:
            logger.info("\n모든 테스트가 통과했습니다!")
        else:
            logger.error(f"\n{self.failed_count}개의 테스트가 실패했습니다.")

        logger.info("="*70)


def main() -> None:
    """메인 함수입니다."""
    setup_test_logging()
    data_dir = Path("data")
    runner = TestScenarioRunner(data_dir)
    runner.run_all_tests()


if __name__ == "__main__":
    main()
