"""
Response repository for managing survey response data access.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.form import FormResponse, Answer, Form, Question
from app.repositories.base_repository import BaseRepository


class ResponseRepository(BaseRepository[FormResponse]):
    """Repository for survey response-related database operations."""
    
    def __init__(self, db: Session):
        super().__init__(FormResponse, db)
    
    def create_response(
        self,
        survey_id: int,
        respondent_email: Optional[str] = None,
        respondent_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> FormResponse:
        """Create a new survey response."""
        response = self.create(
            form_id=survey_id,
            respondent_email=respondent_email,
            respondent_id=respondent_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return response
    
    def add_answer(
        self,
        response_id: int,
        question_id: int,
        text_answer: Optional[str] = None,
        number_answer: Optional[int] = None,
        json_answer: Optional[Any] = None,
        file_url: Optional[str] = None
    ) -> Answer:
        """Add an answer to a response."""
        answer = Answer(
            response_id=response_id,
            question_id=question_id,
            text_answer=text_answer,
            number_answer=number_answer,
            json_answer=json_answer,
            file_url=file_url
        )
        self.db.add(answer)
        self.db.commit()
        self.db.refresh(answer)
        return answer
    
    def get_survey_responses(
        self,
        survey_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[FormResponse]:
        """Get all responses for a survey."""
        return self.db.query(FormResponse).filter(
            FormResponse.form_id == survey_id
        ).offset(skip).limit(limit).all()
    
    def get_user_response(
        self,
        survey_id: int,
        user_id: int
    ) -> Optional[FormResponse]:
        """Get a user's response to a survey."""
        return self.db.query(FormResponse).filter(
            FormResponse.form_id == survey_id,
            FormResponse.respondent_id == user_id
        ).first()
    
    def get_response_by_email(
        self,
        survey_id: int,
        email: str
    ) -> Optional[FormResponse]:
        """Get a response by respondent email."""
        return self.db.query(FormResponse).filter(
            FormResponse.form_id == survey_id,
            FormResponse.respondent_email == email
        ).first()
    
    def has_user_responded(
        self,
        survey_id: int,
        user_id: Optional[int] = None,
        email: Optional[str] = None
    ) -> bool:
        """Check if a user has already responded to a survey."""
        query = self.db.query(FormResponse).filter(
            FormResponse.form_id == survey_id
        )
        
        if user_id:
            query = query.filter(FormResponse.respondent_id == user_id)
        elif email:
            query = query.filter(FormResponse.respondent_email == email)
        else:
            return False
        
        return query.count() > 0
    
    def count_survey_responses(self, survey_id: int) -> int:
        """Count total responses for a survey."""
        return self.db.query(FormResponse).filter(
            FormResponse.form_id == survey_id
        ).count()
    
    def get_survey_statistics(self, survey_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a survey."""
        # Get total responses
        total_responses = self.count_survey_responses(survey_id)
        
        # Get questions and their answers
        questions = self.db.query(Question).filter(
            Question.form_id == survey_id
        ).order_by(Question.order).all()
        
        question_stats = []
        for question in questions:
            q_stat = {
                "id": question.id,
                "title": question.title,
                "type": question.question_type.value if hasattr(question.question_type, 'value') else question.question_type,
                "required": question.required,
                "answer_distribution": {}
            }
            
            # Get answer distribution
            answers = self.db.query(Answer).filter(
                Answer.question_id == question.id
            ).all()
            
            for answer in answers:
                # Determine the answer value
                answer_value = None
                if answer.text_answer:
                    answer_value = answer.text_answer
                elif answer.number_answer is not None:
                    answer_value = str(answer.number_answer)
                elif answer.json_answer:
                    answer_value = str(answer.json_answer)
                
                if answer_value:
                    if answer_value not in q_stat["answer_distribution"]:
                        q_stat["answer_distribution"][answer_value] = 0
                    q_stat["answer_distribution"][answer_value] += 1
            
            question_stats.append(q_stat)
        
        return {
            "total_responses": total_responses,
            "questions": question_stats
        }
    
    def delete_response_answers(self, response_id: int) -> None:
        """Delete all answers for a response."""
        self.db.query(Answer).filter(
            Answer.response_id == response_id
        ).delete()
        self.db.commit()
    
    def update_response_answers(
        self,
        response_id: int,
        answers_data: List[Dict[str, Any]]
    ) -> List[Answer]:
        """Update answers for a response (delete old and create new)."""
        # Delete existing answers
        self.delete_response_answers(response_id)
        
        # Create new answers
        new_answers = []
        for answer_data in answers_data:
            answer = self.add_answer(
                response_id=response_id,
                **answer_data
            )
            new_answers.append(answer)
        
        return new_answers