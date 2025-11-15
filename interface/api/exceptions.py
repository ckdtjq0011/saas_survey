from datetime import datetime
from typing import TypeVar, Generic
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from domain.value_objects.result import Result, Success, Failure


T = TypeVar("T")
E = TypeVar("E")


class ErrorResponse(BaseModel):
    """표준 에러 응답 스키마입니다.

    Attributes:
        error: 에러 타입
        detail: 에러 상세 정보
        timestamp: 에러 발생 시각
    """
    error: str
    detail: str
    timestamp: datetime


def handle_result(result: Result[T, str], not_found_msg: str | None = None) -> T:
    """Result 패턴을 HTTPException으로 변환합니다.

    Args:
        result: Result 객체
        not_found_msg: 404 에러로 처리할 메시지 (옵션)

    Returns:
        Success인 경우 값 반환

    Raises:
        HTTPException: Failure인 경우 HTTP 예외 발생
    """
    if isinstance(result, Success):
        return result.value

    error_msg = result.error

    if not_found_msg and not_found_msg in error_msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )

    if "권한" in error_msg or "소유자" in error_msg:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_msg
        )

    if "존재하지 않" in error_msg or "찾을 수 없" in error_msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )

    if "중복" in error_msg or "이미 존재" in error_msg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_msg
        )

    if "검증" in error_msg or "유효하지 않" in error_msg or "형식" in error_msg:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_msg
    )


async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """전역 예외 핸들러입니다.

    Args:
        request: HTTP 요청
        exc: 발생한 예외

    Returns:
        에러 응답
    """
    logger.exception("예외 발생")

    error_response = ErrorResponse(
        error="서버 오류",
        detail="서버에서 오류가 발생했습니다. 관리자에게 문의하세요.",
        timestamp=datetime.now()
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


class AuthenticationException(HTTPException):
    """인증 실패 예외입니다."""

    def __init__(self, detail: str = "인증에 실패했습니다"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(HTTPException):
    """권한 부족 예외입니다."""

    def __init__(self, detail: str = "권한이 부족합니다"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
