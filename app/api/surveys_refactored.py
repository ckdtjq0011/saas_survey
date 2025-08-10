"""
Survey management API with improved readability and clean architecture
"""
from __future__ import annotations
from typing import List, Optional
from datetime import datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.base import get_db
from app.models import Form, Question, FormResponse, Answer, User
from app.api.auth import get_current_user

router = APIRouter()


# ==================== Data Transfer Objects ====================

class QuestionData(BaseModel):
    """Represents a question in a survey"""
    question: str = Field(..., min_length=1, description="Question text")
    type: str = Field(..., description="Question type (e.g., multiple_choice, text)")
    options: List[str] = Field(default_factory=list, description="Available options for selection")
    required: bool = Field(True, description="Whether this question must be answered")


class SurveyCreate(BaseModel):
    """Data required to create a new survey"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    questions: List[QuestionData] = Field(..., min_items=1)
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = Field(None, gt=0)
    requires_login: bool = False


class SurveyUpdate(BaseModel):
    """Data for updating an existing survey"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = Field(None, gt=0)


class SurveyResponse(BaseModel):
    """Survey data returned to clients"""
    id: int
    title: str
    description: Optional[str]
    questions: List[dict]
    created_at: datetime
    share_token: Optional[str] = None
    share_link: Optional[str] = None
    response_count: int = 0
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = None
    is_active: bool = True
    requires_login: bool = False


class SurveyStatistics(BaseModel):
    """Statistical summary of survey responses"""
    total_responses: int
    completion_rate: float
    average_completion_time: Optional[float]
    questions: List[QuestionStatistics]


class QuestionStatistics(BaseModel):
    """Statistics for a single question"""
    question_id: int
    question_text: str
    response_count: int
    answer_distribution: dict


# ==================== Service Layer ====================

class SurveyService:
    """Business logic for survey operations"""
    
    @staticmethod
    def generate_share_token() -> str:
        """Generate a secure random token for survey sharing"""
        return secrets.token_urlsafe(16)
    
    @staticmethod
    def create_survey_with_questions(
        survey_data: SurveyCreate,
        owner_id: int,
        db: Session
    ) -> Form:
        """
        Create a survey with all its questions in a single transaction
        """
        survey = SurveyService._create_survey_entity(
            survey_data=survey_data,
            owner_id=owner_id
        )
        
        db.add(survey)
        db.flush()  # Get survey ID without committing
        
        questions = SurveyService._create_question_entities(
            survey_id=survey.id,
            questions_data=survey_data.questions
        )
        
        for question in questions:
            db.add(question)
        
        db.commit()
        db.refresh(survey)
        
        return survey
    
    @staticmethod
    def _create_survey_entity(
        survey_data: SurveyCreate,
        owner_id: int
    ) -> Form:
        """Create a Form entity from survey data"""
        return Form(
            title=survey_data.title,
            description=survey_data.description,
            owner_id=owner_id,
            is_public=True,
            is_active=True,
            share_token=SurveyService.generate_share_token(),
            deadline=survey_data.deadline,
            max_responses=survey_data.max_responses,
            requires_login=survey_data.requires_login,
        )
    
    @staticmethod
    def _create_question_entities(
        survey_id: int,
        questions_data: List[QuestionData]
    ) -> List[Question]:
        """Create Question entities from question data"""
        questions = []
        
        for position, question_data in enumerate(questions_data, start=1):
            question = Question(
                form_id=survey_id,
                title=question_data.question,
                question_type=question_data.type,
                options=question_data.options,
                required=question_data.required,
                order=position,
            )
            questions.append(question)
        
        return questions
    
    @staticmethod
    def is_survey_accepting_responses(survey: Form) -> tuple[bool, str]:
        """
        Check if a survey can accept new responses
        Returns: (is_accepting, reason_if_not)
        """
        if not survey.is_active:
            return False, "Survey is no longer active"
        
        if not survey.accepts_responses:
            return False, "Survey is not accepting responses"
        
        if survey.deadline and datetime.now() > survey.deadline:
            return False, "Survey deadline has passed"
        
        if survey.max_responses and len(survey.responses) >= survey.max_responses:
            return False, "Survey has reached maximum responses"
        
        return True, ""
    
    @staticmethod
    def calculate_survey_statistics(survey: Form) -> SurveyStatistics:
        """Calculate comprehensive statistics for a survey"""
        if not survey.responses:
            return SurveyStatistics(
                total_responses=0,
                completion_rate=0.0,
                average_completion_time=None,
                questions=[]
            )
        
        total_responses = len(survey.responses)
        
        question_stats = []
        for question in survey.questions:
            stats = SurveyService._calculate_question_statistics(question)
            question_stats.append(stats)
        
        return SurveyStatistics(
            total_responses=total_responses,
            completion_rate=100.0,  # TODO: Implement partial response tracking
            average_completion_time=None,  # TODO: Implement time tracking
            questions=question_stats
        )
    
    @staticmethod
    def _calculate_question_statistics(question: Question) -> QuestionStatistics:
        """Calculate statistics for a single question"""
        answer_distribution = {}
        response_count = 0
        
        for answer in question.answers:
            response_count += 1
            
            # Handle different answer types
            if question.question_type in ["multiple_choice", "checkbox", "dropdown"]:
                answer_value = answer.json_answer or answer.text_answer
                if answer_value:
                    answer_distribution[answer_value] = answer_distribution.get(answer_value, 0) + 1
            elif question.question_type == "scale":
                answer_value = answer.number_answer or answer.text_answer
                if answer_value:
                    answer_distribution[str(answer_value)] = answer_distribution.get(str(answer_value), 0) + 1
        
        return QuestionStatistics(
            question_id=question.id,
            question_text=question.title,
            response_count=response_count,
            answer_distribution=answer_distribution
        )


# ==================== Conversion Utilities ====================

class SurveyConverter:
    """Convert between database models and API responses"""
    
    @staticmethod
    def to_response(
        survey: Form,
        include_share_link: bool = False,
        base_url: str = "http://localhost:8000"
    ) -> SurveyResponse:
        """Convert a Form model to a SurveyResponse"""
        questions = SurveyConverter._format_questions(survey.questions)
        
        response = SurveyResponse(
            id=survey.id,
            title=survey.title,
            description=survey.description,
            questions=questions,
            created_at=survey.created_at,
            share_token=survey.share_token if include_share_link else None,
            response_count=len(survey.responses) if survey.responses else 0,
            deadline=survey.deadline,
            max_responses=survey.max_responses,
            is_active=survey.is_active,
            requires_login=survey.requires_login,
        )
        
        if include_share_link and survey.share_token:
            response.share_link = f"{base_url}/surveys/s/{survey.share_token}"
        
        return response
    
    @staticmethod
    def _format_questions(questions: List[Question]) -> List[dict]:
        """Format questions for API response"""
        formatted_questions = []
        
        for question in sorted(questions, key=lambda q: q.order):
            formatted_question = {
                "id": question.id,
                "question": question.title,
                "type": question.question_type,
                "options": question.options or [],
                "required": question.required,
                "order": question.order,
            }
            formatted_questions.append(formatted_question)
        
        return formatted_questions


# ==================== API Endpoints ====================

@router.post("/", response_model=SurveyResponse)
async def create_survey(
    survey_data: SurveyCreate,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Create a new survey with questions
    
    Anonymous users are assigned owner_id = 1 (guest user)
    """
    guest_user_id = 1
    
    survey = SurveyService.create_survey_with_questions(
        survey_data=survey_data,
        owner_id=guest_user_id,
        db=db
    )
    
    return SurveyConverter.to_response(survey, include_share_link=True)


@router.get("/", response_model=List[SurveyResponse])
async def list_surveys(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
) -> List[SurveyResponse]:
    """
    List all public surveys with optional filtering
    """
    query = db.query(Form).filter(Form.is_public == True)
    
    if is_active is not None:
        query = query.filter(Form.is_active == is_active)
    
    surveys = query.offset(skip).limit(limit).all()
    
    return [
        SurveyConverter.to_response(survey) 
        for survey in surveys
    ]


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey(
    survey_id: int,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Get a specific survey by ID
    """
    survey = db.query(Form).filter(Form.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    return SurveyConverter.to_response(survey, include_share_link=True)


@router.get("/s/{share_token}", response_model=SurveyResponse)
async def get_survey_by_token(
    share_token: str,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Get a survey using its share token
    """
    survey = db.query(Form).filter(Form.share_token == share_token).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found or invalid share token"
        )
    
    is_accepting, reason = SurveyService.is_survey_accepting_responses(survey)
    if not is_accepting:
        survey.accepts_responses = False  # Update status for response
    
    return SurveyConverter.to_response(survey)


@router.put("/{survey_id}", response_model=SurveyResponse)
async def update_survey(
    survey_id: int,
    update_data: SurveyUpdate,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Update survey properties (title, description, status, etc.)
    """
    survey = db.query(Form).filter(Form.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Update only provided fields
    update_fields = update_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(survey, field, value)
    
    db.commit()
    db.refresh(survey)
    
    return SurveyConverter.to_response(survey, include_share_link=True)


@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a survey and all its associated data
    """
    survey = db.query(Form).filter(Form.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    db.delete(survey)
    db.commit()
    
    return {"message": "Survey deleted successfully"}


@router.post("/{survey_id}/duplicate", response_model=SurveyResponse)
async def duplicate_survey(
    survey_id: int,
    db: Session = Depends(get_db)
) -> SurveyResponse:
    """
    Create a copy of an existing survey
    """
    original_survey = db.query(Form).filter(Form.id == survey_id).first()
    
    if not original_survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    # Create survey data from original
    survey_data = SurveyCreate(
        title=f"{original_survey.title} (Copy)",
        description=original_survey.description or "",
        questions=[
            QuestionData(
                question=q.title,
                type=q.question_type,
                options=q.options or [],
                required=q.required
            )
            for q in sorted(original_survey.questions, key=lambda x: x.order)
        ],
        deadline=None,  # Reset deadline for copy
        max_responses=original_survey.max_responses,
        requires_login=original_survey.requires_login
    )
    
    # Create the duplicate
    guest_user_id = 1
    duplicate = SurveyService.create_survey_with_questions(
        survey_data=survey_data,
        owner_id=guest_user_id,
        db=db
    )
    
    return SurveyConverter.to_response(duplicate, include_share_link=True)


@router.get("/{survey_id}/stats", response_model=SurveyStatistics)
async def get_survey_statistics(
    survey_id: int,
    db: Session = Depends(get_db)
) -> SurveyStatistics:
    """
    Get statistical analysis of survey responses
    """
    survey = db.query(Form).filter(Form.id == survey_id).first()
    
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )
    
    return SurveyService.calculate_survey_statistics(survey)