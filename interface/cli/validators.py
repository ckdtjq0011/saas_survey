import re
from typing import Callable


def validate_email(email: str) -> tuple[bool, str]:
    """이메일 형식을 검증합니다.

    Args:
        email: 검증할 이메일 주소

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True, ""
    return False, "유효하지 않은 이메일 형식입니다 (예: user@example.com)"


def validate_password(password: str) -> tuple[bool, str]:
    """비밀번호 강도를 검증합니다.

    Args:
        password: 검증할 비밀번호

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"

    if not any(c.isdigit() for c in password):
        return False, "비밀번호는 최소 1개의 숫자를 포함해야 합니다"

    if not any(c.isalpha() for c in password):
        return False, "비밀번호는 최소 1개의 문자를 포함해야 합니다"

    return True, ""


def validate_username(username: str) -> tuple[bool, str]:
    """사용자명을 검증합니다.

    Args:
        username: 검증할 사용자명

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if len(username) < 3:
        return False, "사용자명은 최소 3자 이상이어야 합니다"

    if len(username) > 20:
        return False, "사용자명은 최대 20자까지 가능합니다"

    if not username[0].isalpha():
        return False, "사용자명은 영문자로 시작해야 합니다"

    if not all(c.isalnum() or c in ['_', '-'] for c in username):
        return False, "사용자명은 영문자, 숫자, _, - 만 사용 가능합니다"

    return True, ""


def validate_tenant_name(name: str) -> tuple[bool, str]:
    """테넌트 이름을 검증합니다.

    Args:
        name: 검증할 테넌트 이름

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if len(name) < 2:
        return False, "테넌트 이름은 최소 2자 이상이어야 합니다"

    if len(name) > 50:
        return False, "테넌트 이름은 최대 50자까지 가능합니다"

    return True, ""


def validate_survey_title(title: str) -> tuple[bool, str]:
    """설문 제목을 검증합니다.

    Args:
        title: 검증할 설문 제목

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if len(title) < 3:
        return False, "설문 제목은 최소 3자 이상이어야 합니다"

    if len(title) > 100:
        return False, "설문 제목은 최대 100자까지 가능합니다"

    return True, ""


def validate_question_text(text: str) -> tuple[bool, str]:
    """질문 내용을 검증합니다.

    Args:
        text: 검증할 질문 내용

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if len(text) < 5:
        return False, "질문 내용은 최소 5자 이상이어야 합니다"

    if len(text) > 500:
        return False, "질문 내용은 최대 500자까지 가능합니다"

    return True, ""


def validate_rating_answer(answer: str) -> tuple[bool, str]:
    """평점 답변을 검증합니다.

    Args:
        answer: 검증할 평점 답변

    Returns:
        (유효 여부, 에러 메시지) 튜플
    """
    if not answer.isdigit():
        return False, "평점은 숫자여야 합니다"

    rating = int(answer)
    if rating < 1 or rating > 5:
        return False, "평점은 1-5 사이여야 합니다"

    return True, ""


def create_validator(validator_func: Callable[[str], tuple[bool, str]]) -> Callable[[str], str]:
    """Rich Prompt용 validator를 생성합니다.

    Args:
        validator_func: 검증 함수

    Returns:
        Rich Prompt에서 사용할 수 있는 검증 함수
    """
    def wrapper(value: str) -> str:
        is_valid, error = validator_func(value)
        if not is_valid:
            raise ValueError(error)
        return value
    return wrapper
