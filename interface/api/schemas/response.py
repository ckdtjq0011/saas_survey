from pydantic import BaseModel, Field


class SubmitResponseRequest(BaseModel):
    """응답 제출 요청 스키마입니다.

    Attributes:
        respondent_id: 응답자 ID
        answers: 질문 ID와 답변의 딕셔너리
        session_id: 세션 ID
        time_spent_data: 질문 ID와 소요 시간(초)의 딕셔너리
    """
    respondent_id: str = Field(..., min_length=1, max_length=100, description="응답자 ID")
    answers: dict[str, str] = Field(..., description="질문 ID와 답변의 딕셔너리")
    session_id: str = Field(..., description="세션 ID")
    time_spent_data: dict[str, int] = Field(..., description="질문 ID와 소요 시간(초)의 딕셔너리")


class SubmitResponseResponse(BaseModel):
    """응답 제출 응답 스키마입니다.

    Attributes:
        message: 응답 메시지
        respondent_id: 응답자 ID
    """
    message: str = Field(default="응답이 제출되었습니다", description="응답 메시지")
    respondent_id: str = Field(..., description="응답자 ID")


class QuestionResultResponse(BaseModel):
    """질문별 결과 응답 스키마입니다.

    Attributes:
        question: 질문 내용
        type: 질문 유형
        count: 응답 수
        average: 평균 평점 (rating 유형인 경우)
        distribution: 선택지별 분포 (choice 유형인 경우)
        answers: 텍스트 답변 목록 (text 유형인 경우)
    """
    question: str = Field(..., description="질문 내용")
    type: str = Field(..., description="질문 유형")
    count: int = Field(..., description="응답 수")
    average: float | None = Field(None, description="평균 평점")
    distribution: dict[str, int] | None = Field(None, description="선택지별 분포")
    answers: list[str] | None = Field(None, description="텍스트 답변 목록")


class SurveyResultsResponse(BaseModel):
    """설문 결과 응답 스키마입니다.

    Attributes:
        survey_id: 설문 ID
        results: 질문 ID별 결과 딕셔너리
    """
    survey_id: str = Field(..., description="설문 ID")
    results: dict[str, QuestionResultResponse] = Field(default_factory=dict, description="질문별 결과")


class UpdateResponseRequest(BaseModel):
    """응답 수정 요청 스키마입니다.

    Attributes:
        answer: 수정할 답변
    """
    answer: str = Field(..., min_length=1, description="수정할 답변")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "수정된 답변 내용"
            }
        }


class ResponseDetailResponse(BaseModel):
    """응답 상세 정보 스키마입니다.

    Attributes:
        id: 응답 ID
        survey_id: 설문 ID
        question_id: 질문 ID
        answer: 답변
        respondent_id: 응답자 ID
        answered_at: 응답 일시
        session_id: 세션 ID
        time_spent_seconds: 소요 시간 (초)
    """
    id: str = Field(..., description="응답 ID")
    survey_id: str = Field(..., description="설문 ID")
    question_id: str = Field(..., description="질문 ID")
    answer: str = Field(..., description="답변")
    respondent_id: str = Field(..., description="응답자 ID")
    answered_at: str = Field(..., description="응답 일시")
    session_id: str = Field(..., description="세션 ID")
    time_spent_seconds: int = Field(default=0, description="소요 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "response_123",
                "survey_id": "survey_456",
                "question_id": "question_789",
                "answer": "매우 만족",
                "respondent_id": "respondent_001",
                "answered_at": "2025-11-11T10:30:00",
                "session_id": "session_abc",
                "time_spent_seconds": 45
            }
        }


class ResponseHistoryResponse(BaseModel):
    """응답 수정 이력 응답 스키마입니다.

    Attributes:
        id: 이력 ID
        response_id: 응답 ID
        old_answer: 이전 답변
        new_answer: 새 답변
        modified_at: 수정 일시
        modified_by: 수정자 ID
    """
    id: str = Field(..., description="이력 ID")
    response_id: str = Field(..., description="응답 ID")
    old_answer: str = Field(..., description="이전 답변")
    new_answer: str = Field(..., description="새 답변")
    modified_at: str = Field(..., description="수정 일시")
    modified_by: str = Field(..., description="수정자 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "history_123",
                "response_id": "response_456",
                "old_answer": "만족",
                "new_answer": "매우 만족",
                "modified_at": "2025-11-11T11:00:00",
                "modified_by": "user_789"
            }
        }


class ResponseListResponse(BaseModel):
    """응답 목록 응답 스키마입니다.

    Attributes:
        responses: 응답 목록
        total: 전체 응답 수
    """
    responses: list[ResponseDetailResponse] = Field(default_factory=list, description="응답 목록")
    total: int = Field(..., description="전체 응답 수")

    class Config:
        json_schema_extra = {
            "example": {
                "responses": [
                    {
                        "id": "response_1",
                        "survey_id": "survey_456",
                        "question_id": "question_1",
                        "answer": "매우 만족",
                        "respondent_id": "respondent_001",
                        "answered_at": "2025-11-11T10:30:00",
                        "session_id": "session_abc",
                        "time_spent_seconds": 45
                    }
                ],
                "total": 1
            }
        }
