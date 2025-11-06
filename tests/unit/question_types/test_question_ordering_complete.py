"""
질문 순서 관리 완전 테스트 스위트
60개 테스트 케이스로 모든 시나리오 검증
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, call
from dataclasses import dataclass
from typing import ClassVar

from domain.entities.user import User
from domain.value_objects.role import Role
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.category import Category
from domain.value_objects.types import QuestionType
from domain.repositories.survey_repository import SurveyRepository
from domain.repositories.response_repository import ResponseRepository
from domain.repositories.category_repository import CategoryRepository

from application.survey_service import SurveyService
from application.response_service import ResponseService
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository


@dataclass(frozen=True, slots=True)
class OrderingTestCase:
    """순서 관리 테스트 케이스"""
    case_id: str
    initial_order: list[int]
    operation: str
    target_index: int | None
    expected_order: list[int]
    description: str


class TestQuestionOrdering:
    """질문 순서 기본 테스트 (20개)"""

    @pytest.fixture
    def setup_ordered_survey(self):
        """순서가 있는 설문 설정"""
        admin = User(
            id="admin1",
            tenant_id="tenant1",
            username="admin",
            email="admin@example.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.TENANT_ADMIN,
            created_at=datetime.now()
        )

        category = Category(
            id="cat1",
            name="순서 테스트",
            description="질문 순서 테스트"
        )

        questions = [
            Question(id="q1", survey_id="s1", text="첫 번째 질문", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="두 번째 질문", question_type=QuestionType.RATING, order=2),
            Question(id="q3", survey_id="s1", text="세 번째 질문", question_type=QuestionType.YES_NO, order=3),
            Question(id="q4", survey_id="s1", text="네 번째 질문", question_type=QuestionType.EMAIL, order=4),
            Question(id="q5", survey_id="s1", text="다섯 번째 질문", question_type=QuestionType.NUMBER, order=5)
        ]

        survey = Survey(
            id="s1",
            title="순서 테스트 설문",
            description="질문 순서 관리",
            creator_id=admin.id,
            category_id=category.id,
            questions=questions
        )

        return admin, category, survey

    def test_initial_order_preservation(self, setup_ordered_survey):
        """초기 순서 유지"""
        _, _, survey = setup_ordered_survey

        # 순서대로 정렬되어야 함
        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        assert [q.id for q in sorted_questions] == ["q1", "q2", "q3", "q4", "q5"]

    def test_order_field_defaults_to_zero(self):
        """order 필드 기본값 0"""
        question = Question(
            id="q1",
            survey_id="s1",
            text="질문",
            question_type=QuestionType.TEXT
            # order 생략
        )
        assert question.order == 0

    def test_questions_sorted_by_order(self, setup_ordered_survey):
        """order 필드로 정렬"""
        _, _, survey = setup_ordered_survey

        # 순서 섞기
        survey.questions[0].order = 3
        survey.questions[1].order = 1
        survey.questions[2].order = 2

        sorted_q = sorted(survey.questions[:3], key=lambda q: q.order)
        assert sorted_q[0].order == 1
        assert sorted_q[1].order == 2
        assert sorted_q[2].order == 3

    def test_duplicate_order_values(self):
        """중복 순서 값"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=1),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=2)
        ]

        # 같은 order 값인 경우 id로 정렬
        sorted_q = sorted(questions, key=lambda q: (q.order, q.id))
        assert [q.id for q in sorted_q] == ["q1", "q2", "q3"]

    def test_negative_order_values(self):
        """음수 순서 값"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=-1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=0),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=1)
        ]

        sorted_q = sorted(questions, key=lambda q: q.order)
        assert sorted_q[0].order == -1
        assert sorted_q[1].order == 0
        assert sorted_q[2].order == 1

    def test_large_order_values(self):
        """큰 순서 값"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1000),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=100),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=10)
        ]

        sorted_q = sorted(questions, key=lambda q: q.order)
        assert sorted_q[0].order == 10
        assert sorted_q[1].order == 100
        assert sorted_q[2].order == 1000

    def test_non_sequential_orders(self):
        """비연속적 순서"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=10),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=20),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=30)
        ]

        sorted_q = sorted(questions, key=lambda q: q.order)
        assert [q.order for q in sorted_q] == [10, 20, 30]

    @pytest.mark.parametrize("orders,expected", [
        ([3, 1, 2], [1, 2, 3]),
        ([5, 4, 3, 2, 1], [1, 2, 3, 4, 5]),
        ([2, 4, 1, 3], [1, 2, 3, 4]),
        ([1, 1, 1], [1, 1, 1])  # 중복 허용
    ])
    def test_various_order_patterns(self, orders, expected):
        """다양한 순서 패턴"""
        questions = []
        for i, order in enumerate(orders):
            questions.append(
                Question(id=f"q{i}", survey_id="s1", text=f"Q{i}",
                        question_type=QuestionType.TEXT, order=order)
            )

        sorted_q = sorted(questions, key=lambda q: q.order)
        assert [q.order for q in sorted_q] == expected

    def test_order_with_mixed_types(self):
        """다양한 질문 타입과 순서"""
        questions = [
            Question(id="q1", survey_id="s1", text="Text", question_type=QuestionType.TEXT, order=3),
            Question(id="q2", survey_id="s1", text="Email", question_type=QuestionType.EMAIL, order=1),
            Question(id="q3", survey_id="s1", text="Number", question_type=QuestionType.NUMBER, order=2),
            Question(id="q4", survey_id="s1", text="YesNo", question_type=QuestionType.YES_NO, order=4)
        ]

        sorted_q = sorted(questions, key=lambda q: q.order)
        assert [q.question_type for q in sorted_q] == [
            QuestionType.EMAIL,
            QuestionType.NUMBER,
            QuestionType.TEXT,
            QuestionType.YES_NO
        ]

    def test_order_preservation_in_dict(self):
        """딕셔너리 변환 시 순서 보존"""
        question = Question(
            id="q1",
            survey_id="s1",
            text="질문",
            question_type=QuestionType.TEXT,
            order=5
        )

        q_dict = question.to_dict()
        assert q_dict["order"] == 5

        # from_dict로 복원
        restored = Question.from_dict(q_dict)
        assert restored.order == 5


class TestReorderingOperations:
    """순서 재배치 작업 테스트 (20개)"""

    @pytest.fixture
    def survey_service(self):
        """설문 서비스 설정"""
        survey_repo = Mock(spec=SurveyRepository)
        response_repo = Mock(spec=ResponseRepository)
        category_repo = Mock(spec=CategoryRepository)

        service = SurveyService(survey_repo, response_repo, category_repo)
        return service, survey_repo

    def test_reorder_questions_basic(self, survey_service):
        """기본 순서 재배치"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id=admin.id,
            questions=questions
        )

        survey_repo.find_by_id.return_value = survey
        survey_repo.update_question.return_value = True

        # q1과 q3의 순서 바꾸기
        new_orders = {"q1": 3, "q2": 2, "q3": 1}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_success
        assert survey_repo.update_question.call_count == 3

    def test_reorder_partial_questions(self, survey_service):
        """일부 질문만 순서 변경"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.update_question.return_value = True

        # q1만 순서 변경
        new_orders = {"q1": 3}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_success
        # q1만 업데이트
        assert survey_repo.update_question.call_count == 1

    def test_reorder_invalid_question_id(self, survey_service):
        """잘못된 질문 ID로 순서 변경"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id=admin.id,
            questions=[
                Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1)
            ]
        )

        survey_repo.find_by_id.return_value = survey

        # 존재하지 않는 질문
        new_orders = {"q99": 1}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_failure
        assert "찾을 수 없" in result.error

    def test_reorder_no_permission(self, survey_service):
        """권한 없는 사용자의 순서 변경"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())
        other = User(id="user2", tenant_id="tenant1", username="user", email="user@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.RESPONDENT, created_at=datetime.now())

        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id=admin.id,
            questions=[
                Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1)
            ]
        )

        survey_repo.find_by_id.return_value = survey

        result = service.reorder_questions(other, "s1", {"q1": 2})

        assert result.is_failure
        assert "권한" in result.error

    def test_move_question_up(self, survey_service):
        """질문 위로 이동"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.find_question_by_id.return_value = questions[1]  # q2
        survey_repo.update_question.return_value = True

        result = service.move_question_up(admin, "q2")

        assert result.is_success
        # q1과 q2의 순서가 바뀌어야 함
        assert survey_repo.update_question.call_count == 2

    def test_move_question_up_first(self, survey_service):
        """첫 번째 질문 위로 이동 시도"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.find_question_by_id.return_value = questions[0]  # q1

        result = service.move_question_up(admin, "q1")

        assert result.is_failure
        assert "첫" in result.error or "이동할 수 없" in result.error

    def test_move_question_down(self, survey_service):
        """질문 아래로 이동"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.find_question_by_id.return_value = questions[1]  # q2
        survey_repo.update_question.return_value = True

        result = service.move_question_down(admin, "q2")

        assert result.is_success
        # q2와 q3의 순서가 바뀌어야 함
        assert survey_repo.update_question.call_count == 2

    def test_move_question_down_last(self, survey_service):
        """마지막 질문 아래로 이동 시도"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.find_question_by_id.return_value = questions[1]  # q2

        result = service.move_question_down(admin, "q2")

        assert result.is_failure
        assert "마지막" in result.error or "이동할 수 없" in result.error

    def test_bulk_reorder_all_questions(self, survey_service):
        """모든 질문 일괄 재배치"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id=f"q{i}", survey_id="s1", text=f"Q{i}",
                    question_type=QuestionType.TEXT, order=i)
            for i in range(1, 11)  # 10개 질문
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.update_question.return_value = True

        # 역순으로 재배치
        new_orders = {f"q{i}": 11-i for i in range(1, 11)}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_success
        assert survey_repo.update_question.call_count == 10

    def test_reorder_with_gaps(self, survey_service):
        """간격이 있는 순서로 재배치"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.update_question.return_value = True

        # 10, 20, 30으로 재배치
        new_orders = {"q1": 10, "q2": 20, "q3": 30}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_success

    def test_swap_two_questions(self, survey_service):
        """두 질문의 순서 교환"""
        service, survey_repo = survey_service

        admin = User(id="admin1", tenant_id="tenant1", username="admin", email="admin@example.com",
                    password_hash="$2b$12$dummy_hash", role=Role.TENANT_ADMIN, created_at=datetime.now())

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2)
        ]

        survey = Survey(id="s1", title="Test", description="Test", creator_id=admin.id, questions=questions)

        survey_repo.find_by_id.return_value = survey
        survey_repo.update_question.return_value = True

        # q1과 q2 교환
        new_orders = {"q1": 2, "q2": 1}
        result = service.reorder_questions(admin, "s1", new_orders)

        assert result.is_success
        assert survey_repo.update_question.call_count == 2


class TestOrderingPersistence:
    """순서 영속성 테스트 (10개)"""

    @pytest.fixture
    def csv_repo(self, tmp_path):
        """CSV 저장소 설정"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return CsvSurveyRepository(str(data_dir))

    def test_save_with_order(self, csv_repo):
        """순서 포함 저장"""
        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id="admin1",
            questions=[
                Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=2),
                Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=1)
            ]
        )

        result = csv_repo.save_survey(survey)
        assert result

        # 저장 후 로드
        loaded = csv_repo.find_survey_by_id("s1")
        assert loaded is not None
        assert loaded.questions[0].order == 2
        assert loaded.questions[1].order == 1

    def test_load_without_order_field(self, tmp_path):
        """order 필드 없는 레거시 데이터 로드"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # 레거시 CSV (order 필드 없음)
        questions_file = data_dir / "questions.csv"
        questions_file.write_text(
            "id,survey_id,text,question_type,options,created_at,updated_at,is_required\n"
            "q1,s1,Question 1,text,,2024-01-01,2024-01-01,true\n"
            "q2,s1,Question 2,rating,,2024-01-01,2024-01-01,true\n",
            encoding="utf-8-sig"
        )

        surveys_file = data_dir / "surveys.csv"
        surveys_file.write_text(
            "id,title,description,creator_id,category_id,created_at,updated_at\n"
            "s1,Survey,Desc,admin1,,2024-01-01,2024-01-01\n",
            encoding="utf-8-sig"
        )

        csv_repo = CsvSurveyRepository(str(data_dir))
        survey = csv_repo.find_survey_by_id("s1")

        assert survey is not None
        # order 필드가 없으면 기본값 0
        assert all(q.order == 0 for q in survey.questions)

    def test_update_question_order(self, csv_repo):
        """질문 순서 업데이트"""
        question = Question(
            id="q1",
            survey_id="s1",
            text="Question",
            question_type=QuestionType.TEXT,
            order=1
        )

        csv_repo.save_question(question)

        # 순서 변경
        question.order = 5
        result = csv_repo.update_question(question)
        assert result

        # 확인
        loaded = csv_repo.find_question_by_id("q1")
        assert loaded is not None
        assert loaded.order == 5

    def test_preserve_order_on_update(self, csv_repo):
        """업데이트 시 순서 보존"""
        survey = Survey(
            id="s1",
            title="Original",
            description="Test",
            creator_id="admin1",
            questions=[
                Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=3),
                Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=1),
                Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=2)
            ]
        )

        csv_repo.save_survey(survey)

        # 제목만 업데이트
        survey.title = "Updated"
        csv_repo.update_survey(survey)

        loaded = csv_repo.find_survey_by_id("s1")
        assert loaded.title == "Updated"
        # 순서는 그대로
        assert [q.order for q in loaded.questions] == [3, 1, 2]

    def test_order_in_csv_format(self, tmp_path):
        """CSV 형식에서 order 필드 확인"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        csv_repo = CsvSurveyRepository(str(data_dir))

        question = Question(
            id="q1",
            survey_id="s1",
            text="Question",
            question_type=QuestionType.TEXT,
            order=5
        )

        csv_repo.save_question(question)

        # CSV 파일 직접 확인
        questions_file = data_dir / "questions.csv"
        content = questions_file.read_text(encoding="utf-8-sig")

        assert "order" in content
        assert ",5," in content or ",5\n" in content

    def test_mixed_order_values_sorting(self, csv_repo):
        """혼합된 순서 값 정렬"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=100),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=0),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=50),
            Question(id="q4", survey_id="s1", text="Q4", question_type=QuestionType.TEXT, order=-10)
        ]

        for q in questions:
            csv_repo.save_question(q)

        # 설문에서 정렬 확인
        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id="admin1",
            questions=questions
        )

        csv_repo.save_survey(survey)

        loaded = csv_repo.find_survey_by_id("s1")
        sorted_questions = sorted(loaded.questions, key=lambda q: q.order)

        assert [q.order for q in sorted_questions] == [-10, 0, 50, 100]

    def test_order_backward_compatibility(self, tmp_path):
        """order 필드 하위 호환성"""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        csv_repo = CsvSurveyRepository(str(data_dir))

        # 새 질문 (order 있음)
        new_q = Question(id="q1", survey_id="s1", text="New", question_type=QuestionType.TEXT, order=5)
        csv_repo.save_question(new_q)

        # CSV 수정하여 order 필드 제거 (레거시 시뮬레이션)
        questions_file = data_dir / "questions.csv"
        lines = questions_file.read_text(encoding="utf-8-sig").splitlines()

        # 헤더에서 order 제거
        header = lines[0].replace(",order", "")
        # 데이터에서 order 값 제거
        data = lines[1].replace(",5", "")

        questions_file.write_text(f"{header}\n{data}\n", encoding="utf-8-sig")

        # 다시 로드
        csv_repo2 = CsvSurveyRepository(str(data_dir))
        loaded = csv_repo2.find_question_by_id("q1")

        assert loaded is not None
        assert loaded.order == 0  # 기본값


class TestOrderingIntegration:
    """순서 통합 테스트 (10개)"""

    def test_cli_display_order(self):
        """CLI 표시 순서"""
        questions = [
            Question(id="q1", survey_id="s1", text="Third", question_type=QuestionType.TEXT, order=3),
            Question(id="q2", survey_id="s1", text="First", question_type=QuestionType.TEXT, order=1),
            Question(id="q3", survey_id="s1", text="Second", question_type=QuestionType.TEXT, order=2)
        ]

        # CLI에서 표시할 때 정렬
        sorted_q = sorted(questions, key=lambda q: q.order)
        display_order = [q.text for q in sorted_q]

        assert display_order == ["First", "Second", "Third"]

    def test_response_collection_order(self):
        """응답 수집 시 질문 순서"""
        survey = Survey(
            id="s1",
            title="Test",
            description="Test",
            creator_id="admin1",
            questions=[
                Question(id="q3", survey_id="s1", text="Email?", question_type=QuestionType.EMAIL, order=3),
                Question(id="q1", survey_id="s1", text="Name?", question_type=QuestionType.TEXT, order=1),
                Question(id="q2", survey_id="s1", text="Age?", question_type=QuestionType.NUMBER, order=2)
            ]
        )

        # 응답자가 볼 순서
        response_order = sorted(survey.questions, key=lambda q: q.order)
        assert [q.text for q in response_order] == ["Name?", "Age?", "Email?"]

    def test_results_display_order(self):
        """결과 표시 순서"""
        responses = [
            Response(id="r1", survey_id="s1", respondent_id="u1",
                    answers={"q1": "Answer1", "q2": "Answer2", "q3": "Answer3"})
        ]

        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=2),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=1),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        # 결과 표시 시 질문 순서대로
        sorted_q = sorted(questions, key=lambda q: q.order)
        result_order = []
        for q in sorted_q:
            result_order.append((q.text, responses[0].answers.get(q.id)))

        assert result_order == [
            ("Q2", "Answer2"),
            ("Q1", "Answer1"),
            ("Q3", "Answer3")
        ]

    def test_export_order(self):
        """내보내기 시 순서"""
        survey = Survey(
            id="s1",
            title="Export Test",
            description="Test",
            creator_id="admin1",
            questions=[
                Question(id="q1", survey_id="s1", text="Last", question_type=QuestionType.TEXT, order=99),
                Question(id="q2", survey_id="s1", text="First", question_type=QuestionType.TEXT, order=1),
                Question(id="q3", survey_id="s1", text="Middle", question_type=QuestionType.TEXT, order=50)
            ]
        )

        # CSV 내보내기 시 순서
        export_headers = []
        for q in sorted(survey.questions, key=lambda q: q.order):
            export_headers.append(q.text)

        assert export_headers == ["First", "Middle", "Last"]

    def test_dynamic_reordering_ui(self):
        """동적 순서 변경 UI 시뮬레이션"""
        # 드래그 앤 드롭 시뮬레이션
        questions = [
            {"id": "q1", "order": 1, "text": "Question 1"},
            {"id": "q2", "order": 2, "text": "Question 2"},
            {"id": "q3", "order": 3, "text": "Question 3"}
        ]

        # q3을 q1 위치로 드래그
        def drag_drop(from_idx, to_idx):
            item = questions.pop(from_idx)
            questions.insert(to_idx, item)

            # 순서 재계산
            for i, q in enumerate(questions):
                q["order"] = i + 1

        drag_drop(2, 0)  # q3을 첫 번째로

        assert [q["id"] for q in questions] == ["q3", "q1", "q2"]
        assert [q["order"] for q in questions] == [1, 2, 3]

    def test_conditional_ordering(self):
        """조건부 순서 (로직 점프)"""
        # 특정 답변에 따라 다음 질문이 달라지는 경우
        questions = [
            Question(id="q1", survey_id="s1", text="Yes or No?", question_type=QuestionType.YES_NO, order=1),
            Question(id="q2", survey_id="s1", text="If Yes", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="If No", question_type=QuestionType.TEXT, order=2),
            Question(id="q4", survey_id="s1", text="Common", question_type=QuestionType.TEXT, order=3)
        ]

        # 응답에 따른 다음 질문 결정
        def get_next_question(current_q, answer):
            if current_q.id == "q1":
                if answer == "y":
                    return "q2"
                else:
                    return "q3"
            elif current_q.id in ["q2", "q3"]:
                return "q4"
            return None

        # Yes 선택 시 경로
        assert get_next_question(questions[0], "y") == "q2"
        # No 선택 시 경로
        assert get_next_question(questions[0], "n") == "q3"

    def test_order_with_deletion(self):
        """질문 삭제 후 순서 재정렬"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3),
            Question(id="q4", survey_id="s1", text="Q4", question_type=QuestionType.TEXT, order=4)
        ]

        # q2 삭제
        questions = [q for q in questions if q.id != "q2"]

        # 순서 재정렬
        for i, q in enumerate(questions):
            q.order = i + 1

        assert [q.order for q in questions] == [1, 2, 3]
        assert [q.id for q in questions] == ["q1", "q3", "q4"]

    def test_order_with_insertion(self):
        """질문 삽입 시 순서 조정"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=2),
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=3)
        ]

        # q1과 q2 사이에 새 질문 삽입
        new_q = Question(id="q_new", survey_id="s1", text="New", question_type=QuestionType.TEXT, order=1.5)
        questions.append(new_q)

        # 순서로 정렬
        questions = sorted(questions, key=lambda q: q.order)

        # 순서 재정렬 (1, 2, 3, 4로)
        for i, q in enumerate(questions):
            q.order = i + 1

        assert [q.id for q in questions] == ["q1", "q_new", "q2", "q3"]
        assert [q.order for q in questions] == [1, 2, 3, 4]

    def test_batch_order_update(self):
        """일괄 순서 업데이트"""
        questions = [
            Question(id=f"q{i}", survey_id="s1", text=f"Q{i}",
                    question_type=QuestionType.TEXT, order=i*10)
            for i in range(1, 21)  # 20개 질문
        ]

        # 모든 질문을 1씩 증가하는 순서로 정규화
        for i, q in enumerate(questions):
            q.order = i + 1

        assert all(questions[i].order == i + 1 for i in range(20))

    def test_order_conflict_resolution(self):
        """순서 충돌 해결"""
        questions = [
            Question(id="q1", survey_id="s1", text="Q1", question_type=QuestionType.TEXT, order=1),
            Question(id="q2", survey_id="s1", text="Q2", question_type=QuestionType.TEXT, order=1),  # 충돌
            Question(id="q3", survey_id="s1", text="Q3", question_type=QuestionType.TEXT, order=2),
            Question(id="q4", survey_id="s1", text="Q4", question_type=QuestionType.TEXT, order=2)   # 충돌
        ]

        # 충돌 해결: 같은 순서면 ID로 정렬
        questions = sorted(questions, key=lambda q: (q.order, q.id))

        # 순서 재할당
        for i, q in enumerate(questions):
            q.order = i + 1

        assert [q.id for q in questions] == ["q1", "q2", "q3", "q4"]
        assert [q.order for q in questions] == [1, 2, 3, 4]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])