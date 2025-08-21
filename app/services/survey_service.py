"""
Survey service for managing survey business logic.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status

from app.repositories.survey_repository import SurveyRepository
from app.repositories.response_repository import ResponseRepository
from app.models.form import Form, Question


class SurveyService:
    """Service for survey-related business operations."""
    
    def __init__(self, survey_repo: SurveyRepository, response_repo: ResponseRepository):
        self.survey_repo = survey_repo
        self.response_repo = response_repo
    
    def create_survey(
        self,
        title: str,
        description: Optional[str],
        owner_id: int,
        questions: List[Dict[str, Any]],
        **kwargs
    ) -> Form:
        """Create a new survey with questions."""
        # Create the survey
        survey = self.survey_repo.create_survey(
            title=title,
            description=description,
            owner_id=owner_id,
            **kwargs
        )
        
        # Add questions
        for idx, question_data in enumerate(questions):
            # Make a copy to avoid modifying the original
            q_data = question_data.copy()
            
            # Extract required fields
            title = q_data.pop('title', '')
            question_type = q_data.pop('question_type', 'short_text')
            order = q_data.pop('order', idx)
            
            self.survey_repo.add_question(
                survey_id=survey.id,
                title=title,
                question_type=question_type,
                order=order,
                **q_data
            )
        
        return survey
    
    def get_survey(self, survey_id: int) -> Form:
        """Get a survey by ID."""
        survey = self.survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        return survey
    
    def get_survey_by_token(self, token: str) -> Form:
        """Get a survey by share token."""
        survey = self.survey_repo.get_by_share_token(token)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        # Check if survey is accepting responses
        self._validate_survey_availability(survey)
        return survey
    
    def list_surveys(
        self,
        user_id: Optional[int] = None,
        my_surveys_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Form]:
        """List surveys based on criteria."""
        if my_surveys_only and user_id:
            return self.survey_repo.get_user_surveys(user_id, skip, limit)
        else:
            return self.survey_repo.get_public_surveys(skip, limit)
    
    def update_survey(
        self,
        survey_id: int,
        user_id: int,
        **update_data
    ) -> Form:
        """Update a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this survey"
            )
        
        # Update survey
        survey = self.survey_repo.update(survey_id, **update_data)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        return survey
    
    def delete_survey(self, survey_id: int, user_id: int) -> None:
        """Delete a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this survey"
            )
        
        # Delete survey (cascade will handle questions and responses)
        if not self.survey_repo.delete(survey_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
    
    def duplicate_survey(self, survey_id: int, user_id: int) -> Form:
        """Create a copy of a survey."""
        new_survey = self.survey_repo.duplicate_survey(survey_id, user_id)
        if not new_survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        return new_survey
    
    def get_survey_statistics(self, survey_id: int, user_id: int) -> Dict[str, Any]:
        """Get statistics for a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view statistics"
            )
        
        return self.response_repo.get_survey_statistics(survey_id)
    
    def add_question(
        self,
        survey_id: int,
        user_id: int,
        question_data: Dict[str, Any]
    ) -> Question:
        """Add a question to a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this survey"
            )
        
        # Get current question count for order
        survey = self.get_survey(survey_id)
        order = len(survey.questions)
        
        return self.survey_repo.add_question(
            survey_id=survey_id,
            order=order,
            **question_data
        )
    
    def update_question(
        self,
        survey_id: int,
        question_id: int,
        user_id: int,
        **update_data
    ) -> Question:
        """Update a question in a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this survey"
            )
        
        question = self.survey_repo.update_question(survey_id, question_id, **update_data)
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        return question
    
    def delete_question(
        self,
        survey_id: int,
        question_id: int,
        user_id: int
    ) -> None:
        """Delete a question from a survey."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this survey"
            )
        
        if not self.survey_repo.delete_question(survey_id, question_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
    
    def _validate_survey_availability(self, survey: Form) -> None:
        """Validate if a survey is available for responses."""
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
            response_count = self.response_repo.count_survey_responses(survey.id)
            if response_count >= survey.max_responses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Survey has reached maximum responses"
                )