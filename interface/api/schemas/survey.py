from pydantic import BaseModel, Field
from datetime import datetime


class CreateSurveyRequest(BaseModel):
    """설문 생성 요청 스키마입니다.

    Attributes:
        title: 설문 제목
        description: 설문 설명
    """
    title: str = Field(..., min_length=1, max_length=200, description="설문 제목")
    description: str = Field(..., min_length=1, max_length=1000, description="설문 설명")


class CreateSurveyResponse(BaseModel):
    """설문 생성 응답 스키마입니다.

    Attributes:
        survey_id: 생성된 설문 ID
        message: 응답 메시지
    """
    survey_id: str = Field(..., description="생성된 설문 ID")
    message: str = Field(default="설문이 생성되었습니다", description="응답 메시지")


class AddQuestionRequest(BaseModel):
    """질문 추가 요청 스키마입니다.

    Attributes:
        text: 질문 내용
        question_type: 질문 유형 (text, rating, choice)
        options: 객관식 선택지 (객관식인 경우에만)
    """
    text: str = Field(..., min_length=1, max_length=500, description="질문 내용")
    question_type: str = Field(..., pattern="^(text|rating|choice)$", description="질문 유형")
    options: list[str] | None = Field(None, description="객관식 선택지")


class AddQuestionResponse(BaseModel):
    """질문 추가 응답 스키마입니다.

    Attributes:
        question_id: 생성된 질문 ID
        message: 응답 메시지
    """
    question_id: str = Field(..., description="생성된 질문 ID")
    message: str = Field(default="질문이 추가되었습니다", description="응답 메시지")


class QuestionResponse(BaseModel):
    """질문 정보 응답 스키마입니다.

    Attributes:
        id: 질문 ID
        text: 질문 내용
        type: 질문 유형
        options: 객관식 선택지
    """
    id: str = Field(..., description="질문 ID")
    text: str = Field(..., description="질문 내용")
    type: str = Field(..., description="질문 유형")
    options: list[str] = Field(default_factory=list, description="객관식 선택지")


class SurveyResponse(BaseModel):
    """설문 상세 정보 응답 스키마입니다.

    Attributes:
        id: 설문 ID
        title: 설문 제목
        description: 설문 설명
        created_at: 생성 일시
        questions: 질문 목록
    """
    id: str = Field(..., description="설문 ID")
    title: str = Field(..., description="설문 제목")
    description: str = Field(..., description="설문 설명")
    created_at: str = Field(..., description="생성 일시")
    questions: list[QuestionResponse] = Field(default_factory=list, description="질문 목록")


class SurveyListItem(BaseModel):
    """설문 목록 항목 스키마입니다.

    Attributes:
        id: 설문 ID
        title: 설문 제목
        description: 설문 설명
        question_count: 질문 수
    """
    id: str = Field(..., description="설문 ID")
    title: str = Field(..., description="설문 제목")
    description: str = Field(..., description="설문 설명")
    question_count: str = Field(..., description="질문 수")


class SurveyListResponse(BaseModel):
    """설문 목록 응답 스키마입니다.

    Attributes:
        surveys: 설문 목록
        total: 전체 설문 수
    """
    surveys: list[SurveyListItem] = Field(default_factory=list, description="설문 목록")
    total: int = Field(..., description="전체 설문 수")
