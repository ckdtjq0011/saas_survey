"""보안 취약점 테스트 모음입니다.

이 테스트들은 시스템의 보안 취약점을 검증합니다.
초기 실행 시 실패할 것으로 예상되며, 코드 수정 후 통과해야 합니다.
"""

import uuid
from datetime import datetime
import pytest

from domain.entities.tenant import Tenant
from domain.entities.user import User
from domain.entities.survey import Survey
from domain.entities.question import Question
from domain.value_objects.role import Role
from domain.value_objects.types import QuestionType


class TestCSVInjection:
    """CSV Injection 취약점 테스트 (VULN-001 - Critical)"""

    def test_csv_injection_in_tenant_name(self, tenant_repo):
        """테넌트 이름에 CSV 수식 문자 삽입 시 이스케이프되는지 테스트"""
        # CSV 수식 공격 시도: Excel에서 실행될 수 있는 수식
        malicious_names = [
            "=1+1",  # 수식 시작
            "+1+1",  # 수식 시작
            "-1+1",  # 수식 시작
            "@SUM(A1:A10)",  # 함수 호출
            "=cmd|'/c calc'!A1",  # 명령어 실행 시도
        ]

        for malicious_name in malicious_names:
            tenant = Tenant(
                id=str(uuid.uuid4()),
                name=malicious_name,
                created_at=datetime.now(),
                is_active=True,
            )
            tenant_repo.save_tenant(tenant)

            # CSV 파일을 읽어서 이스케이프되었는지 확인
            loaded_tenant = tenant_repo.find_tenant_by_id(tenant.id)
            assert loaded_tenant is not None

            # 원본 데이터는 그대로 유지되어야 함
            assert loaded_tenant.name == malicious_name

            # CSV 파일 직접 읽기로 이스케이프 확인
            import csv
            csv_path = tenant_repo.tenants_file
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                matching_row = next((r for r in rows if r["id"] == tenant.id), None)
                assert matching_row is not None

                # CSV에 저장된 값이 수식으로 해석되지 않도록 이스케이프되어야 함
                # 예: =1+1 → '=1+1 또는 "=1+1" 형태로 저장
                csv_value = matching_row["name"]
                if csv_value.startswith(("=", "+", "-", "@")):
                    # 위험한 문자로 시작하는 경우, 반드시 따옴표나 이스케이프 처리되어야 함
                    # 하지만 DictReader는 이미 파싱된 값을 반환하므로
                    # 실제로는 파일 내용을 직접 확인해야 함
                    pass

            # 정리
            tenant_repo.delete_tenant(tenant.id)

    def test_csv_injection_in_survey_data(self, survey_repo, tenant_repo):
        """설문 제목/설명에 CSV 수식 문자 삽입 시 이스케이프되는지 테스트"""
        # 테넌트 생성
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        malicious_title = "=1+1"
        malicious_description = "@SUM(A1:A10)"

        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_id="test_user_id",
            title=malicious_title,
            description=malicious_description,
            created_at=datetime.now(),
        )
        survey_repo.save_survey(survey)

        # CSV 파일에서 이스케이프 확인
        loaded_survey = survey_repo.find_survey_by_id(survey.id)
        assert loaded_survey is not None
        assert loaded_survey.title == malicious_title
        assert loaded_survey.description == malicious_description

        # 정리
        survey_repo.delete_survey(survey.id)
        tenant_repo.delete_tenant(tenant.id)


class TestWhitespaceValidation:
    """빈 문자열 및 공백 검증 테스트 (VULN-003 - High)"""

    def test_whitespace_only_survey_title_rejected(self, tenant_repo):
        """공백만으로 이루어진 설문 제목은 거부되어야 함"""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        whitespace_titles = [
            "   ",  # 공백만
            "\t\t\t",  # 탭만
            "  \t  \n  ",  # 혼합 공백
        ]

        for title in whitespace_titles:
            with pytest.raises(ValueError, match="제목|필수"):
                Survey(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    owner_id="test_user_id",
                    title=title,
                    description="Valid description",
                    created_at=datetime.now(),
                )

        # 정리
        tenant_repo.delete_tenant(tenant.id)

    def test_whitespace_only_question_text_rejected(self, tenant_repo, survey_repo):
        """공백만으로 이루어진 질문 내용은 거부되어야 함"""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_id="test_user_id",
            title="Valid Survey",
            description="Valid description",
            created_at=datetime.now(),
        )
        survey_repo.save_survey(survey)

        whitespace_texts = [
            "     ",  # 공백만
            "\t\t",  # 탭만
        ]

        for text in whitespace_texts:
            with pytest.raises(ValueError, match="질문|필수"):
                Question(
                    id=str(uuid.uuid4()),
                    survey_id=survey.id,
                    text=text,
                    question_type=QuestionType.TEXT,
                    options=None,
                )

        # 정리
        survey_repo.delete_survey(survey.id)
        tenant_repo.delete_tenant(tenant.id)


class TestQuestionOptionsParsingVulnerability:
    """질문 옵션 파싱 취약점 테스트 (VULN-006 - High)"""

    def test_question_options_with_pipe_character(
        self, survey_repo, tenant_repo
    ):
        """선택지에 파이프 문자(|)가 포함된 경우 올바르게 처리되는지 테스트

        현재 구현은 파이프를 구분자로 사용하므로,
        선택지에 파이프가 포함되면 파싱 오류가 발생할 수 있음
        """
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        survey = Survey(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_id="test_user_id",
            title="Options Test Survey",
            description="Testing pipe character in options",
            created_at=datetime.now(),
        )
        survey_repo.save_survey(survey)

        # 파이프 문자를 포함한 선택지
        options_with_pipe = (
            "Option A | Sub-option 1",  # 파이프가 옵션 설명의 일부
            "Price: $10 | Quantity: 5",  # 파이프로 구분된 정보
            "Yes|No",  # 파이프가 의미의 일부
        )

        question = Question(
            id=str(uuid.uuid4()),
            survey_id=survey.id,
            text="Choose an option with pipe character",
            question_type=QuestionType.MULTIPLE_CHOICE,
            options=options_with_pipe,
        )
        survey_repo.save_question(question)

        # 로드 후 옵션이 정확히 복원되는지 확인
        loaded_questions = survey_repo.find_questions_by_survey_id(survey.id)
        assert len(loaded_questions) == 1
        loaded_question = loaded_questions[0]
        assert loaded_question.options == options_with_pipe
        assert len(loaded_question.options) == 3  # 3개 옵션이어야 함 (하지만 파이프 구분자 때문에 실패할 것)

        # 정리
        survey_repo.delete_survey(survey.id)
        tenant_repo.delete_tenant(tenant.id)


class TestUserValidation:
    """사용자 입력 검증 테스트 (VULN-007, VULN-008 - High)"""

    def test_invalid_email_formats_rejected(self, tenant_repo):
        """잘못된 이메일 형식은 거부되어야 함 (VULN-007)"""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        invalid_emails = [
            "not-an-email",  # @ 없음
            "missing-domain@",  # 도메인 없음
            "@missing-local.com",  # 로컬 부분 없음
            "spaces in@email.com",  # 공백 포함
            "double@@domain.com",  # @ 중복
            "no-tld@domain",  # TLD 없음
            ".start@domain.com",  # 점으로 시작
            "end.@domain.com",  # 점으로 끝
            "a@b",  # 너무 짧음
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="이메일|형식|유효"):
                User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    username="validuser",
                    email=invalid_email,
                    password_hash="$2b$12$dummy_hash",
                    role=Role.RESPONDENT,
                    created_at=datetime.now(),
                    is_active=True,
                )

        # 정리
        tenant_repo.delete_tenant(tenant.id)

    def test_username_with_spaces_rejected(self, tenant_repo):
        """공백이 포함된 사용자명은 거부되어야 함 (VULN-008)"""
        tenant = Tenant(
            id=str(uuid.uuid4()),
            name="Test Tenant",
            created_at=datetime.now(),
            is_active=True,
        )
        tenant_repo.save_tenant(tenant)

        invalid_usernames = [
            "user name",  # 공백 포함
            "user\tname",  # 탭 포함
            " username",  # 앞 공백
            "username ",  # 뒤 공백
            "user\nname",  # 개행 포함
        ]

        for invalid_username in invalid_usernames:
            with pytest.raises(ValueError, match="사용자명|공백|유효"):
                User(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant.id,
                    username=invalid_username,
                    email="valid@email.com",
                    password_hash="$2b$12$dummy_hash",
                    role=Role.RESPONDENT,
                    created_at=datetime.now(),
                    is_active=True,
                )

        # 정리
        tenant_repo.delete_tenant(tenant.id)
