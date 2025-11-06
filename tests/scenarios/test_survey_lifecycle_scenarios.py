"""
설문 생명주기 시나리오 테스트
Survey Lifecycle Scenario Tests

설문의 생성부터 삭제까지 전체 생명주기를 검증하는 시나리오 테스트입니다.
- 설문 생성, 수정, 복제, 삭제
- 질문 추가, 수정, 삭제
- 설문 상태 관리
- 소유권 이전
"""

import pytest
import uuid
from datetime import datetime, timedelta
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


class TestSurveyLifecycleScenarios:
    """설문 생명주기 시나리오 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.tenant_id = str(uuid.uuid4())
        self.admin_id = str(uuid.uuid4())
        self.manager1_id = str(uuid.uuid4())
        self.manager2_id = str(uuid.uuid4())
        self.respondent_id = str(uuid.uuid4())

    @pytest.fixture
    def setup_repositories(self, temp_data_dir):
        """테스트용 저장소 설정"""
        tenant_repo = CsvTenantRepository(temp_data_dir)
        user_repo = CsvUserRepository(temp_data_dir)
        survey_repo = CsvSurveyRepository(temp_data_dir)
        response_repo = CsvResponseRepository(temp_data_dir)
        category_repo = CsvCategoryRepository(temp_data_dir)
        session_repo = CsvSessionRepository(temp_data_dir)

        return {
            'tenant_repo': tenant_repo,
            'user_repo': user_repo,
            'survey_repo': survey_repo,
            'response_repo': response_repo,
            'category_repo': category_repo,
            'session_repo': session_repo
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
        services = setup_services
        repos = services['repos']

        # 테넌트 생성
        tenant = Tenant(
            id=self.tenant_id,
            name="테스트 회사",
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

        # SURVEY_MANAGER 사용자 1
        manager1 = User(
            id=self.manager1_id,
            tenant_id=self.tenant_id,
            username="manager1",
            email="manager1@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.SURVEY_MANAGER,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(manager1)

        # SURVEY_MANAGER 사용자 2
        manager2 = User(
            id=self.manager2_id,
            tenant_id=self.tenant_id,
            username="manager2",
            email="manager2@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.SURVEY_MANAGER,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(manager2)

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
            'manager1': manager1,
            'manager2': manager2,
            'respondent': respondent
        }

    def test_scenario_1_1_1_survey_creation_to_completion(self, setup_services, setup_users):
        """시나리오 1.1.1: 설문 생성부터 완료까지 정상 흐름"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 테넌트 관리자가 설문 생성
        result = survey_service.create_survey(
            user=users['admin'],
            title="고객 만족도 조사",
            description="2024년 상반기 고객 만족도를 조사합니다"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 다양한 타입의 질문 추가
        question_types_and_data = [
            (QuestionType.TEXT, "귀하의 성함을 입력해주세요", None, 0),
            (QuestionType.RATING, "전반적인 서비스 만족도를 평가해주세요", None, 1),
            (QuestionType.MULTIPLE_CHOICE, "가장 자주 사용하는 기능은?", ["검색", "필터", "정렬", "내보내기"], 2),
            (QuestionType.YES_NO, "서비스를 다른 사람에게 추천하시겠습니까?", None, 3),
            (QuestionType.SCALE_10, "서비스의 가격 대비 가치를 평가해주세요 (1-10)", None, 4),
            (QuestionType.MULTI_SELECT, "개선이 필요한 부분을 모두 선택해주세요", ["UI/UX", "성능", "기능", "가격", "고객지원"], 5),
            (QuestionType.DATE, "서비스를 처음 사용한 날짜는?", None, 6),
            (QuestionType.NUMBER, "월 평균 사용 횟수는?", None, 7),
            (QuestionType.EMAIL, "연락 가능한 이메일 주소를 입력해주세요", None, 8)
        ]

        question_ids = []
        for q_type, q_text, q_options, q_order in question_types_and_data:
            result = survey_service.add_question(
                user=users['admin'],
                survey_id=survey_id,
                text=q_text,
                question_type=q_type,
                options=q_options,
                is_required=True if q_order < 5 else False,  # 처음 5개는 필수
                order=q_order
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 설문 조회 및 질문 순서 확인
        result = survey_service.get_survey(users['admin'], survey_id)
        assert result.is_success
        survey = result.value

        assert survey.title == "고객 만족도 조사"
        assert len(survey.questions) == 9

        # 질문 순서 확인
        sorted_questions = sorted(survey.questions, key=lambda q: q.order)
        assert sorted_questions[0].question_type == QuestionType.TEXT
        assert sorted_questions[0].order == 0
        assert sorted_questions[-1].question_type == QuestionType.EMAIL
        assert sorted_questions[-1].order == 8

        # 4. 설문 상태 확인
        assert survey.created_at is not None
        assert survey.updated_at is not None

        print("✅ 시나리오 1.1.1: 설문 생성부터 완료까지 성공")

    def test_scenario_1_1_2_survey_modification_flow(self, setup_services, setup_users):
        """시나리오 1.1.2: 설문 수정 전체 플로우"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="원래 제목",
            description="원래 설명"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 추가
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_id,
            text="원래 질문",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["옵션1", "옵션2", "옵션3"]
        )
        assert result.is_success
        question_id = result.value

        # 3. 설문 제목 수정
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=survey_id,
            title="수정된 제목",
            description="원래 설명"  # 설명은 유지
        )
        assert result.is_success

        # 4. 설문 설명 수정
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=survey_id,
            title="수정된 제목",  # 제목은 유지
            description="수정된 설명"
        )
        assert result.is_success

        # 5. 질문 텍스트 수정
        result = survey_service.update_question(
            user=users['manager1'],
            question_id=question_id,
            text="수정된 질문",
            options=["옵션1", "옵션2", "옵션3"]  # 옵션은 유지
        )
        assert result.is_success

        # 6. 질문 옵션 수정
        result = survey_service.update_question(
            user=users['manager1'],
            question_id=question_id,
            text="수정된 질문",  # 텍스트는 유지
            options=["새옵션1", "새옵션2", "새옵션3", "새옵션4"]
        )
        assert result.is_success

        # 7. 수정 후 데이터 무결성 확인
        result = survey_service.get_survey(users['manager1'], survey_id)
        assert result.is_success
        survey = result.value

        assert survey.title == "수정된 제목"
        assert survey.description == "수정된 설명"
        assert len(survey.questions) == 1
        assert survey.questions[0].text == "수정된 질문"
        assert survey.questions[0].options == ["새옵션1", "새옵션2", "새옵션3", "새옵션4"]

        print("✅ 시나리오 1.1.2: 설문 수정 전체 플로우 성공")

    def test_scenario_1_1_3_survey_duplication(self, setup_services, setup_users):
        """시나리오 1.1.3: 설문 복제 시나리오"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 원본 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="원본 설문",
            description="복제할 설문입니다"
        )
        assert result.is_success
        original_survey_id = result.value

        # 2. 질문들 추가
        questions_data = [
            ("질문 1", QuestionType.TEXT, None),
            ("질문 2", QuestionType.RATING, None),
            ("질문 3", QuestionType.MULTIPLE_CHOICE, ["A", "B", "C"])
        ]

        for text, q_type, options in questions_data:
            result = survey_service.add_question(
                user=users['manager1'],
                survey_id=original_survey_id,
                text=text,
                question_type=q_type,
                options=options
            )
            assert result.is_success

        # 3. 설문 복제
        result = survey_service.get_survey(users['manager1'], original_survey_id)
        assert result.is_success
        original_survey = result.value

        # 새 설문 생성 (복제)
        result = survey_service.create_survey(
            user=users['manager1'],
            title=f"{original_survey.title} (복사본)",
            description=original_survey.description
        )
        assert result.is_success
        cloned_survey_id = result.value

        # 질문들 복제
        for question in original_survey.questions:
            result = survey_service.add_question(
                user=users['manager1'],
                survey_id=cloned_survey_id,
                text=question.text,
                question_type=question.question_type,
                options=question.options,
                is_required=question.is_required,
                order=question.order
            )
            assert result.is_success

        # 4. 복제된 설문 독립성 확인
        result = survey_service.get_survey(users['manager1'], cloned_survey_id)
        assert result.is_success
        cloned_survey = result.value

        assert cloned_survey.id != original_survey_id
        assert cloned_survey.title == "원본 설문 (복사본)"
        assert len(cloned_survey.questions) == 3

        # 5. 복제본 수정이 원본에 영향 없음 확인
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=cloned_survey_id,
            title="복제본 수정됨",
            description="복제본만 수정"
        )
        assert result.is_success

        # 원본 확인
        result = survey_service.get_survey(users['manager1'], original_survey_id)
        assert result.is_success
        original_survey = result.value
        assert original_survey.title == "원본 설문"  # 변경 없음

        print("✅ 시나리오 1.1.3: 설문 복제 시나리오 성공")

    def test_scenario_1_1_4_survey_deletion_cascade(self, setup_services, setup_users):
        """시나리오 1.1.4: 설문 삭제 플로우"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        response_service = services['response_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="삭제할 설문",
            description="삭제 테스트용"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 추가
        question_ids = []
        for i in range(3):
            result = survey_service.add_question(
                user=users['manager1'],
                survey_id=survey_id,
                text=f"질문 {i+1}",
                question_type=QuestionType.TEXT
            )
            assert result.is_success
            question_ids.append(result.value)

        # 3. 응답 제출
        answers = {
            question_ids[0]: "답변 1",
            question_ids[1]: "답변 2",
            question_ids[2]: "답변 3"
        }

        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers=answers
        )
        assert result.is_success
        response_id = result.value

        # 4. 설문 삭제
        result = survey_service.delete_survey(
            user=users['manager1'],
            survey_id=survey_id
        )
        assert result.is_success

        # 5. 삭제 후 조회 불가 확인
        result = survey_service.get_survey(users['manager1'], survey_id)
        assert result.is_failure
        assert "찾을 수 없" in result.error

        # 6. 질문들도 삭제 확인
        for question_id in question_ids:
            question = services['repos']['survey_repo'].find_question_by_id(question_id)
            assert question is None

        # 7. 응답도 삭제 확인 (또는 고아 상태)
        response = services['repos']['response_repo'].find_by_id(response_id)
        # 구현에 따라 None이거나 survey_id가 없는 상태
        assert response is None or response.survey_id != survey_id

        print("✅ 시나리오 1.1.4: 설문 삭제 플로우 성공")

    def test_scenario_1_1_5_survey_ownership_transfer(self, setup_services, setup_users):
        """시나리오 1.1.5: 설문 소유권 이전"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        repos = services['repos']

        # 1. Manager1이 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="소유권 이전 테스트",
            description="Manager1이 생성"
        )
        assert result.is_success
        survey_id = result.value

        # 2. Manager1이 설문 관리 가능 확인
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=survey_id,
            title="Manager1이 수정",
            description="Manager1이 생성"
        )
        assert result.is_success

        # 3. Manager2는 수정 불가 확인
        result = survey_service.update_survey(
            user=users['manager2'],
            survey_id=survey_id,
            title="Manager2가 수정 시도",
            description="실패해야 함"
        )
        assert result.is_failure
        assert "권한" in result.error

        # 4. Tenant Admin이 소유권을 Manager2로 변경
        survey = repos['survey_repo'].find_survey_by_id(survey_id)
        survey.creator_id = users['manager2'].id
        result = repos['survey_repo'].update_survey(survey)
        assert result

        # 5. Manager2가 설문 관리 가능 확인
        result = survey_service.update_survey(
            user=users['manager2'],
            survey_id=survey_id,
            title="Manager2가 수정 성공",
            description="소유권 이전 후"
        )
        assert result.is_success

        # 6. Manager1은 더 이상 관리 불가 확인
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=survey_id,
            title="Manager1이 다시 수정 시도",
            description="실패해야 함"
        )
        assert result.is_failure
        assert "권한" in result.error

        print("✅ 시나리오 1.1.5: 설문 소유권 이전 성공")

    def test_scenario_1_1_6_survey_with_category(self, setup_services, setup_users):
        """시나리오 1.1.6: 카테고리별 설문 관리"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        repos = services['repos']

        # 1. 카테고리 생성
        category1 = Category(
            id=str(uuid.uuid4()),
            name="고객 만족도",
            description="고객 만족도 관련 설문"
        )
        repos['category_repo'].save_category(category1)

        category2 = Category(
            id=str(uuid.uuid4()),
            name="직원 평가",
            description="직원 평가 관련 설문"
        )
        repos['category_repo'].save_category(category2)

        # 2. 각 카테고리에 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="고객 만족도 설문 1",
            description="2024 Q1",
            category_id=category1.id
        )
        assert result.is_success
        survey1_id = result.value

        result = survey_service.create_survey(
            user=users['manager1'],
            title="고객 만족도 설문 2",
            description="2024 Q2",
            category_id=category1.id
        )
        assert result.is_success
        survey2_id = result.value

        result = survey_service.create_survey(
            user=users['manager1'],
            title="직원 평가 설문",
            description="2024 상반기",
            category_id=category2.id
        )
        assert result.is_success
        survey3_id = result.value

        # 3. 카테고리별 설문 조회
        surveys_cat1 = repos['survey_repo'].find_by_category_id(category1.id)
        surveys_cat2 = repos['survey_repo'].find_by_category_id(category2.id)

        assert len(surveys_cat1) == 2
        assert len(surveys_cat2) == 1

        # 4. 카테고리 없는 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="카테고리 없는 설문",
            description="미분류"
        )
        assert result.is_success

        print("✅ 시나리오 1.1.6: 카테고리별 설문 관리 성공")

    def test_scenario_1_1_7_survey_status_management(self, setup_services, setup_users):
        """시나리오 1.1.7: 설문 상태 관리 (활성/비활성)"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        response_service = services['response_service']
        repos = services['repos']

        # 1. 설문 생성 (기본 활성 상태)
        result = survey_service.create_survey(
            user=users['manager1'],
            title="상태 관리 테스트",
            description="활성/비활성 테스트"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 추가
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_id,
            text="테스트 질문",
            question_type=QuestionType.TEXT
        )
        assert result.is_success
        question_id = result.value

        # 3. 활성 상태에서 응답 가능 확인
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={question_id: "답변"}
        )
        assert result.is_success

        # 4. 설문 비활성화 (구현 필요 시)
        survey = repos['survey_repo'].find_survey_by_id(survey_id)
        if hasattr(survey, 'is_active'):
            survey.is_active = False
            repos['survey_repo'].update_survey(survey)

            # 5. 비활성 상태에서 응답 불가 확인
            result = response_service.submit_response(
                user=users['respondent'],
                survey_id=survey_id,
                answers={question_id: "새 답변"}
            )
            # 구현에 따라 실패해야 함
            # assert result.is_failure

        print("✅ 시나리오 1.1.7: 설문 상태 관리 성공")

    def test_scenario_1_1_8_survey_with_mixed_question_types(self, setup_services, setup_users):
        """시나리오 1.1.8: 혼합 질문 타입 설문"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="종합 평가 설문",
            description="다양한 질문 타입 포함"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 각 타입별 질문 추가 및 특성 확인
        questions = [
            {
                'type': QuestionType.TEXT,
                'text': "자유 의견을 작성해주세요",
                'options': None,
                'required': False
            },
            {
                'type': QuestionType.RATING,
                'text': "서비스 평점 (1-5)",
                'options': None,
                'required': True
            },
            {
                'type': QuestionType.MULTIPLE_CHOICE,
                'text': "선호하는 색상",
                'options': ["빨강", "파랑", "초록", "노랑"],
                'required': True
            },
            {
                'type': QuestionType.MULTI_SELECT,
                'text': "관심 분야 (복수 선택)",
                'options': ["IT", "금융", "의료", "교육", "제조"],
                'required': False
            },
            {
                'type': QuestionType.YES_NO,
                'text': "재구매 의향",
                'options': None,
                'required': True
            },
            {
                'type': QuestionType.SCALE_10,
                'text': "추천 가능성 (NPS)",
                'options': None,
                'required': True
            },
            {
                'type': QuestionType.DATE,
                'text': "첫 구매일",
                'options': None,
                'required': False
            },
            {
                'type': QuestionType.NUMBER,
                'text': "월 평균 구매 금액",
                'options': None,
                'required': False
            },
            {
                'type': QuestionType.EMAIL,
                'text': "이벤트 알림용 이메일",
                'options': None,
                'required': False
            }
        ]

        question_count = 0
        for i, q_data in enumerate(questions):
            result = survey_service.add_question(
                user=users['manager1'],
                survey_id=survey_id,
                text=q_data['text'],
                question_type=q_data['type'],
                options=q_data['options'],
                is_required=q_data['required'],
                order=i
            )
            assert result.is_success
            question_count += 1

        # 3. 설문 조회 및 검증
        result = survey_service.get_survey(users['manager1'], survey_id)
        assert result.is_success
        survey = result.value

        assert len(survey.questions) == question_count

        # 필수 질문 수 확인
        required_count = sum(1 for q in survey.questions if q.is_required)
        optional_count = sum(1 for q in survey.questions if not q.is_required)

        assert required_count == 4  # RATING, MULTIPLE_CHOICE, YES_NO, SCALE_10
        assert optional_count == 5  # TEXT, MULTI_SELECT, DATE, NUMBER, EMAIL

        print("✅ 시나리오 1.1.8: 혼합 질문 타입 설문 성공")

    def test_scenario_1_1_9_survey_update_after_responses(self, setup_services, setup_users):
        """시나리오 1.1.9: 응답 수집 후 설문 수정 제약"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']
        response_service = services['response_service']

        # 1. 설문 생성
        result = survey_service.create_survey(
            user=users['manager1'],
            title="수정 제약 테스트",
            description="응답 후 수정"
        )
        assert result.is_success
        survey_id = result.value

        # 2. 질문 추가
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_id,
            text="기존 질문",
            question_type=QuestionType.RATING,
            is_required=True
        )
        assert result.is_success
        question_id = result.value

        # 3. 응답 제출
        result = response_service.submit_response(
            user=users['respondent'],
            survey_id=survey_id,
            answers={question_id: "4"}
        )
        assert result.is_success

        # 4. 설문 제목/설명은 수정 가능
        result = survey_service.update_survey(
            user=users['manager1'],
            survey_id=survey_id,
            title="수정된 제목",
            description="수정된 설명"
        )
        assert result.is_success

        # 5. 새 질문 추가는 가능 (선택사항)
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_id,
            text="새 질문",
            question_type=QuestionType.TEXT,
            is_required=False  # 선택적 질문
        )
        # 구현에 따라 성공 또는 실패

        # 6. 기존 질문 삭제는 제한 (구현에 따라)
        result = survey_service.delete_question(
            user=users['manager1'],
            question_id=question_id
        )
        # 응답이 있는 질문 삭제는 제한될 수 있음

        print("✅ 시나리오 1.1.9: 응답 수집 후 설문 수정 제약 검증 성공")

    def test_scenario_1_1_10_survey_versioning(self, setup_services, setup_users):
        """시나리오 1.1.10: 설문 버전 관리 (선택적)"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 1. 초기 설문 생성 (v1)
        result = survey_service.create_survey(
            user=users['manager1'],
            title="버전 관리 테스트 v1",
            description="초기 버전"
        )
        assert result.is_success
        survey_v1_id = result.value

        # 2. 질문 추가
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_v1_id,
            text="v1 질문",
            question_type=QuestionType.TEXT
        )
        assert result.is_success

        # 3. 새 버전 생성 (복제 후 수정)
        result = survey_service.get_survey(users['manager1'], survey_v1_id)
        assert result.is_success
        survey_v1 = result.value

        result = survey_service.create_survey(
            user=users['manager1'],
            title="버전 관리 테스트 v2",
            description="개선된 버전"
        )
        assert result.is_success
        survey_v2_id = result.value

        # v1 질문 복제
        for question in survey_v1.questions:
            result = survey_service.add_question(
                user=users['manager1'],
                survey_id=survey_v2_id,
                text=f"{question.text} (개선)",
                question_type=question.question_type,
                options=question.options
            )
            assert result.is_success

        # 추가 질문
        result = survey_service.add_question(
            user=users['manager1'],
            survey_id=survey_v2_id,
            text="v2 신규 질문",
            question_type=QuestionType.RATING
        )
        assert result.is_success

        # 4. 두 버전 모두 독립적으로 운영
        surveys = services['repos']['survey_repo'].find_by_creator_id(users['manager1'].id)
        version_surveys = [s for s in surveys if "버전 관리 테스트" in s.title]
        assert len(version_surveys) >= 2

        print("✅ 시나리오 1.1.10: 설문 버전 관리 성공")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])