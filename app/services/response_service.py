"""
Response service for managing survey response business logic.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from app.repositories.survey_repository import SurveyRepository
from app.repositories.response_repository import ResponseRepository
from app.models.form import FormResponse, Form, Question


class ResponseService:
    """Service for survey response-related business operations."""
    
    def __init__(self, survey_repo: SurveyRepository, response_repo: ResponseRepository):
        self.survey_repo = survey_repo
        self.response_repo = response_repo
    
    def submit_response(
        self,
        survey_id: int,
        answers: List[Dict[str, Any]],
        respondent_email: Optional[str] = None,
        respondent_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> FormResponse:
        """Submit a response to a survey."""
        # Get and validate survey
        survey = self._get_and_validate_survey(survey_id)
        
        # Check for authentication requirement
        if survey.requires_login and not respondent_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Login required to submit response"
            )
        
        # Check for duplicate response if limited to one
        if survey.limit_one_response:
            self._check_duplicate_response(survey_id, respondent_id, respondent_email)
        
        # Validate answers against questions
        self._validate_answers(survey.questions, answers)
        
        # Create response
        response = self.response_repo.create_response(
            survey_id=survey_id,
            respondent_email=respondent_email or "Anonymous",
            respondent_id=respondent_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Add answers
        for answer_data in answers:
            self.response_repo.add_answer(
                response_id=response.id,
                **answer_data
            )
        
        return response
    
    def get_response(self, response_id: int, user_id: Optional[int] = None) -> FormResponse:
        """Get a specific response."""
        response = self.response_repo.get(response_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response not found"
            )
        
        # Check authorization
        survey = self.survey_repo.get(response.form_id)
        if user_id:
            # User can view if they own the survey or submitted the response
            is_owner = survey.owner_id == user_id
            is_respondent = response.respondent_id == user_id
            
            if not (is_owner or is_respondent):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this response"
                )
        
        return response
    
    def list_survey_responses(
        self,
        survey_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[FormResponse]:
        """List all responses for a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view responses"
            )
        
        return self.response_repo.get_survey_responses(survey_id, skip, limit)
    
    def update_response(
        self,
        response_id: int,
        user_id: int,
        answers: List[Dict[str, Any]]
    ) -> FormResponse:
        """Update a response."""
        response = self.response_repo.get(response_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response not found"
            )
        
        # Check authorization (only respondent can update)
        if response.respondent_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this response"
            )
        
        # Get survey and validate answers
        survey = self.survey_repo.get(response.form_id)
        self._validate_answers(survey.questions, answers)
        
        # Update answers
        self.response_repo.update_response_answers(response_id, answers)
        
        return self.response_repo.get(response_id)
    
    def delete_response(self, response_id: int, user_id: int) -> None:
        """Delete a response."""
        response = self.response_repo.get(response_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Response not found"
            )
        
        # Check authorization (survey owner or respondent can delete)
        survey = self.survey_repo.get(response.form_id)
        is_owner = survey.owner_id == user_id
        is_respondent = response.respondent_id == user_id
        
        if not (is_owner or is_respondent):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this response"
            )
        
        self.response_repo.delete(response_id)
    
    def _get_and_validate_survey(self, survey_id: int) -> Form:
        """Get and validate survey availability."""
        survey = self.survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        # Validate survey is accepting responses
        if not survey.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Survey is not active"
            )
        
        if not survey.accepts_responses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Survey is not accepting responses"
            )
        
        # Check deadline
        if survey.deadline and datetime.utcnow() > survey.deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Survey deadline has passed"
            )
        
        # Check response limit
        if survey.max_responses:
            response_count = self.response_repo.count_survey_responses(survey_id)
            if response_count >= survey.max_responses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Survey has reached maximum responses"
                )
        
        return survey
    
    def _check_duplicate_response(
        self,
        survey_id: int,
        user_id: Optional[int],
        email: Optional[str]
    ) -> None:
        """Check if user has already responded."""
        if self.response_repo.has_user_responded(survey_id, user_id, email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted a response"
            )
    
    def _validate_answers(
        self,
        questions: List[Question],
        answers: List[Dict[str, Any]]
    ) -> None:
        """Validate answers against survey questions."""
        # Create a map of question IDs for quick lookup
        question_map = {q.id: q for q in questions}
        
        # Check each answer
        for answer in answers:
            question_id = answer.get("question_id")
            if not question_id or question_id not in question_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid question ID: {question_id}"
                )
            
            question = question_map[question_id]
            
            # Check required questions
            if question.required:
                has_answer = (
                    answer.get("text_answer") or
                    answer.get("number_answer") is not None or
                    answer.get("json_answer") or
                    answer.get("file_url")
                )
                if not has_answer:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Question '{question.title}' is required"
                    )
            
            # Validate answer type based on question type
            self._validate_answer_type(question, answer)
    
    def _validate_answer_type(self, question: Question, answer: Dict[str, Any]) -> None:
        """Validate answer type matches question type."""
        question_type = question.question_type.value if hasattr(question.question_type, 'value') else str(question.question_type)
        
        if question_type in ["short_text", "long_text", "email"]:
            if answer.get("number_answer") is not None or answer.get("json_answer"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid answer type for question '{question.title}'"
                )
        
        elif question_type == "number":
            if answer.get("number_answer") is None and answer.get("text_answer"):
                # Try to convert text to number
                try:
                    float(answer.get("text_answer"))
                except (ValueError, TypeError):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Question '{question.title}' requires a number"
                    )
        
        elif question_type in ["multiple_choice", "dropdown"]:
            # Validate against options if provided
            if question.options:
                answer_value = answer.get("text_answer") or answer.get("json_answer")
                if answer_value and answer_value not in question.options:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid option for question '{question.title}'"
                    )
        
        elif question_type == "checkbox":
            # Should be stored as JSON array
            if not answer.get("json_answer") and answer.get("text_answer"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question '{question.title}' requires multiple selections"
                )