from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Success(Generic[T]):
    """성공 결과를 나타냅니다.

    Attributes:
        value: 성공 시 반환값
    """
    value: T

    def is_success(self) -> bool:
        """성공 여부를 반환합니다."""
        return True

    def is_failure(self) -> bool:
        """실패 여부를 반환합니다."""
        return False


@dataclass(frozen=True, slots=True)
class Failure(Generic[E]):
    """실패 결과를 나타냅니다.

    Attributes:
        error: 실패 사유
    """
    error: E

    def is_success(self) -> bool:
        """성공 여부를 반환합니다."""
        return False

    def is_failure(self) -> bool:
        """실패 여부를 반환합니다."""
        return True


Result = Success[T] | Failure[E]
