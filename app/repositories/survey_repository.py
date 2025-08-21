"""
Survey repository for managing survey data access.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import secrets

from app.models.form import Form, Question, QuestionType
from app.repositories.base_repository import BaseRepository


class SurveyRepository(BaseRepository[Form]):
    """Repository for survey-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(Form, db)
    
    def create_survey(
        self,
        title: str,
        description: Optional[str],
        owner_id: int,
        **kwargs
    ) -> Form:
        """Create a new survey with share token."""
        share_token = secrets.token_urlsafe(16)
        
        survey = self.create(
            title=title,
            description=description,
            owner_id=owner_id,
            share_token=share_token,
            **kwargs
        )
        return survey
    
    def get_by_share_token(self, token: str) -> Optional[Form]:
        """Get survey by share token."""
        return self.db.query(Form).filter(
            Form.share_token == token,
            Form.is_active == True
        ).first()
    
    def get_user_surveys(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Form]:
        """Get all surveys created by a user."""
        return self.db.query(Form).filter(
            Form.owner_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_public_surveys(self, skip: int = 0, limit: int = 100) -> List[Form]:
        """Get all public surveys."""
        return self.db.query(Form).filter(
            Form.is_public == True,
            Form.is_active == True
        ).offset(skip).limit(limit).all()
    
    def add_question(
        self,
        survey_id: int,
        title: str,
        question_type,
        order: int = 0,
        **kwargs
    ) -> Question:
        """Add a question to a survey."""
        # Convert string to QuestionType enum if needed
        if isinstance(question_type, str):
            question_type = QuestionType(question_type)
        
        question = Question(
            form_id=survey_id,
            title=title,
            question_type=question_type,
            order=order,
            **kwargs
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question
    
    def get_question(self, survey_id: int, question_id: int) -> Optional[Question]:
        """Get a specific question from a survey."""
        return self.db.query(Question).filter(
            Question.id == question_id,
            Question.form_id == survey_id
        ).first()
    
    def update_question(self, survey_id: int, question_id: int, **kwargs) -> Optional[Question]:
        """Update a question in a survey."""
        question = self.get_question(survey_id, question_id)
        if question:
            for key, value in kwargs.items():
                if hasattr(question, key):
                    setattr(question, key, value)
            self.db.commit()
            self.db.refresh(question)
        return question
    
    def delete_question(self, survey_id: int, question_id: int) -> bool:
        """Delete a question from a survey."""
        question = self.get_question(survey_id, question_id)
        if question:
            self.db.delete(question)
            self.db.commit()
            return True
        return False
    
    def duplicate_survey(self, survey_id: int, new_owner_id: int) -> Optional[Form]:
        """Create a copy of an existing survey."""
        original = self.get(survey_id)
        if not original:
            return None
        
        # Create new survey
        new_survey = self.create_survey(
            title=f"{original.title} (Copy)",
            description=original.description,
            owner_id=new_owner_id,
            is_public=original.is_public,
            is_active=True,
            requires_login=original.requires_login,
            limit_one_response=original.limit_one_response,
            show_progress_bar=original.show_progress_bar,
            shuffle_questions=original.shuffle_questions,
            confirmation_message=original.confirmation_message
        )
        
        # Copy questions
        for question in original.questions:
            self.add_question(
                survey_id=new_survey.id,
                title=question.title,
                question_type=question.question_type,
                order=question.order,
                description=question.description,
                required=question.required,
                options=question.options,
                settings=question.settings,
                validation_rules=question.validation_rules
            )
        
        return new_survey
    
    def is_owner(self, survey_id: int, user_id: int) -> bool:
        """Check if user is the owner of a survey."""
        survey = self.get(survey_id)
        return survey and survey.owner_id == user_id