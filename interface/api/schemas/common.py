from typing import TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorResponse(BaseModel):
    """표준 에러 응답 스키마입니다.

    Attributes:
        error: 에러 타입
        detail: 에러 상세 정보
        timestamp: 에러 발생 시각
    """
    error: str = Field(..., description="에러 타입")
    detail: str = Field(..., description="에러 상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "인증 실패",
                "detail": "API 키가 유효하지 않습니다",
                "timestamp": "2025-11-11T10:30:00"
            }
        }


class SuccessResponse(BaseModel):
    """표준 성공 응답 스키마입니다.

    Attributes:
        message: 성공 메시지
        data: 응답 데이터 (선택)
    """
    message: str = Field(..., description="성공 메시지")
    data: dict | None = Field(default=None, description="응답 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "작업이 성공적으로 완료되었습니다",
                "data": {"id": "123", "status": "completed"}
            }
        }


class PaginationMeta(BaseModel):
    """페이지네이션 메타 정보입니다.

    Attributes:
        total: 전체 항목 수
        page: 현재 페이지 번호
        page_size: 페이지 크기
        total_pages: 전체 페이지 수
    """
    total: int = Field(..., description="전체 항목 수", ge=0)
    page: int = Field(..., description="현재 페이지 번호", ge=1)
    page_size: int = Field(..., description="페이지 크기", ge=1, le=100)
    total_pages: int = Field(..., description="전체 페이지 수", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "total": 50,
                "page": 1,
                "page_size": 20,
                "total_pages": 3
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 응답 스키마입니다.

    Attributes:
        items: 항목 목록
        meta: 페이지네이션 메타 정보
    """
    items: list[T] = Field(..., description="항목 목록")
    meta: PaginationMeta = Field(..., description="페이지네이션 메타 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {"id": "1", "name": "항목 1"},
                    {"id": "2", "name": "항목 2"}
                ],
                "meta": {
                    "total": 50,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 3
                }
            }
        }


class IdResponse(BaseModel):
    """ID 반환 응답 스키마입니다.

    Attributes:
        id: 생성된 리소스 ID
        message: 메시지
    """
    id: str = Field(..., description="생성된 리소스 ID")
    message: str = Field(..., description="메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "survey_123",
                "message": "설문이 생성되었습니다"
            }
        }


class MessageResponse(BaseModel):
    """메시지 응답 스키마입니다.

    Attributes:
        message: 메시지
    """
    message: str = Field(..., description="메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "작업이 완료되었습니다"
            }
        }
