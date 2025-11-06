import uuid
import csv
import re
from datetime import datetime
from collections import Counter
from pathlib import Path
from domain.entities.response import Response
from domain.entities.response_history import ResponseHistory
from domain.entities.user import User
from domain.value_objects.result import Success, Failure, Result
from domain.value_objects.types import QuestionType
from domain.repositories.response_repository import ResponseRepository
from domain.repositories.response_history_repository import ResponseHistoryRepository
from domain.repositories.survey_repository import SurveyRepository
from domain.repositories.category_repository import CategoryRepository


class ResponseService:
    """응답 관련 유스케이스를 처리하는 서비스입니다.

    Attributes:
        response_repository: 응답 저장소
        response_history_repository: 응답 수정 이력 저장소
        survey_repository: 설문 저장소
    """

    def __init__(
        self,
        response_repository: ResponseRepository,
        response_history_repository: ResponseHistoryRepository,
        survey_repository: SurveyRepository,
        category_repository: CategoryRepository | None = None,
    ):
        """서비스를 초기화합니다.

        Args:
            response_repository: 응답 저장소 구현체
            response_history_repository: 응답 수정 이력 저장소 구현체
            survey_repository: 설문 저장소 구현체
            category_repository: 범주 저장소 구현체 (선택적)
        """
        self.response_repository = response_repository
        self.response_history_repository = response_history_repository
        self.survey_repository = survey_repository
        self.category_repository = category_repository

    def submit_response(
        self,
        user: User,
        survey_id: str,
        answers: dict[str, str],
        session_id: str,
        time_spent_data: dict[str, int],
    ) -> Result[None, str]:
        """설문 응답을 제출합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            answers: 질문 ID와 답변의 딕셔너리
            session_id: 세션 ID
            time_spent_data: 질문 ID와 소요 시간(초)의 딕셔너리

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        question_map = {q.id: q for q in survey.questions}

        # 필수 질문들이 모두 답변되었는지 확인
        for question in survey.questions:
            if question.is_required and question.id not in answers:
                return Failure(f"필수 질문에 답변하지 않았습니다: {question.text}")

        for question_id, answer in answers.items():
            question = question_map.get(question_id)
            if not question:
                return Failure(f"질문을 찾을 수 없습니다: {question_id}")

            validation_result = self._validate_answer(question, answer)
            if validation_result.is_failure():
                return validation_result

            time_spent_seconds = time_spent_data.get(question_id, 0)

            response_id = str(uuid.uuid4())
            response = Response(
                id=response_id,
                survey_id=survey_id,
                question_id=question_id,
                answer=answer,
                respondent_id=user.id,
                answered_at=datetime.now(),
                session_id=session_id,
                time_spent_seconds=time_spent_seconds,
            )
            self.response_repository.save(response)

        return Success(None)

    def _validate_answer(self, question, answer: str) -> Result[None, str]:
        """답변을 검증합니다.

        Args:
            question: Question 엔티티
            answer: 답변

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        from domain.value_objects.types import QuestionType
        import datetime
        import re

        # 선택적 질문이고 답변이 없으면 OK
        if not question.is_required and not answer:
            return Success(None)

        if question.question_type == QuestionType.RATING:
            if not answer.isdigit():
                return Failure(f"평점은 숫자여야 합니다: {answer}")

            rating = int(answer)
            if rating < 1 or rating > 5:
                return Failure(f"평점은 1-5 사이여야 합니다: {rating}")

        elif question.question_type == QuestionType.SCALE_10:
            if not answer.isdigit():
                return Failure(f"척도는 숫자여야 합니다: {answer}")

            scale = int(answer)
            if scale < 1 or scale > 10:
                return Failure(f"척도는 1-10 사이여야 합니다: {scale}")

        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            if not question.options:
                return Failure("객관식 질문에 선택지가 없습니다")

            if answer not in question.options:
                return Failure(f"유효하지 않은 선택지입니다: {answer}. 가능한 선택지: {', '.join(question.options)}")

        elif question.question_type == QuestionType.MULTI_SELECT:
            if not question.options:
                return Failure("다중 선택 질문에 선택지가 없습니다")

            selected = [item.strip() for item in answer.split(',')]
            invalid = [item for item in selected if item not in question.options]
            if invalid:
                return Failure(f"유효하지 않은 선택: {', '.join(invalid)}. 가능한 선택지: {', '.join(question.options)}")

        elif question.question_type == QuestionType.DATE:
            try:
                datetime.datetime.strptime(answer, "%Y-%m-%d")
            except ValueError:
                return Failure(f"날짜는 YYYY-MM-DD 형식이어야 합니다: {answer}")

        elif question.question_type == QuestionType.NUMBER:
            try:
                float(answer)
            except ValueError:
                return Failure(f"유효한 숫자가 아닙니다: {answer}")

        elif question.question_type == QuestionType.EMAIL:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, answer):
                return Failure(f"유효한 이메일 형식이 아닙니다: {answer}")

        elif question.question_type == QuestionType.YES_NO:
            answer_lower = answer.lower().strip()
            if answer_lower not in ['y', 'n', 'yes', 'no', '예', '아니오']:
                return Failure(f"답변은 y (예) 또는 n (아니오)여야 합니다: {answer}")

        return Success(None)

    def get_survey_results(self, user: User, survey_id: str) -> Result[dict[str, dict[str, int | float | list[str]]], str]:
        """설문 결과를 조회합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자

        Returns:
            Success[질문 ID별 결과 통계] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_view_results(is_owner):
            return Failure("결과 조회 권한이 없습니다")

        results = {}
        for question in survey.questions:
            responses = self.response_repository.find_by_question_id(question.id)
            answers = [r.answer for r in responses]

            if question.question_type == QuestionType.RATING:
                ratings = [int(a) for a in answers if a.isdigit()]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0.0
                counter = Counter([str(r) for r in ratings])
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(ratings),
                    "average": round(avg_rating, 2),
                    "distribution": dict(counter),
                }
            elif question.question_type == QuestionType.SCALE_10:
                scales = [int(a) for a in answers if a.isdigit()]
                avg_scale = sum(scales) / len(scales) if scales else 0.0
                counter = Counter([str(s) for s in scales])
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(scales),
                    "average": round(avg_scale, 2),
                    "distribution": dict(counter),
                }
            elif question.question_type == QuestionType.MULTIPLE_CHOICE:
                counter = Counter(answers)
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(answers),
                    "distribution": dict(counter),
                }
            elif question.question_type == QuestionType.YES_NO:
                # 정규화: y/yes/예 -> y, n/no/아니오 -> n
                normalized = []
                for a in answers:
                    a_lower = a.lower().strip()
                    if a_lower in ['y', 'yes', '예']:
                        normalized.append('y')
                    elif a_lower in ['n', 'no', '아니오']:
                        normalized.append('n')
                counter = Counter(normalized)
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(normalized),
                    "distribution": {"예": counter.get('y', 0), "아니오": counter.get('n', 0)},
                }
            elif question.question_type == QuestionType.MULTI_SELECT:
                # 다중 선택 답변 집계
                all_selections = []
                for a in answers:
                    selections = [item.strip() for item in a.split(',')]
                    all_selections.extend(selections)
                counter = Counter(all_selections)
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(answers),
                    "distribution": dict(counter),
                    "total_selections": len(all_selections),
                }
            elif question.question_type == QuestionType.NUMBER:
                # 숫자형 답변 통계
                numbers = []
                for a in answers:
                    try:
                        numbers.append(float(a))
                    except ValueError:
                        pass
                if numbers:
                    avg_num = sum(numbers) / len(numbers)
                    results[question.id] = {
                        "question": question.text,
                        "type": question.question_type.value,
                        "count": len(numbers),
                        "average": round(avg_num, 2),
                        "min": min(numbers),
                        "max": max(numbers),
                        "answers": [str(n) for n in numbers],
                    }
                else:
                    results[question.id] = {
                        "question": question.text,
                        "type": question.question_type.value,
                        "count": 0,
                        "answers": [],
                    }
            else:
                # TEXT, DATE, EMAIL 등은 개별 답변 목록으로 제공
                results[question.id] = {
                    "question": question.text,
                    "type": question.question_type.value,
                    "count": len(answers),
                    "answers": answers,
                }

        return Success(results)

    def update_response(self, user: User, response_id: str, answer: str) -> Result[None, str]:
        """응답을 수정합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 식별자
            answer: 새로운 답변

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        all_responses = []
        all_surveys = self.survey_repository.find_all_surveys()
        for survey in all_surveys:
            responses = self.response_repository.find_by_survey_id(survey.id)
            all_responses.extend(responses)

        target_response = None
        for resp in all_responses:
            if resp.id == response_id:
                target_response = resp
                break

        if not target_response:
            return Failure(f"응답을 찾을 수 없습니다: {response_id}")

        survey = self.survey_repository.find_survey_by_id(target_response.survey_id)
        if not survey:
            return Failure("응답에 해당하는 설문을 찾을 수 없습니다")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 응답에 접근할 수 없습니다")

        if target_response.respondent_id != user.id and not user.role.can_manage_survey(survey.owner_id == user.id):
            return Failure("응답 수정 권한이 없습니다")

        history_id = str(uuid.uuid4())
        history = ResponseHistory(
            id=history_id,
            response_id=response_id,
            old_answer=target_response.answer,
            new_answer=answer,
            updated_at=datetime.now(),
            updated_by=user.id,
        )
        self.response_history_repository.save(history)

        self.response_repository.update_response(response_id, answer)
        return Success(None)

    def delete_response(self, user: User, response_id: str) -> Result[None, str]:
        """응답을 삭제합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 식별자

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        all_responses = []
        all_surveys = self.survey_repository.find_all_surveys()
        for survey in all_surveys:
            responses = self.response_repository.find_by_survey_id(survey.id)
            all_responses.extend(responses)

        target_response = None
        for resp in all_responses:
            if resp.id == response_id:
                target_response = resp
                break

        if not target_response:
            return Failure(f"응답을 찾을 수 없습니다: {response_id}")

        survey = self.survey_repository.find_survey_by_id(target_response.survey_id)
        if not survey:
            return Failure("응답에 해당하는 설문을 찾을 수 없습니다")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 응답에 접근할 수 없습니다")

        if target_response.respondent_id != user.id and not user.role.can_manage_survey(survey.owner_id == user.id):
            return Failure("응답 삭제 권한이 없습니다")

        self.response_repository.delete_response(response_id)
        return Success(None)

    def get_response_history(self, user: User, response_id: str) -> Result[list[ResponseHistory], str]:
        """응답 수정 이력을 조회합니다.

        Args:
            user: 사용자 엔티티
            response_id: 응답 식별자

        Returns:
            Success[이력 목록] 또는 Failure[에러 메시지]
        """
        all_responses = []
        all_surveys = self.survey_repository.find_all_surveys()
        for survey in all_surveys:
            responses = self.response_repository.find_by_survey_id(survey.id)
            all_responses.extend(responses)

        target_response = None
        for resp in all_responses:
            if resp.id == response_id:
                target_response = resp
                break

        if not target_response:
            return Failure(f"응답을 찾을 수 없습니다: {response_id}")

        survey = self.survey_repository.find_survey_by_id(target_response.survey_id)
        if not survey:
            return Failure("응답에 해당하는 설문을 찾을 수 없습니다")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 응답에 접근할 수 없습니다")

        if target_response.respondent_id != user.id and not user.role.can_manage_survey(survey.owner_id == user.id):
            return Failure("이력 조회 권한이 없습니다")

        histories = self.response_history_repository.find_by_response_id(response_id)
        return Success(histories)

    def export_results_to_csv(
        self,
        user: User,
        survey_id: str,
        export_dir: Path | None = None
    ) -> Result[tuple[str, str], str]:
        """설문 결과를 CSV 파일로 내보냅니다.

        Raw Data와 Summary 두 개의 CSV 파일을 생성합니다.

        Args:
            user: 사용자 엔티티
            survey_id: 설문 식별자
            export_dir: CSV 파일을 저장할 디렉토리 (None이면 기본 exports 폴더)

        Returns:
            Success[(raw_csv_path, summary_csv_path)] 또는 Failure[에러 메시지]
        """
        survey = self.survey_repository.find_survey_by_id(survey_id)
        if not survey:
            return Failure(f"설문을 찾을 수 없습니다: {survey_id}")

        if survey.tenant_id != user.tenant_id:
            return Failure("다른 테넌트의 설문에 접근할 수 없습니다")

        is_owner = survey.owner_id == user.id
        if not user.role.can_view_results(is_owner):
            return Failure("결과 조회 권한이 없습니다")

        if export_dir is None:
            export_dir = Path("data") / "exports"

        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\s-]', '', survey.title).strip()[:50]
        if not safe_title:
            safe_title = "survey"

        raw_filename = f"{safe_title}_raw_{timestamp}.csv"
        summary_filename = f"{safe_title}_summary_{timestamp}.csv"
        raw_path = export_dir / raw_filename
        summary_path = export_dir / summary_filename

        raw_result = self._generate_raw_data_csv(survey, raw_path)
        if raw_result.is_failure():
            return raw_result

        summary_result = self._generate_summary_csv(survey, summary_path)
        if summary_result.is_failure():
            return summary_result

        return Success((str(raw_path), str(summary_path)))

    def _generate_raw_data_csv(self, survey, csv_path: Path) -> Result[None, str]:
        """Raw Data CSV 파일을 생성합니다.

        Args:
            survey: Survey 엔티티
            csv_path: CSV 파일 경로

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        try:
            fieldnames = [
                "응답ID",
                "설문제목",
                "질문",
                "질문유형",
                "질문범주",
                "답변",
                "응답자ID",
                "응답시간",
                "소요시간(초)",
                "세션ID"
            ]

            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for question in survey.questions:
                    category_name = ""
                    if question.category_id and self.category_repository:
                        category = self.category_repository.find_category_by_id(question.category_id)
                        if category:
                            category_name = category.name

                    responses = self.response_repository.find_by_question_id(question.id)

                    for response in responses:
                        row = {
                            "응답ID": response.id,
                            "설문제목": survey.title,
                            "질문": question.text,
                            "질문유형": question.question_type.value,
                            "질문범주": category_name,
                            "답변": response.answer,
                            "응답자ID": response.respondent_id,
                            "응답시간": response.answered_at.strftime("%Y-%m-%d %H:%M:%S"),
                            "소요시간(초)": response.time_spent_seconds,
                            "세션ID": response.session_id
                        }
                        writer.writerow(row)

                f.flush()

            return Success(None)

        except Exception as e:
            return Failure(f"Raw Data CSV 생성 실패: {str(e)}")

    def _generate_summary_csv(self, survey, csv_path: Path) -> Result[None, str]:
        """Summary CSV 파일을 생성합니다.

        Args:
            survey: Survey 엔티티
            csv_path: CSV 파일 경로

        Returns:
            Success[None] 또는 Failure[에러 메시지]
        """
        try:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)

                writer.writerow(["설문 정보"])
                writer.writerow(["제목", survey.title])
                writer.writerow(["설명", survey.description])
                writer.writerow(["생성일", survey.created_at.strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow([])

                for question in survey.questions:
                    category_name = ""
                    if question.category_id and self.category_repository:
                        category = self.category_repository.find_category_by_id(question.category_id)
                        if category:
                            category_name = category.name

                    responses = self.response_repository.find_by_question_id(question.id)
                    answers = [r.answer for r in responses]

                    writer.writerow(["질문", question.text])
                    writer.writerow(["유형", question.question_type.value])
                    writer.writerow(["범주", category_name])
                    writer.writerow(["총 응답 수", len(answers)])

                    if question.question_type == QuestionType.RATING:
                        ratings = [int(a) for a in answers if a.isdigit()]
                        if ratings:
                            avg_rating = sum(ratings) / len(ratings)
                            writer.writerow(["평균 평점", round(avg_rating, 2)])

                            counter = Counter(ratings)
                            writer.writerow(["평점", "개수"])
                            for rating in range(1, 6):
                                count = counter.get(rating, 0)
                                writer.writerow([rating, count])

                    elif question.question_type == QuestionType.MULTIPLE_CHOICE:
                        counter = Counter(answers)
                        writer.writerow(["선택지", "개수"])
                        for choice, count in counter.items():
                            writer.writerow([choice, count])

                    elif question.question_type == QuestionType.TEXT:
                        writer.writerow(["텍스트 응답은 Raw Data CSV를 참조하세요"])

                    writer.writerow([])

                f.flush()

            return Success(None)

        except Exception as e:
            return Failure(f"Summary CSV 생성 실패: {str(e)}")
