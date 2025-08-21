from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.form import QuestionType


class QuestionBase(BaseModel):
    question_type: QuestionType
    title: str
    description: Optional[str] = None
    required: bool = False
    order: int = 0
    options: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_type: Optional[QuestionType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required: Optional[bool] = None
    order: Optional[int] = None
    options: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None


class Question(QuestionBase):
    id: int
    form_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FormBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True
    is_public: bool = True
    accepts_responses: bool = True
    requires_login: bool = False
    limit_one_response: bool = False
    show_progress_bar: bool = False
    shuffle_questions: bool = False
    confirmation_message: str = "Thank you for your response!"


class FormCreate(FormBase):
    questions: Optional[List[QuestionCreate]] = []


class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    accepts_responses: Optional[bool] = None
    requires_login: Optional[bool] = None
    limit_one_response: Optional[bool] = None
    show_progress_bar: Optional[bool] = None
    shuffle_questions: Optional[bool] = None
    confirmation_message: Optional[str] = None


class Form(FormBase):
    id: int
    owner_id: int
    share_token: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    questions: List[Question] = []
    
    class Config:
        from_attributes = True


class FormWithStats(Form):
    response_count: int = 0


class AnswerBase(BaseModel):
    question_id: int
    text_answer: Optional[str] = None
    number_answer: Optional[int] = None
    json_answer: Optional[Any] = None
    file_url: Optional[str] = None


class AnswerCreate(AnswerBase):
    pass


class Answer(AnswerBase):
    id: int
    response_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FormResponseBase(BaseModel):
    respondent_email: Optional[str] = None


class FormResponseCreate(FormResponseBase):
    answers: List[AnswerCreate]


class FormResponse(FormResponseBase):
    id: int
    form_id: int
    respondent_id: Optional[int] = None
    submitted_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    answers: List[Answer] = []
    
    class Config:
        from_attributes = True