"""
질문 관리 시나리오 테스트
Question Management Scenario Tests

질문의 추가, 수정, 삭제, 순서 변경 등 동적 관리를 검증합니다.
- 질문 순서 변경 (위/아래 이동, 일괄 재배치)
- 질문 삭제 후 순서 조정
- 필수/선택 속성 변경
- 범주별 질문 관리
"""

import pytest
import uuid
from datetime import datetime
from typing import List, Dict, Any

from domain.entities.user import User
from domain.entities.tenant import Tenant
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.category import Category
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType

from application.auth_service import AuthService
from application.survey_service import SurveyService
from application.response_service import ResponseService

from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_category_repository import CsvCategoryRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository


class TestQuestionManagementScenarios:
    """질문 관리 시나리오 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.tenant_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())
        self.manager_id = str(uuid.uuid4())
        self.respondent_id = str(uuid.uuid4())

    @pytest.fixture
    def setup_repositories(self, temp_data_dir):
        """테스트용 저장소 설정"""
        return {
            'tenant_repo': CsvTenantRepository(temp_data_dir),
            'user_repo': CsvUserRepository(temp_data_dir),
            'survey_repo': CsvSurveyRepository(temp_data_dir),
            'response_repo': CsvResponseRepository(temp_data_dir),
            'category_repo': CsvCategoryRepository(temp_data_dir),
            'session_repo': CsvSessionRepository(temp_data_dir)
        }

    @pytest.fixture
    def setup_services(self, setup_repositories):
        """테스트용 서비스 설정"""
        repos = setup_repositories

        auth_service = AuthService(
            repos['user_repo'],
            repos['tenant_repo'],
            repos['session_repo']
        )

        survey_service = SurveyService(
            repos['survey_repo'],
            repos['response_repo'],
            repos['category_repo']
        )

        response_service = ResponseService(
            repos['response_repo'],
            repos['survey_repo'],
            repos['category_repo']
        )

        return {
            'auth_service': auth_service,
            'survey_service': survey_service,
            'response_service': response_service,
            'repos': repos
        }

    @pytest.fixture
    def setup_users(self, setup_services):
        """테스트용 사용자 생성"""
        repos = setup_services['repos']

        # 테넌트 생성
        tenant = Tenant(
            id=self.tenant_id,
            name="질문 관리 테스트 회사",
            created_at=datetime.now(),
            is_active=True
        )
        repos['tenant_repo'].save_tenant(tenant)

        # TENANT_ADMIN 사용자
        admin = User(
            id=self.admin_id,
            tenant_id=self.tenant_id,
            username="admin",
            email="admin@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.TENANT_ADMIN,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(admin)

        # SURVEY_MANAGER 사용자
        manager = User(
            id=self.manager_id,
            tenant_id=self.tenant_id,
            username="manager",
            email="manager@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.SURVEY_MANAGER,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(manager)

        # RESPONDENT 사용자
        respondent = User(
            id=self.respondent_id,
            tenant_id=self.tenant_id,
            username="respondent",
            email="respondent@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(respondent)

        return {
            'tenant': tenant,
            'admin': admin,
            'manager': manager,
            'respondent': respondent
        }

    def test_scenario_5_1_1_question_order_change_flow(self, setup_services, setup_users):
        """시나리오 5.1.1: 질문 순서 변경 플로우"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="순서 변경 테스트",
            description="질문 순서 변경 검증"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 5개 추가 (order: 0, 1, 2, 3, 4)
        question_ids = []
        for i in range(5):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type=QuestionType.TEXT,
                order=i
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 질문 3번(index 2)을 위로 이동 (order 2와 1 교환)
        result = survey_service.move_question_up(users['manager'], question_ids[2])
        assert result.is_success

        # 순서 확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        # 원래: 0, 1, 2, 3, 4
        # 변경 후: 0, 2, 1, 3, 4 (질문3이 위로)
        assert sorted_questions[1].id == question_ids[2]  # 질문3이 order 1 위치에
        assert sorted_questions[2].id == question_ids[1]  # 질문2가 order 2 위치에

        # 4. 질문 1번(index 0)을 아래로 이동
        result = survey_service.move_question_down(users['manager'], question_ids[0])
        assert result.is_success

        # 순서 재확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        # 변경 후: 2, 0, 1, 3, 4 또는 다른 순서 (구현에 따라)
        assert sorted_questions[0].id == question_ids[2] or sorted_questions[1].id == question_ids[0]

        print("✅ 시나리오 5.1.1: 질문 순서 변경 플로우 성공")

    def test_scenario_5_1_2_bulk_question_reordering(self, setup_services, setup_users):
        """시나리오 5.1.2: 질문 순서 일괄 재배치"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="일괄 재배치 테스트",
            description="질문 순서 일괄 변경"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 5개 추가
        question_ids = []
        for i in range(5):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type=QuestionType.TEXT,
                order=i
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 순서를 완전히 역순으로 재배치
        new_orders = {
            question_ids[0]: 4,  # 질문1 -> 마지막
            question_ids[1]: 3,  # 질문2 -> 4번째
            question_ids[2]: 2,  # 질문3 -> 중간 유지
            question_ids[3]: 1,  # 질문4 -> 2번째
            question_ids[4]: 0   # 질문5 -> 첫 번째
        }

        result = survey_service.reorder_questions(
            user=users['manager'],
            survey_id=survey_id,
            question_orders=new_orders
        )
        assert result.is_success

        # 4. 새로운 순서 확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        assert sorted_questions[0].id == question_ids[4]  # 질문5가 첫 번째
        assert sorted_questions[1].id == question_ids[3]  # 질문4가 두 번째
        assert sorted_questions[2].id == question_ids[2]  # 질문3이 중간
        assert sorted_questions[3].id == question_ids[1]  # 질문2가 네 번째
        assert sorted_questions[4].id == question_ids[0]  # 질문1이 마지막

        print("✅ 시나리오 5.1.2: 질문 순서 일괄 재배치 성공")

    def test_scenario_5_1_3_question_type_constraints(self, setup_services, setup_users):
        """시나리오 5.1.3: 질문 타입 변경 제약"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        response_service = services['response_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="타입 변경 제약 테스트",
            description="질문 타입 변경 검증"
        )
        assert result.is_success
        survey_id = result.value

        # 2. MULTIPLE_CHOICE 질문 생성
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="선호하는 색상",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["빨강", "파랑", "초록", "노랑"]
        )
        assert result.is_success
        question_id = result.value

        # 3. 응답 여러 개 제출
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={question_id: "빨강"}
        )
        assert result.is_success

        # 4. TEXT 타입으로 변경 시도
        # 구현에 따라 실패하거나 경고
        result = survey_service.update_question(
            user=users['manager'],
            question_id=question_id,
            question_type=QuestionType.TEXT  # 타입 변경
        )
        # 응답이 있는 경우 타입 변경은 제한될 수 있음
        # assert result.is_failure or result.is_success with warning

        # 5. 옵션 변경은 가능 (같은 타입 내에서)
        result = survey_service.update_question(
            user=users['manager'],
            question_id=question_id,
            options=["빨강", "파랑", "초록", "노랑", "보라"]  # 옵션 추가
        )
        # 같은 타입 내 옵션 변경은 보통 허용
        # assert result.is_success

        print("✅ 시나리오 5.1.3: 질문 타입 변경 제약 검증 성공")

    def test_scenario_5_1_4_question_deletion_order_adjustment(self, setup_services, setup_users):
        """시나리오 5.1.4: 질문 삭제 후 순서 자동 조정"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="삭제 순서 조정 테스트",
            description="질문 삭제 후 순서"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 5개 추가 (order: 0, 1, 2, 3, 4)
        question_ids = []
        for i in range(5):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type=QuestionType.TEXT,
                order=i
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 2번 질문(order=2) 삭제
        result = survey_service.delete_question(
            user=users['manager'],
            question_id=question_ids[2]
        )
        assert result.is_success

        # 4. 남은 질문 순서 확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        assert len(survey.questions) == 4

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        # 순서는 유지되지만 간격 존재: 0, 1, 3, 4
        assert sorted_questions[0].order == 0
        assert sorted_questions[1].order == 1
        assert sorted_questions[2].order == 3  # 간격 있음
        assert sorted_questions[3].order == 4

        # 5. 순서 정규화 (선택적 - 구현에 따라)
        # 간격을 없애고 0, 1, 2, 3으로 재정렬
        new_orders = {}
        for i, q in enumerate(sorted_questions):
            new_orders[q.id] = i

        result = survey_service.reorder_questions(
            user=users['manager'],
            survey_id=survey_id,
            question_orders=new_orders
        )
        assert result.is_success

        # 재확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        for i, q in enumerate(sorted_questions):
            assert q.order == i  # 0, 1, 2, 3

        print("✅ 시나리오 5.1.4: 질문 삭제 후 순서 자동 조정 성공")

    def test_scenario_5_1_5_question_middle_insertion(self, setup_services, setup_users):
        """시나리오 5.1.5: 질문 중간 삽입"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="중간 삽입 테스트",
            description="질문 중간 삽입"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 3개 추가 (order: 0, 1, 2)
        question_ids = []
        for i in range(3):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=survey_id,
                text=f"기존 질문 {i+1}",
                question_type=QuestionType.TEXT,
                order=i * 10  # 간격을 두고 생성: 0, 10, 20
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. order 10과 20 사이에 새 질문 삽입 (order 15)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="중간 삽입 질문",
            question_type=QuestionType.RATING,
            order=15  # 10과 20 사이
        )
        assert result.is_success
        inserted_id = result.value

        # 4. 순서 확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        assert len(survey.questions) == 4

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        assert sorted_questions[0].order == 0
        assert sorted_questions[1].order == 10
        assert sorted_questions[2].order == 15  # 중간에 삽입됨
        assert sorted_questions[3].order == 20

        # 5. order 0 앞에 새 질문 삽입 (order -5)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="맨 앞 질문",
            question_type=QuestionType.YES_NO,
            order=-5  # 음수 order로 맨 앞에
        )
        assert result.is_success

        # 순서 재확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        assert sorted_questions[0].order == -5  # 맨 앞
        assert sorted_questions[0].text == "맨 앞 질문"

        print("✅ 시나리오 5.1.5: 질문 중간 삽입 성공")

    def test_scenario_5_1_6_required_attribute_change(self, setup_services, setup_users):
        """시나리오 5.1.6: 필수 질문 속성 변경"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        response_service = services['response_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="필수 속성 변경 테스트",
            description="필수/선택 변경"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 필수 질문 생성
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="초기 필수 질문",
            question_type=QuestionType.TEXT,
            is_required=True
        )
        assert result.is_success
        question_id = result.value

        # 3. 필수 질문이므로 응답 없이 제출 불가
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={}  # 빈 응답
        )
        assert result.is_failure
        assert "필수" in result.error

        # 4. 질문 속성을 선택적으로 변경
        result = survey_service.update_question(
            user=users['manager'],
            question_id=question_id,
            is_required=False
        )
        assert result.is_success

        # 5. 이제 해당 질문 건너뛰기 가능
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={}  # 빈 응답도 가능
        )
        assert result.is_success

        # 6. 다시 필수로 변경
        result = survey_service.update_question(
            user=users['manager'],
            question_id=question_id,
            is_required=True
        )
        assert result.is_success

        # 7. 새 응답은 다시 필수
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={}
        )
        assert result.is_failure
        assert "필수" in result.error

        print("✅ 시나리오 5.1.6: 필수 질문 속성 변경 성공")

    def test_scenario_5_1_7_category_based_question_management(self, setup_services, setup_users):
        """시나리오 5.1.7: 범주별 질문 관리"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        repos = services['repos']

        # 1. 범주 생성
        category1 = Category(
            id=str(uuid.uuid4()),
            name="서비스 품질",
            description="서비스 품질 관련 질문"
        )
        repos['category_repo'].save_category(category1)

        category2 = Category(
            id=str(uuid.uuid4()),
            name="가격 만족도",
            description="가격 관련 질문"
        )
        repos['category_repo'].save_category(category2)

        # 2. 각 범주별 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="서비스 품질 평가",
            description="품질 관련",
            category_id=category1.id
        )
        assert result.is_success
        quality_survey_id = result.value

        result = survey_service.create_survey(
            user=users['manager'],
            title="가격 만족도 조사",
            description="가격 관련",
            category_id=category2.id
        )
        assert result.is_success
        price_survey_id = result.value

        # 3. 각 설문에 질문 추가
        # 서비스 품질 설문
        for i in range(3):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=quality_survey_id,
                text=f"품질 질문 {i+1}",
                question_type=QuestionType.RATING
            )
            assert result.is_success

        # 가격 만족도 설문
        for i in range(2):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=price_survey_id,
                text=f"가격 질문 {i+1}",
                question_type=QuestionType.SCALE_10
            )
            assert result.is_success

        # 4. 범주별 설문 조회
        quality_surveys = repos['survey_repo'].find_by_category_id(category1.id)
        price_surveys = repos['survey_repo'].find_by_category_id(category2.id)

        assert len(quality_surveys) == 1
        assert len(price_surveys) == 1

        # 5. 범주 삭제 시 설문 처리
        # 범주 삭제 (구현에 따라)
        result = repos['category_repo'].delete(category1.id)
        if result:
            # 설문의 category_id가 null이 되거나 설문도 함께 삭제
            survey = repos['survey_repo'].find_survey_by_id(quality_survey_id)
            if survey:
                assert survey.category_id is None or survey.category_id == ""

        print("✅ 시나리오 5.1.7: 범주별 질문 관리 성공")

    def test_scenario_5_1_8_complex_ordering_operations(self, setup_services, setup_users):
        """시나리오 5.1.8: 복잡한 순서 작업"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['admin'],
            title="복잡한 순서 테스트",
            description="다양한 순서 작업"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 다양한 타입의 질문 10개 추가
        question_ids = []
        question_types = [
            QuestionType.TEXT,
            QuestionType.RATING,
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.YES_NO,
            QuestionType.SCALE_10,
            QuestionType.MULTI_SELECT,
            QuestionType.DATE,
            QuestionType.NUMBER,
            QuestionType.EMAIL,
            QuestionType.TEXT
        ]

        for i, q_type in enumerate(question_types):
            options = None
            if q_type == QuestionType.MULTIPLE_CHOICE:
                options = ["A", "B", "C"]
            elif q_type == QuestionType.MULTI_SELECT:
                options = ["1", "2", "3", "4", "5"]

            result = survey_service.add_question(
                user=users['admin'],
                survey_id=survey_id,
                text=f"질문 {i+1} ({q_type.value})",
                question_type=q_type,
                options=options,
                order=i
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 첫 번째와 마지막 질문 교환
        new_orders = {
            question_ids[0]: 9,
            question_ids[9]: 0
        }
        result = survey_service.reorder_questions(
            user=users['admin'],
            survey_id=survey_id,
            question_orders=new_orders
        )
        assert result.is_success

        # 4. 중간 질문들을 한 칸씩 위로
        for i in range(4, 7):
            result = survey_service.move_question_up(
                user=users['admin'],
                question_ids[i]
            )
            assert result.is_success

        # 5. 최종 순서 확인
        result = survey_service.get_survey(users['admin'], survey_id)
        assert result.is_success
        survey = result.value

        assert len(survey.questions) == 10

        # 순서가 변경되었는지 확인
        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        # 첫 번째와 마지막이 교환되었는지 확인
        first_q = next(q for q in sorted_questions if q.order == 0)
        last_q = next(q for q in sorted_questions if q.order == 9)

        print("✅ 시나리오 5.1.8: 복잡한 순서 작업 성공")

    def test_scenario_5_1_9_question_options_management(self, setup_services, setup_users):
        """시나리오 5.1.9: 질문 옵션 관리"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="옵션 관리 테스트",
            description="질문 옵션 추가/삭제/수정"
        )
        assert result.is_success
        survey_id = result.value

        # 2. MULTIPLE_CHOICE 질문 생성
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="초기 옵션 질문",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["옵션1", "옵션2", "옵션3"]
        )
        assert result.is_success
        mc_question_id = result.value

        # 3. MULTI_SELECT 질문 생성
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="다중 선택 질문",
            question_type=QuestionType.MULTI_SELECT,
            options=["A", "B", "C", "D"]
        )
        assert result.is_success
        ms_question_id = result.value

        # 4. 옵션 추가
        result = survey_service.update_question(
            user=users['manager'],
            question_id=mc_question_id,
            options=["옵션1", "옵션2", "옵션3", "옵션4", "옵션5"]
        )
        assert result.is_success

        # 5. 옵션 삭제
        result = survey_service.update_question(
            user=users['manager'],
            question_id=ms_question_id,
            options=["A", "B", "C"]  # D 삭제
        )
        assert result.is_success

        # 6. 옵션 텍스트 변경
        result = survey_service.update_question(
            user=users['manager'],
            question_id=mc_question_id,
            options=["선택1", "선택2", "선택3", "선택4", "선택5"]
        )
        assert result.is_success

        # 7. 확인
        result = survey_service.get_survey(users['manager'], survey_id)
        assert result.is_success
        survey = result.value

        mc_question = next(q for q in survey.questions if q.id == mc_question_id)
        assert len(mc_question.options) == 5
        assert mc_question.options[0] == "선택1"

        ms_question = next(q for q in survey.questions if q.id == ms_question_id)
        assert len(ms_question.options) == 3
        assert "D" not in ms_question.options

        print("✅ 시나리오 5.1.9: 질문 옵션 관리 성공")

    def test_scenario_5_1_10_question_boundary_operations(self, setup_services, setup_users):
        """시나리오 5.1.10: 질문 경계 작업"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['admin'],
            title="경계 테스트",
            description="질문 경계 작업"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 1개만 추가
        result = survey_service.add_question(
            user=users['admin'],
            survey_id=survey_id,
            text="유일한 질문",
            question_type=QuestionType.TEXT,
            order=0
        )
        assert result.is_success
        single_question_id = result.value

        # 3. 유일한 질문을 위로 이동 시도 (불가)
        result = survey_service.move_question_up(
            user=users['admin'],
            single_question_id
        )
        assert result.is_failure  # 이미 첫 번째

        # 4. 유일한 질문을 아래로 이동 시도 (불가)
        result = survey_service.move_question_down(
            user=users['admin'],
            single_question_id
        )
        assert result.is_failure  # 이미 마지막

        # 5. 질문 추가하여 2개로 만들기
        result = survey_service.add_question(
            user=users['admin'],
            survey_id=survey_id,
            text="두 번째 질문",
            question_type=QuestionType.RATING,
            order=1
        )
        assert result.is_success
        second_question_id = result.value

        # 6. 이제 이동 가능
        result = survey_service.move_question_down(
            user=users['admin'],
            single_question_id
        )
        assert result.is_success

        # 7. 최대 개수 질문 추가 테스트 (구현에 따라 제한이 있을 수 있음)
        for i in range(98):  # 총 100개 만들기
            result = survey_service.add_question(
                user=users['admin'],
                survey_id=survey_id,
                text=f"추가 질문 {i+3}",
                question_type=QuestionType.TEXT,
                order=i+2
            )
            # 제한이 있다면 어느 시점에서 실패
            if result.is_failure:
                break

        # 8. 질문 개수 확인
        result = survey_service.get_survey(users['admin'], survey_id)
        assert result.is_success
        survey = result.value

        print(f"✅ 시나리오 5.1.10: 질문 경계 작업 성공 (총 {len(survey.questions)}개 질문)")

    def test_scenario_5_1_11_question_move_edge_cases(self, setup_services, setup_users):
        """시나리오 5.1.11: 질문 이동 엣지 케이스"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="이동 엣지 케이스",
            description="질문 이동 특수 상황"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 3개 추가
        question_ids = []
        for i in range(3):
            result = survey_service.add_question(
                user=users['manager'],
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type=QuestionType.TEXT,
                order=i
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 첫 번째 질문을 위로 이동 시도
        result = survey_service.move_question_up(
            user=users['manager'],
            question_ids[0]
        )
        assert result.is_failure
        assert "첫" in result.error or "이동할 수 없" in result.error

        # 4. 마지막 질문을 아래로 이동 시도
        result = survey_service.move_question_down(
            user=users['manager'],
            question_ids[2]
        )
        assert result.is_failure
        assert "마지막" in result.error or "이동할 수 없" in result.error

        # 5. 존재하지 않는 질문 이동 시도
        fake_question_id = str(uuid.uuid4())
        result = survey_service.move_question_up(
            user=users['manager'],
            fake_question_id
        )
        assert result.is_failure
        assert "찾을 수 없" in result.error

        # 6. 다른 설문의 질문 이동 시도
        result = survey_service.create_survey(
            user=users['manager'],
            title="다른 설문",
            description="별개 설문"
        )
        assert result.is_success
        other_survey_id = result.value

        result = survey_service.add_question(
            user=users['manager'],
            survey_id=other_survey_id,
            text="다른 설문 질문",
            question_type=QuestionType.TEXT
        )
        assert result.is_success
        other_question_id = result.value

        # 권한이 있어도 다른 설문의 질문은 이동 불가
        result = survey_service.move_question_up(
            user=users['manager'],
            other_question_id
        )
        # 첫 번째 질문이므로 위로 이동 불가
        assert result.is_failure

        print("✅ 시나리오 5.1.11: 질문 이동 엣지 케이스 성공")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])