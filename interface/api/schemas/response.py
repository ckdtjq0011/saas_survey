from pydantic import BaseModel, Field


class SubmitResponseRequest(BaseModel):
    """응답 제출 요청 스키마입니다.

    Attributes:
        respondent_id: 응답자 ID
        answers: 질문 ID와 답변의 딕셔너리
    """
    respondent_id: str = Field(..., min_length=1, max_length=100, description="응답자 ID")
    answers: dict[str, str] = Field(..., description="질문 ID와 답변의 딕셔너리")


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
