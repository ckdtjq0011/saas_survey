"""
Export service for managing data export operations.
"""
import csv
import json
import io
from typing import Dict, Any, List
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.repositories.survey_repository import SurveyRepository
from app.repositories.response_repository import ResponseRepository


class ExportService:
    """Service for data export operations."""
    
    def __init__(self, survey_repo: SurveyRepository, response_repo: ResponseRepository):
        self.survey_repo = survey_repo
        self.response_repo = response_repo
    
    def export_responses_csv(self, survey_id: int, user_id: int) -> StreamingResponse:
        """Export survey responses as CSV."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to export this survey"
            )
        
        # Get survey and responses
        survey = self.survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        responses = self.response_repo.get_survey_responses(survey_id, limit=10000)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ["Response ID", "Submitted At", "Respondent"]
        for question in survey.questions:
            headers.append(question.title)
        writer.writerow(headers)
        
        # Write response data
        for response in responses:
            row = [
                response.id,
                response.submitted_at.isoformat() if response.submitted_at else "",
                response.respondent_email or "Anonymous"
            ]
            
            # Create answer map for quick lookup
            answer_map = {}
            for answer in response.answers:
                answer_value = self._get_answer_value(answer)
                answer_map[answer.question_id] = answer_value
            
            # Add answers in question order
            for question in survey.questions:
                row.append(answer_map.get(question.id, ""))
            
            writer.writerow(row)
        
        # Prepare response
        output.seek(0)
        filename = f"survey_{survey_id}_responses.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    def export_responses_json(self, survey_id: int, user_id: int) -> StreamingResponse:
        """Export survey responses as JSON."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to export this survey"
            )
        
        # Get survey and responses
        survey = self.survey_repo.get(survey_id)
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        responses = self.response_repo.get_survey_responses(survey_id, limit=10000)
        
        # Build JSON structure
        export_data = {
            "survey": {
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "created_at": survey.created_at.isoformat() if survey.created_at else None,
                "questions": [
                    {
                        "id": q.id,
                        "title": q.title,
                        "type": q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type),
                        "required": q.required,
                        "options": q.options
                    }
                    for q in survey.questions
                ]
            },
            "responses": []
        }
        
        # Add responses
        for response in responses:
            response_data = {
                "id": response.id,
                "submitted_at": response.submitted_at.isoformat() if response.submitted_at else None,
                "respondent": response.respondent_email or "Anonymous",
                "answers": []
            }
            
            # Add answers
            for answer in response.answers:
                answer_data = {
                    "question_id": answer.question_id,
                    "question": answer.question.title if answer.question else None,
                    "value": self._get_answer_value(answer)
                }
                response_data["answers"].append(answer_data)
            
            export_data["responses"].append(response_data)
        
        # Prepare response
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        filename = f"survey_{survey_id}_responses.json"
        
        return StreamingResponse(
            io.BytesIO(json_str.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    def export_statistics(self, survey_id: int, user_id: int) -> Dict[str, Any]:
        """Export survey statistics."""
        # Check ownership
        if not self.survey_repo.is_owner(survey_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view statistics"
            )
        
        return self.response_repo.get_survey_statistics(survey_id)
    
    def _get_answer_value(self, answer) -> str:
        """Extract the appropriate value from an answer."""
        if answer.text_answer:
            return answer.text_answer
        elif answer.number_answer is not None:
            return str(answer.number_answer)
        elif answer.json_answer:
            if isinstance(answer.json_answer, list):
                return ", ".join(str(item) for item in answer.json_answer)
            return str(answer.json_answer)
        elif answer.file_url:
            return answer.file_url
        return ""