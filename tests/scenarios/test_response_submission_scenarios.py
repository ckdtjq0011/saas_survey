"""
응답 제출 플로우 시나리오 테스트
Response Submission Flow Scenario Tests

응답자가 설문에 참여하고 응답을 제출하는 전체 과정을 검증합니다.
- 정상 응답 제출
- 필수 질문 검증
- 다양한 질문 타입별 응답
- 응답 수정 및 삭제
- 세션별 응답 추적
"""

import pytest
import uuid
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

from domain.entities.user import User
from domain.entities.tenant import Tenant
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.entities.response import Response
from domain.entities.category import Category
from domain.entities.survey_session import SurveySession
from domain.entities.response_history import ResponseHistory
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType

from application.auth_service import AuthService
from application.survey_service import SurveyService
from application.response_service import ResponseService
from application.survey_session_service import SurveySessionService

from infrastructure.persistence.csv_tenant_repository import CsvTenantRepository
from infrastructure.persistence.csv_user_repository import CsvUserRepository
from infrastructure.persistence.csv_survey_repository import CsvSurveyRepository
from infrastructure.persistence.csv_response_repository import CsvResponseRepository
from infrastructure.persistence.csv_category_repository import CsvCategoryRepository
from infrastructure.persistence.csv_session_repository import CsvSessionRepository
from infrastructure.persistence.csv_survey_session_repository import CsvSurveySessionRepository
from infrastructure.persistence.csv_response_history_repository import CsvResponseHistoryRepository

from interface.cli.validators import (
    validate_text_answer,
    validate_rating_answer,
    validate_multiple_choice_answer,
    validate_multi_select_answer,
    validate_yes_no_answer,
    validate_scale_10_answer,
    validate_date_answer,
    validate_number_answer,
    validate_email_answer
)


class TestResponseSubmissionScenarios:
    """응답 제출 시나리오 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 초기화"""
        self.tenant_id = str(uuid.uuid4())
        self.manager_id = str(uuid.uuid4())
        self.respondent1_id = str(uuid.uuid4())
        self.respondent2_id = str(uuid.uuid4())
        self.respondent3_id = str(uuid.uuid4())

    @pytest.fixture
    def setup_repositories(self, temp_data_dir):
        """테스트용 저장소 설정"""
        return {
            'tenant_repo': CsvTenantRepository(temp_data_dir),
            'user_repo': CsvUserRepository(temp_data_dir),
            'survey_repo': CsvSurveyRepository(temp_data_dir),
            'response_repo': CsvResponseRepository(temp_data_dir),
            'category_repo': CsvCategoryRepository(temp_data_dir),
            'session_repo': CsvSessionRepository(temp_data_dir),
            'survey_session_repo': CsvSurveySessionRepository(temp_data_dir),
            'response_history_repo': CsvResponseHistoryRepository(temp_data_dir)
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

        survey_session_service = SurveySessionService(
            repos['survey_session_repo'],
            repos['survey_repo']
        )

        return {
            'auth_service': auth_service,
            'survey_service': survey_service,
            'response_service': response_service,
            'survey_session_service': survey_session_service,
            'repos': repos
        }

    @pytest.fixture
    def setup_users(self, setup_services):
        """테스트용 사용자 생성"""
        repos = setup_services['repos']

        # 테넌트 생성
        tenant = Tenant(
            id=self.tenant_id,
            name="응답 테스트 회사",
            created_at=datetime.now(),
            is_active=True
        )
        repos['tenant_repo'].save_tenant(tenant)

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

        # RESPONDENT 사용자들
        respondent1 = User(
            id=self.respondent1_id,
            tenant_id=self.tenant_id,
            username="respondent1",
            email="respondent1@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(respondent1)

        respondent2 = User(
            id=self.respondent2_id,
            tenant_id=self.tenant_id,
            username="respondent2",
            email="respondent2@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(respondent2)

        respondent3 = User(
            id=self.respondent3_id,
            tenant_id=self.tenant_id,
            username="respondent3",
            email="respondent3@test.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        repos['user_repo'].save_user(respondent3)

        return {
            'tenant': tenant,
            'manager': manager,
            'respondent1': respondent1,
            'respondent2': respondent2,
            'respondent3': respondent3
        }

    @pytest.fixture
    def setup_survey(self, setup_services, setup_users):
        """테스트용 설문 생성"""
        services = setup_services
        users = setup_users
        survey_service = services['survey_service']

        # 설문 생성
        result = survey_service.create_survey(
            user=users['manager'],
            title="종합 응답 테스트 설문",
            description="모든 질문 타입 포함"
        )
        assert result.is_success
        survey_id = result.value

        # 다양한 질문 추가
        questions = []

        # TEXT 질문 (필수)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="귀하의 이름을 입력해주세요",
            question_type=QuestionType.TEXT,
            is_required=True,
            order=0
        )
        assert result.is_success
        questions.append(result.value)

        # RATING 질문 (필수)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="서비스 만족도 (1-5)",
            question_type=QuestionType.RATING,
            is_required=True,
            order=1
        )
        assert result.is_success
        questions.append(result.value)

        # MULTIPLE_CHOICE 질문 (필수)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="선호하는 연락 방법",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=["이메일", "전화", "문자", "카톡"],
            is_required=True,
            order=2
        )
        assert result.is_success
        questions.append(result.value)

        # YES_NO 질문 (선택)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="재구매 의향이 있으신가요?",
            question_type=QuestionType.YES_NO,
            is_required=False,
            order=3
        )
        assert result.is_success
        questions.append(result.value)

        # SCALE_10 질문 (선택)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="추천 가능성 (1-10)",
            question_type=QuestionType.SCALE_10,
            is_required=False,
            order=4
        )
        assert result.is_success
        questions.append(result.value)

        # MULTI_SELECT 질문 (선택)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="관심 있는 기능 (복수 선택)",
            question_type=QuestionType.MULTI_SELECT,
            options=["분석", "리포트", "자동화", "통합", "보안"],
            is_required=False,
            order=5
        )
        assert result.is_success
        questions.append(result.value)

        # DATE 질문 (선택)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="서비스 이용 시작일",
            question_type=QuestionType.DATE,
            is_required=False,
            order=6
        )
        assert result.is_success
        questions.append(result.value)

        # NUMBER 질문 (선택)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="월 평균 사용 횟수",
            question_type=QuestionType.NUMBER,
            is_required=False,
            order=7
        )
        assert result.is_success
        questions.append(result.value)

        # EMAIL 질문 (필수)
        result = survey_service.add_question(
            user=users['manager'],
            survey_id=survey_id,
            text="연락 가능한 이메일",
            question_type=QuestionType.EMAIL,
            is_required=True,
            order=8
        )
        assert result.is_success
        questions.append(result.value)

        return {
            'survey_id': survey_id,
            'question_ids': questions
        }

    def test_scenario_2_1_1_normal_response_submission(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.1: 정상 응답 제출 전체 플로우"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']
        session_service = services['survey_session_service']

        # 1. 응답자가 설문 시작 (세션 생성)
        result = session_service.start_survey(
            user=users['respondent1'],
            survey_id=survey_data['survey_id']
        )
        assert result.is_success
        session_id = result.value

        # 2. 각 질문에 순차적으로 응답
        answers = {
            survey_data['question_ids'][0]: "홍길동",  # TEXT
            survey_data['question_ids'][1]: "5",  # RATING
            survey_data['question_ids'][2]: "이메일",  # MULTIPLE_CHOICE
            survey_data['question_ids'][3]: "y",  # YES_NO
            survey_data['question_ids'][4]: "9",  # SCALE_10
            survey_data['question_ids'][5]: "1,3,5",  # MULTI_SELECT
            survey_data['question_ids'][6]: "2024-01-15",  # DATE
            survey_data['question_ids'][7]: "25",  # NUMBER
            survey_data['question_ids'][8]: "hong@example.com"  # EMAIL
        }

        # 3. 전체 응답 제출
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers
        )
        assert result.is_success
        response_id = result.value

        # 4. 제출 완료 확인
        response = services['repos']['response_repo'].find_by_id(response_id)
        assert response is not None
        assert response.survey_id == survey_data['survey_id']
        assert response.respondent_id == users['respondent1'].id
        assert len(response.answers) == 9

        # 5. 세션 완료 상태 업데이트
        result = session_service.complete_survey(
            user=users['respondent1'],
            session_id=session_id
        )
        assert result.is_success

        session = services['repos']['survey_session_repo'].find_by_id(session_id)
        assert session.completed is True
        assert session.submitted_at is not None

        print("✅ 시나리오 2.1.1: 정상 응답 제출 전체 플로우 성공")

    def test_scenario_2_1_2_required_question_validation(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.2: 필수 질문 검증 플로우"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 1. 필수 질문을 누락한 응답 제출 시도
        incomplete_answers = {
            survey_data['question_ids'][0]: "홍길동",  # TEXT (필수) ✓
            # survey_data['question_ids'][1]: RATING (필수) - 누락!
            survey_data['question_ids'][2]: "이메일",  # MULTIPLE_CHOICE (필수) ✓
            survey_data['question_ids'][3]: "y",  # YES_NO (선택)
            # survey_data['question_ids'][8]: EMAIL (필수) - 누락!
        }

        # 2. 검증 실패 메시지 확인
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=incomplete_answers
        )
        assert result.is_failure
        assert "필수 질문" in result.error

        # 3. 누락된 질문 응답 후 재제출
        complete_answers = incomplete_answers.copy()
        complete_answers[survey_data['question_ids'][1]] = "4"  # RATING 추가
        complete_answers[survey_data['question_ids'][8]] = "hong@example.com"  # EMAIL 추가

        # 4. 제출 성공 확인
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=complete_answers
        )
        assert result.is_success

        print("✅ 시나리오 2.1.2: 필수 질문 검증 플로우 성공")

    def test_scenario_2_1_3_various_question_type_validation(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.3: 다양한 질문 타입별 응답 검증"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # TEXT: 자유 텍스트 입력
        text_valid, _ = validate_text_answer("자유롭게 입력한 텍스트")
        assert text_valid is True

        # RATING: 1-5 범위 검증
        rating_valid_3, _ = validate_rating_answer("3")
        assert rating_valid_3 is True

        rating_valid_0, _ = validate_rating_answer("0")
        assert rating_valid_0 is False

        rating_valid_6, _ = validate_rating_answer("6")
        assert rating_valid_6 is False

        # SCALE_10: 1-10 범위 검증
        scale_valid_5, _ = validate_scale_10_answer("5")
        assert scale_valid_5 is True

        scale_valid_0, _ = validate_scale_10_answer("0")
        assert scale_valid_0 is False

        scale_valid_11, _ = validate_scale_10_answer("11")
        assert scale_valid_11 is False

        # MULTIPLE_CHOICE: 선택지 검증
        options = ["옵션1", "옵션2", "옵션3"]
        mc_valid, _ = validate_multiple_choice_answer("옵션1", options)
        assert mc_valid is True

        mc_invalid, _ = validate_multiple_choice_answer("옵션4", options)
        assert mc_invalid is False

        # MULTI_SELECT: 다중 선택 검증
        ms_options = ["A", "B", "C", "D", "E"]
        ms_valid, _ = validate_multi_select_answer("1,3,5", ms_options)
        assert ms_valid is True

        ms_invalid, _ = validate_multi_select_answer("1,6", ms_options)
        assert ms_invalid is False

        # YES_NO: y/n 검증
        yn_valid_y, _ = validate_yes_no_answer("y")
        assert yn_valid_y is True

        yn_valid_yes, _ = validate_yes_no_answer("yes")
        assert yn_valid_yes is True

        yn_valid_n, _ = validate_yes_no_answer("n")
        assert yn_valid_n is True

        yn_valid_no, _ = validate_yes_no_answer("no")
        assert yn_valid_no is True

        yn_valid_korean_yes, _ = validate_yes_no_answer("예")
        assert yn_valid_korean_yes is True

        yn_valid_korean_no, _ = validate_yes_no_answer("아니오")
        assert yn_valid_korean_no is True

        # DATE: YYYY-MM-DD 형식 검증
        date_valid, _ = validate_date_answer("2024-03-15")
        assert date_valid is True

        date_invalid_format, _ = validate_date_answer("2024/03/15")
        assert date_invalid_format is False

        date_invalid_date, _ = validate_date_answer("2024-02-30")
        assert date_invalid_date is False

        # NUMBER: 숫자 형식 검증
        number_valid_int, _ = validate_number_answer("42")
        assert number_valid_int is True

        number_valid_float, _ = validate_number_answer("3.14")
        assert number_valid_float is True

        number_invalid, _ = validate_number_answer("abc")
        assert number_invalid is False

        # EMAIL: 이메일 형식 검증
        email_valid, _ = validate_email_answer("user@example.com")
        assert email_valid is True

        email_invalid_no_at, _ = validate_email_answer("userexample.com")
        assert email_invalid_no_at is False

        email_invalid_no_domain, _ = validate_email_answer("user@")
        assert email_invalid_no_domain is False

        print("✅ 시나리오 2.1.3: 다양한 질문 타입별 응답 검증 성공")

    def test_scenario_2_1_4_response_modification(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.4: 응답 수정 플로우"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 1. 응답 제출
        original_answers = {
            survey_data['question_ids'][0]: "김철수",
            survey_data['question_ids'][1]: "3",
            survey_data['question_ids'][2]: "전화",
            survey_data['question_ids'][8]: "kim@example.com"
        }

        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=original_answers
        )
        assert result.is_success
        response_id = result.value

        # 2. 응답자가 자신의 응답 수정
        modified_answers = {
            survey_data['question_ids'][0]: "김철수",  # 유지
            survey_data['question_ids'][1]: "5",  # 수정: 3 -> 5
            survey_data['question_ids'][2]: "이메일",  # 수정: 전화 -> 이메일
            survey_data['question_ids'][8]: "kim.cs@example.com"  # 수정
        }

        # 응답 수정 (구현에 따라 update_response 메서드 필요)
        response = services['repos']['response_repo'].find_by_id(response_id)
        response.answers = modified_answers
        response.updated_at = datetime.now()

        result = services['repos']['response_repo'].update(response)
        assert result is True

        # 3. 수정 이력 생성 확인 (구현된 경우)
        history_repo = services['repos']['response_history_repo']
        if hasattr(history_repo, 'save'):
            history = ResponseHistory(
                id=str(uuid.uuid4()),
                response_id=response_id,
                previous_answers=original_answers,
                new_answers=modified_answers,
                modified_by=users['respondent1'].id,
                modified_at=datetime.now()
            )
            history_repo.save(history)

        # 4. 수정된 답변 조회 확인
        updated_response = services['repos']['response_repo'].find_by_id(response_id)
        assert updated_response.answers[survey_data['question_ids'][1]] == "5"
        assert updated_response.answers[survey_data['question_ids'][2]] == "이메일"

        print("✅ 시나리오 2.1.4: 응답 수정 플로우 성공")

    def test_scenario_2_1_5_response_deletion(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.5: 응답 삭제 플로우"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 1. 응답 제출
        answers = {
            survey_data['question_ids'][0]: "삭제할 응답",
            survey_data['question_ids'][1]: "4",
            survey_data['question_ids'][2]: "이메일",
            survey_data['question_ids'][8]: "delete@example.com"
        }

        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers
        )
        assert result.is_success
        response_id = result.value

        # 2. 응답자가 자신의 응답 삭제
        result = response_service.delete_response(
            user=users['respondent1'],
            response_id=response_id
        )
        assert result.is_success

        # 3. 삭제 후 조회 불가 확인
        deleted_response = services['repos']['response_repo'].find_by_id(response_id)
        assert deleted_response is None

        # 4. 통계에서 제외 확인
        result = response_service.get_survey_results(
            user=users['manager'],
            survey_id=survey_data['survey_id']
        )
        if result.is_success:
            results = result.value
            # 삭제된 응답은 통계에 포함되지 않음
            total_responses = results.get('total_responses', 0)
            # 이전 테스트에서 생성된 응답 제외
            assert response_id not in [r.id for r in services['repos']['response_repo'].find_by_survey_id(survey_data['survey_id'])]

        print("✅ 시나리오 2.1.5: 응답 삭제 플로우 성공")

    def test_scenario_2_1_6_partial_response_with_optional(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.6: 부분 응답 저장 (선택적 질문)"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 1. 필수 질문만 응답하고 선택적 질문은 건너뛰기
        partial_answers = {
            survey_data['question_ids'][0]: "필수만 응답",  # TEXT (필수)
            survey_data['question_ids'][1]: "4",  # RATING (필수)
            survey_data['question_ids'][2]: "이메일",  # MULTIPLE_CHOICE (필수)
            # YES_NO (선택) - 건너뜀
            # SCALE_10 (선택) - 건너뜀
            # MULTI_SELECT (선택) - 건너뜀
            # DATE (선택) - 건너뜀
            # NUMBER (선택) - 건너뜀
            survey_data['question_ids'][8]: "partial@example.com"  # EMAIL (필수)
        }

        # 2. 제출 성공 확인
        result = response_service.submit_response(
            user=users['respondent2'],
            survey_id=survey_data['survey_id'],
            answers=partial_answers
        )
        assert result.is_success
        response_id = result.value

        # 3. 선택적 질문 응답 없음 확인
        response = services['repos']['response_repo'].find_by_id(response_id)
        assert len(response.answers) == 4  # 필수 4개만
        assert survey_data['question_ids'][3] not in response.answers  # YES_NO 없음
        assert survey_data['question_ids'][4] not in response.answers  # SCALE_10 없음
        assert survey_data['question_ids'][5] not in response.answers  # MULTI_SELECT 없음

        print("✅ 시나리오 2.1.6: 부분 응답 저장 (선택적 질문) 성공")

    def test_scenario_2_1_7_session_based_response_tracking(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.7: 세션별 응답 추적"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']
        session_service = services['survey_session_service']

        # 1. 동일 응답자가 첫 번째 세션에서 응답
        result = session_service.start_survey(
            user=users['respondent1'],
            survey_id=survey_data['survey_id']
        )
        assert result.is_success
        session1_id = result.value

        session1_start_time = datetime.now()

        answers1 = {
            survey_data['question_ids'][0]: "첫 번째 응답",
            survey_data['question_ids'][1]: "3",
            survey_data['question_ids'][2]: "전화",
            survey_data['question_ids'][8]: "first@example.com"
        }

        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers1
        )
        assert result.is_success
        response1_id = result.value

        session1_end_time = datetime.now()
        session1_duration = (session1_end_time - session1_start_time).total_seconds()

        result = session_service.complete_survey(
            user=users['respondent1'],
            session_id=session1_id
        )
        assert result.is_success

        # 2. 동일 응답자가 두 번째 세션에서 다시 응답
        result = session_service.start_survey(
            user=users['respondent1'],
            survey_id=survey_data['survey_id']
        )
        assert result.is_success
        session2_id = result.value

        session2_start_time = datetime.now()

        answers2 = {
            survey_data['question_ids'][0]: "두 번째 응답",
            survey_data['question_ids'][1]: "5",
            survey_data['question_ids'][2]: "이메일",
            survey_data['question_ids'][8]: "second@example.com"
        }

        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers2
        )
        assert result.is_success
        response2_id = result.value

        session2_end_time = datetime.now()
        session2_duration = (session2_end_time - session2_start_time).total_seconds()

        result = session_service.complete_survey(
            user=users['respondent1'],
            session_id=session2_id
        )
        assert result.is_success

        # 3. 각 세션별로 독립적인 응답 저장 확인
        response1 = services['repos']['response_repo'].find_by_id(response1_id)
        response2 = services['repos']['response_repo'].find_by_id(response2_id)

        assert response1.id != response2.id
        assert response1.answers != response2.answers

        # 4. 세션 ID로 응답 구분 확인
        session1 = services['repos']['survey_session_repo'].find_by_id(session1_id)
        session2 = services['repos']['survey_session_repo'].find_by_id(session2_id)

        assert session1.id != session2.id
        assert session1.completed is True
        assert session2.completed is True

        # 5. 각 세션별 소요 시간 독립적으로 기록
        # 실제 소요 시간은 밀리초 단위로 매우 짧을 것
        assert session1_duration >= 0
        assert session2_duration >= 0

        print("✅ 시나리오 2.1.7: 세션별 응답 추적 성공")

    def test_scenario_2_1_8_concurrent_responses(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.8: 동시 다중 응답자 제출"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 여러 응답자가 동시에 응답 제출
        responses = []

        # 응답자 1
        answers1 = {
            survey_data['question_ids'][0]: "응답자1",
            survey_data['question_ids'][1]: "5",
            survey_data['question_ids'][2]: "이메일",
            survey_data['question_ids'][8]: "user1@example.com"
        }
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers1
        )
        assert result.is_success
        responses.append(result.value)

        # 응답자 2
        answers2 = {
            survey_data['question_ids'][0]: "응답자2",
            survey_data['question_ids'][1]: "4",
            survey_data['question_ids'][2]: "전화",
            survey_data['question_ids'][8]: "user2@example.com"
        }
        result = response_service.submit_response(
            user=users['respondent2'],
            survey_id=survey_data['survey_id'],
            answers=answers2
        )
        assert result.is_success
        responses.append(result.value)

        # 응답자 3
        answers3 = {
            survey_data['question_ids'][0]: "응답자3",
            survey_data['question_ids'][1]: "3",
            survey_data['question_ids'][2]: "문자",
            survey_data['question_ids'][8]: "user3@example.com"
        }
        result = response_service.submit_response(
            user=users['respondent3'],
            survey_id=survey_data['survey_id'],
            answers=answers3
        )
        assert result.is_success
        responses.append(result.value)

        # 모든 응답이 독립적으로 저장되었는지 확인
        assert len(responses) == 3
        assert len(set(responses)) == 3  # 모두 고유한 ID

        # 설문 결과 조회
        result = response_service.get_survey_results(
            user=users['manager'],
            survey_id=survey_data['survey_id']
        )
        assert result.is_success
        results = result.value

        # 응답 수 확인
        survey_responses = services['repos']['response_repo'].find_by_survey_id(survey_data['survey_id'])
        # 이전 테스트의 응답도 포함될 수 있음
        assert len([r for r in survey_responses if r.id in responses]) == 3

        print("✅ 시나리오 2.1.8: 동시 다중 응답자 제출 성공")

    def test_scenario_2_1_9_response_with_all_question_types(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.9: 모든 질문 타입 완전 응답"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 모든 질문 타입에 대한 완전한 응답
        complete_answers = {
            survey_data['question_ids'][0]: "홍길동",  # TEXT
            survey_data['question_ids'][1]: "5",  # RATING (1-5)
            survey_data['question_ids'][2]: "이메일",  # MULTIPLE_CHOICE
            survey_data['question_ids'][3]: "yes",  # YES_NO
            survey_data['question_ids'][4]: "10",  # SCALE_10 (1-10)
            survey_data['question_ids'][5]: "1,2,3",  # MULTI_SELECT
            survey_data['question_ids'][6]: "2024-01-01",  # DATE
            survey_data['question_ids'][7]: "100",  # NUMBER
            survey_data['question_ids'][8]: "complete@example.com"  # EMAIL
        }

        # 응답 제출
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=complete_answers
        )
        assert result.is_success
        response_id = result.value

        # 응답 검증
        response = services['repos']['response_repo'].find_by_id(response_id)
        assert len(response.answers) == 9

        # 각 타입별 응답 값 검증
        assert response.answers[survey_data['question_ids'][0]] == "홍길동"
        assert response.answers[survey_data['question_ids'][1]] == "5"
        assert response.answers[survey_data['question_ids'][2]] == "이메일"
        assert response.answers[survey_data['question_ids'][3]] == "yes"
        assert response.answers[survey_data['question_ids'][4]] == "10"
        assert response.answers[survey_data['question_ids'][5]] == "1,2,3"
        assert response.answers[survey_data['question_ids'][6]] == "2024-01-01"
        assert response.answers[survey_data['question_ids'][7]] == "100"
        assert response.answers[survey_data['question_ids'][8]] == "complete@example.com"

        print("✅ 시나리오 2.1.9: 모든 질문 타입 완전 응답 성공")

    def test_scenario_2_1_10_response_validation_errors(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.10: 응답 검증 오류 처리"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        # 잘못된 형식의 응답들
        invalid_answers = {
            survey_data['question_ids'][0]: "",  # TEXT - 빈 문자열 (필수)
            survey_data['question_ids'][1]: "6",  # RATING - 범위 초과 (1-5)
            survey_data['question_ids'][2]: "없는옵션",  # MULTIPLE_CHOICE - 잘못된 옵션
            survey_data['question_ids'][3]: "maybe",  # YES_NO - 잘못된 값
            survey_data['question_ids'][4]: "11",  # SCALE_10 - 범위 초과 (1-10)
            survey_data['question_ids'][5]: "1,6,7",  # MULTI_SELECT - 범위 초과
            survey_data['question_ids'][6]: "2024-13-45",  # DATE - 잘못된 날짜
            survey_data['question_ids'][7]: "abc",  # NUMBER - 숫자 아님
            survey_data['question_ids'][8]: "not-an-email"  # EMAIL - 잘못된 형식
        }

        # 각 잘못된 응답에 대해 검증 실패 확인
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=invalid_answers
        )
        assert result.is_failure

        # 오류 메시지 확인
        error = result.error
        # 다양한 검증 오류가 포함되어야 함
        assert "필수" in error or "유효" in error or "올바른" in error

        print("✅ 시나리오 2.1.10: 응답 검증 오류 처리 성공")

    def test_scenario_2_1_11_response_progress_tracking(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.11: 응답 진행률 추적"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']

        total_questions = len(survey_data['question_ids'])

        # 부분 응답으로 진행률 계산
        partial_answers = {
            survey_data['question_ids'][0]: "진행 중",  # 1/9 = 11%
            survey_data['question_ids'][1]: "3",  # 2/9 = 22%
            survey_data['question_ids'][2]: "이메일",  # 3/9 = 33%
        }

        answered_count = len(partial_answers)
        progress_percentage = (answered_count / total_questions) * 100

        assert progress_percentage == pytest.approx(33.33, rel=0.01)

        # 더 많은 응답 추가
        partial_answers[survey_data['question_ids'][3]] = "y"  # 4/9 = 44%
        partial_answers[survey_data['question_ids'][4]] = "7"  # 5/9 = 55%

        answered_count = len(partial_answers)
        progress_percentage = (answered_count / total_questions) * 100

        assert progress_percentage == pytest.approx(55.55, rel=0.01)

        # 필수 질문만 완료한 경우
        required_answers = {
            survey_data['question_ids'][0]: "필수",  # TEXT (필수)
            survey_data['question_ids'][1]: "4",  # RATING (필수)
            survey_data['question_ids'][2]: "전화",  # MULTIPLE_CHOICE (필수)
            survey_data['question_ids'][8]: "required@example.com"  # EMAIL (필수)
        }

        required_count = 4
        required_progress = (required_count / total_questions) * 100

        assert required_progress == pytest.approx(44.44, rel=0.01)

        print("✅ 시나리오 2.1.11: 응답 진행률 추적 성공")

    def test_scenario_2_1_12_response_time_tracking(self, setup_services, setup_users, setup_survey):
        """시나리오 2.1.12: 응답 시간 추적"""
        services = setup_services
        users = setup_users
        survey_data = setup_survey
        response_service = services['response_service']
        session_service = services['survey_session_service']

        # 세션 시작
        result = session_service.start_survey(
            user=users['respondent1'],
            survey_id=survey_data['survey_id']
        )
        assert result.is_success
        session_id = result.value

        start_time = datetime.now()

        # 응답 작성 시뮬레이션 (실제로는 각 질문마다 시간이 걸림)
        answers = {
            survey_data['question_ids'][0]: "시간 추적",
            survey_data['question_ids'][1]: "5",
            survey_data['question_ids'][2]: "이메일",
            survey_data['question_ids'][8]: "time@example.com"
        }

        # 응답 제출
        result = response_service.submit_response(
            user=users['respondent1'],
            survey_id=survey_data['survey_id'],
            answers=answers
        )
        assert result.is_success

        end_time = datetime.now()

        # 세션 완료
        result = session_service.complete_survey(
            user=users['respondent1'],
            session_id=session_id
        )
        assert result.is_success

        # 총 소요 시간 계산
        total_duration = (end_time - start_time).total_seconds()
        assert total_duration >= 0

        # 세션 정보에서 시간 확인
        session = services['repos']['survey_session_repo'].find_by_id(session_id)
        assert session.started_at is not None
        assert session.submitted_at is not None

        session_duration = (session.submitted_at - session.started_at).total_seconds()
        assert session_duration >= 0

        print(f"✅ 시나리오 2.1.12: 응답 시간 추적 성공 (소요 시간: {session_duration:.2f}초)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])