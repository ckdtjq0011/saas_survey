import pytest
import uuid
from datetime import datetime
from domain.entities.tenant import Tenant
from domain.entities.user import User
from domain.entities.question import Question
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestTenantValidation:
    """Tenant 엔티티 검증 로직 테스트"""

    def test_tenant_with_empty_name_rejected(self):
        """빈 이름으로 Tenant 생성 시 ValueError 발생

        시나리오:
            1. 빈 문자열로 Tenant 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="테넌트 이름은 필수입니다"):
            Tenant(
                id=str(uuid.uuid4()),
                name="",
                created_at=datetime.now(),
                is_active=True
            )

    def test_tenant_with_whitespace_only_name_rejected(self):
        """공백만으로 구성된 이름 거부

        시나리오:
            1. 공백만 있는 이름으로 Tenant 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="테넌트 이름은 필수입니다"):
            Tenant(
                id=str(uuid.uuid4()),
                name="   ",
                created_at=datetime.now(),
                is_active=True
            )

    def test_tenant_with_very_long_name_accepted(self):
        """매우 긴 이름 처리 (1000자)

        시나리오:
            1. 1000자 이름으로 Tenant 생성
            2. 정상 생성 확인
        """
        long_name = "A" * 1000
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=long_name,
            created_at=datetime.now(),
            is_active=True
        )
        assert tenant.name == long_name
        assert len(tenant.name) == 1000

    def test_tenant_with_special_characters_only_accepted(self):
        """특수문자만으로 구성된 이름 허용

        시나리오:
            1. 특수문자만 있는 이름으로 Tenant 생성
            2. 정상 생성 확인
        """
        special_name = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name=special_name,
            created_at=datetime.now(),
            is_active=True
        )
        assert tenant.name == special_name


class TestUserValidation:
    """User 엔티티 검증 로직 테스트"""

    def test_user_with_consecutive_dots_in_email_rejected(self):
        """이메일에 연속된 점(..) 있는 경우 거부

        시나리오:
            1. 연속 점이 있는 이메일로 User 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="유효한 이메일 형식이 아닙니다"):
            User(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                username="testuser",
                email="test..user@example.com",
                password_hash="$2b$12$dummy_hash",
                role=Role.RESPONDENT,
                created_at=datetime.now(),
                is_active=True
            )

    def test_user_with_special_char_at_email_start_rejected(self):
        """이메일 시작에 특수문자 있는 경우 거부

        시나리오:
            1. 이메일이 특수문자로 시작하는 User 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="유효한 이메일 형식이 아닙니다"):
            User(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                username="testuser",
                email=".testuser@example.com",
                password_hash="$2b$12$dummy_hash",
                role=Role.RESPONDENT,
                created_at=datetime.now(),
                is_active=True
            )

    def test_user_with_international_domain_accepted(self):
        """국제 도메인 이메일 허용

        시나리오:
            1. 국제 도메인 이메일로 User 생성
            2. 정상 생성 확인
        """
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            username="testuser",
            email="test@한국.kr",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        assert user.email == "test@한국.kr"

    def test_user_with_very_long_email_accepted(self):
        """매우 긴 이메일 처리 (RFC 5321 기준)

        시나리오:
            1. 매우 긴 이메일로 User 생성
            2. 정상 생성 확인

        RFC 5321 기준:
            - Local part: 최대 64자
            - Domain: 최대 255자
            - 각 라벨: 최대 63자
        """
        local_part = "a" * 64
        # 도메인 각 라벨은 63자 제한, 전체 도메인은 255자 제한
        domain_part = "b" * 63 + "." + "c" * 63 + "." + "d" * 50 + ".com"
        long_email = f"{local_part}@{domain_part}"

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            username="testuser",
            email=long_email,
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        assert user.email == long_email

    def test_user_with_whitespace_in_username_rejected(self):
        """username에 공백 포함 시 거부

        시나리오:
            1. 공백이 포함된 username으로 User 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="사용자명에 공백이 포함될 수 없습니다"):
            User(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                username="test user",
                email="test@example.com",
                password_hash="$2b$12$dummy_hash",
                role=Role.RESPONDENT,
                created_at=datetime.now(),
                is_active=True
            )

    def test_user_with_very_long_username_rejected(self):
        """매우 긴 username 거부 (50자 제한)

        시나리오:
            1. 50자를 초과하는 username으로 User 생성 시도
            2. ValueError 예외 발생 확인
        """
        long_username = "a" * 51
        with pytest.raises(ValueError, match="사용자명은 50자를 초과할 수 없습니다"):
            User(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                username=long_username,
                email="test@example.com",
                password_hash="$2b$12$dummy_hash",
                role=Role.RESPONDENT,
                created_at=datetime.now(),
                is_active=True
            )

    def test_user_with_special_characters_in_username_accepted(self):
        """username에 특수문자 허용 (하이픈, 언더스코어)

        시나리오:
            1. 특수문자가 포함된 username으로 User 생성
            2. 정상 생성 확인
        """
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            username="test-user_123",
            email="test@example.com",
            password_hash="$2b$12$dummy_hash",
            role=Role.RESPONDENT,
            created_at=datetime.now(),
            is_active=True
        )
        assert user.username == "test-user_123"

    def test_user_with_invalid_role_type_rejected(self):
        """잘못된 Role 타입으로 User 생성 시 거부

        시나리오:
            1. 문자열로 role 설정 시도
            2. TypeError 또는 ValueError 예외 발생 확인
        """
        with pytest.raises((TypeError, ValueError)):
            User(
                id=str(uuid.uuid4()),
                tenant_id=str(uuid.uuid4()),
                username="testuser",
                email="test@example.com",
                password_hash="$2b$12$dummy_hash",
                role="invalid_role",
                created_at=datetime.now(),
                is_active=True
            )


class TestQuestionValidation:
    """Question 엔티티 검증 로직 테스트"""

    def test_multiple_choice_with_no_options_rejected(self):
        """MULTIPLE_CHOICE인데 options=None인 경우 거부

        시나리오:
            1. MULTIPLE_CHOICE 타입인데 options 없이 Question 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="객관식 질문은 최소 2개 이상의 선택지가 필요합니다"):
            Question(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                text="선택하세요",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=None
            )

    def test_multiple_choice_with_single_option_rejected(self):
        """MULTIPLE_CHOICE인데 선택지 1개만 있는 경우 거부

        시나리오:
            1. 선택지 1개만 있는 MULTIPLE_CHOICE 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="객관식 질문은 최소 2개 이상의 선택지가 필요합니다"):
            Question(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                text="선택하세요",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=("옵션1",)
            )

    def test_rating_with_options_provided_accepted(self):
        """RATING인데 options 제공된 경우 허용 (무시됨)

        시나리오:
            1. RATING 타입인데 options와 함께 Question 생성
            2. 정상 생성 확인 (options는 무시)
        """
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="평가하세요",
            question_type=QuestionType.RATING,
            options=("1", "2", "3")
        )
        assert question.question_type == QuestionType.RATING

    def test_text_with_options_provided_accepted(self):
        """TEXT인데 options 제공된 경우 허용 (무시됨)

        시나리오:
            1. TEXT 타입인데 options와 함께 Question 생성
            2. 정상 생성 확인 (options는 무시)
        """
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="설명하세요",
            question_type=QuestionType.TEXT,
            options=("옵션1", "옵션2")
        )
        assert question.question_type == QuestionType.TEXT

    def test_multiple_choice_with_empty_options_list_rejected(self):
        """빈 선택지 배열로 MULTIPLE_CHOICE 생성 거부

        시나리오:
            1. 빈 튜플로 options 제공하여 Question 생성 시도
            2. ValueError 예외 발생 확인
        """
        with pytest.raises(ValueError, match="객관식 질문은 최소 2개 이상의 선택지가 필요합니다"):
            Question(
                id=str(uuid.uuid4()),
                survey_id=str(uuid.uuid4()),
                text="선택하세요",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=()
            )

    def test_multiple_choice_with_duplicate_options_accepted(self):
        """중복 선택지 허용 (비즈니스 로직에서 처리)

        시나리오:
            1. 중복된 선택지로 Question 생성
            2. 정상 생성 확인 (중복 허용)
        """
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="선택하세요",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=("옵션1", "옵션1", "옵션2")
        )
        assert len(question.options) == 3

    def test_question_with_very_long_text_accepted(self):
        """매우 긴 질문 텍스트 허용 (5000자)

        시나리오:
            1. 5000자 질문 텍스트로 Question 생성
            2. 정상 생성 확인
        """
        long_text = "질문" * 2500
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text=long_text,
            question_type=QuestionType.TEXT,
            options=None
        )
        assert len(question.text) == 5000

    def test_multiple_choice_with_100_options_accepted(self):
        """선택지 100개 이상 허용

        시나리오:
            1. 100개 선택지로 Question 생성
            2. 정상 생성 확인
        """
        options = tuple(f"옵션{i}" for i in range(1, 101))
        question = Question(
            id=str(uuid.uuid4()),
            survey_id=str(uuid.uuid4()),
            text="많은 선택지",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=options
        )
        assert len(question.options) == 100
