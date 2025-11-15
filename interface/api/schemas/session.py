from datetime import datetime
from pydantic import BaseModel, Field


class SurveySessionCreate(BaseModel):
    """설문 세션 생성 요청 스키마입니다.

    Attributes:
        respondent_id: 응답자 ID
    """
    respondent_id: str = Field(..., min_length=1, max_length=100, description="응답자 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "respondent_id": "respondent_001"
            }
        }


class SurveySessionResponse(BaseModel):
    """설문 세션 응답 스키마입니다.

    Attributes:
        id: 세션 ID
        survey_id: 설문 ID
        respondent_id: 응답자 ID
        started_at: 시작 일시
        completed_at: 완료 일시
        is_completed: 완료 여부
    """
    id: str = Field(..., description="세션 ID")
    survey_id: str = Field(..., description="설문 ID")
    respondent_id: str = Field(..., description="응답자 ID")
    started_at: datetime = Field(..., description="시작 일시")
    completed_at: datetime | None = Field(None, description="완료 일시")
    is_completed: bool = Field(..., description="완료 여부")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "session_123",
                "survey_id": "survey_456",
                "respondent_id": "respondent_001",
                "started_at": "2025-11-11T10:00:00",
                "completed_at": "2025-11-11T10:15:00",
                "is_completed": True
            }
        }


class SurveySessionListResponse(BaseModel):
    """설문 세션 목록 응답 스키마입니다.

    Attributes:
        sessions: 세션 목록
        total: 전체 세션 수
        completed: 완료된 세션 수
        in_progress: 진행 중인 세션 수
    """
    sessions: list[SurveySessionResponse] = Field(default_factory=list, description="세션 목록")
    total: int = Field(..., description="전체 세션 수")
    completed: int = Field(..., description="완료된 세션 수")
    in_progress: int = Field(..., description="진행 중인 세션 수")

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "session_1",
                        "survey_id": "survey_456",
                        "respondent_id": "respondent_001",
                        "started_at": "2025-11-11T10:00:00",
                        "completed_at": "2025-11-11T10:15:00",
                        "is_completed": True
                    },
                    {
                        "id": "session_2",
                        "survey_id": "survey_456",
                        "respondent_id": "respondent_002",
                        "started_at": "2025-11-11T11:00:00",
                        "completed_at": None,
                        "is_completed": False
                    }
                ],
                "total": 2,
                "completed": 1,
                "in_progress": 1
            }
        }


class CompleteSurveySessionResponse(BaseModel):
    """설문 세션 완료 응답 스키마입니다.

    Attributes:
        session_id: 세션 ID
        completed_at: 완료 일시
        message: 메시지
    """
    session_id: str = Field(..., description="세션 ID")
    completed_at: datetime = Field(..., description="완료 일시")
    message: str = Field(default="설문 응답이 완료되었습니다", description="메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "completed_at": "2025-11-11T10:15:00",
                "message": "설문 응답이 완료되었습니다"
            }
        }
