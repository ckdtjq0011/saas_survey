from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models import Form, FormResponse, Answer, User
from app.schemas.form import FormResponseCreate, FormResponse as FormResponseSchema
from app.api.users import get_current_user

router = APIRouter()


@router.post("/{form_id}/submit", response_model=FormResponseSchema)
async def submit_response(
    form_id: int,
    response_data: FormResponseCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    # Get form
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Check if form accepts responses
    if not form.accepts_responses:
        raise HTTPException(status_code=400, detail="This form is not accepting responses")
    
    # Check if login is required
    if form.requires_login:
        raise HTTPException(status_code=401, detail="Login required to submit this form")
    
    # Create response
    db_response = FormResponse(
        form_id=form_id,
        respondent_id=None,
        respondent_email=response_data.respondent_email,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(db_response)
    db.flush()
    
    # Add answers
    for answer_data in response_data.answers:
        db_answer = Answer(
            response_id=db_response.id,
            **answer_data.dict()
        )
        db.add(db_answer)
    
    db.commit()
    db.refresh(db_response)
    return db_response


@router.get("/{form_id}/responses", response_model=List[FormResponseSchema])
def get_form_responses(
    form_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form exists and user owns it
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view responses for this form")
    
    responses = db.query(FormResponse).filter(
        FormResponse.form_id == form_id
    ).offset(skip).limit(limit).all()
    
    return responses


@router.get("/{form_id}/responses/{response_id}", response_model=FormResponseSchema)
def get_response(
    form_id: int,
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form exists and user owns it
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view responses for this form")
    
    response = db.query(FormResponse).filter(
        FormResponse.id == response_id,
        FormResponse.form_id == form_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    return response


@router.delete("/{form_id}/responses/{response_id}")
def delete_response(
    form_id: int,
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form exists and user owns it
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete responses for this form")
    
    response = db.query(FormResponse).filter(
        FormResponse.id == response_id,
        FormResponse.form_id == form_id
    ).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    db.delete(response)
    db.commit()
    return {"message": "Response deleted successfully"}


@router.get("/{form_id}/statistics")
def get_form_statistics(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form exists and user owns it
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view statistics for this form")
    
    # Get response count
    total_responses = db.query(FormResponse).filter(FormResponse.form_id == form_id).count()
    
    # Get statistics per question
    questions_stats = []
    for question in form.questions:
        answers = db.query(Answer).filter(Answer.question_id == question.id).all()
        
        stats = {
            "question_id": question.id,
            "question_title": question.title,
            "question_type": question.question_type,
            "total_answers": len(answers),
            "required": question.required
        }
        
        # Calculate specific stats based on question type
        if question.question_type in ["multiple_choice", "checkbox", "dropdown"]:
            # Count option selections
            option_counts = {}
            for answer in answers:
                if answer.json_answer:
                    if isinstance(answer.json_answer, list):
                        for option in answer.json_answer:
                            option_counts[option] = option_counts.get(option, 0) + 1
                    else:
                        option_counts[answer.json_answer] = option_counts.get(answer.json_answer, 0) + 1
            stats["option_counts"] = option_counts
        
        elif question.question_type == "scale":
            # Calculate average for scale questions
            scale_values = [a.number_answer for a in answers if a.number_answer is not None]
            if scale_values:
                stats["average"] = sum(scale_values) / len(scale_values)
                stats["min"] = min(scale_values)
                stats["max"] = max(scale_values)
        
        questions_stats.append(stats)
    
    return {
        "form_id": form_id,
        "form_title": form.title,
        "total_responses": total_responses,
        "questions_statistics": questions_stats,
        "created_at": form.created_at,
        "last_response": db.query(FormResponse).filter(
            FormResponse.form_id == form_id
        ).order_by(FormResponse.submitted_at.desc()).first().submitted_at if total_responses > 0 else None
    }