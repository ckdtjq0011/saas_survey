from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.base import get_db
from app.models import Form, Question, FormResponse, Answer, User
from app.api.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


class AnswerData(BaseModel):
    question_index: int
    answer: str


class ResponseCreate(BaseModel):
    survey_id: int
    respondent: Optional[str] = None
    answers: List[AnswerData]


class ResponseUpdate(BaseModel):
    answers: List[AnswerData]


class ResponseData(BaseModel):
    id: int
    survey_id: int
    respondent: str
    answers: List[dict]
    created_at: datetime


def get_form_with_questions(survey_id: int, db: Session):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if not form.is_active:
        raise HTTPException(status_code=400, detail="Survey is not active")
    return form


def validate_survey_access(form: Form, user: Optional[User] = None):
    if form.requires_login and not user:
        raise HTTPException(status_code=401, detail="Login required to submit response")
    
    if hasattr(form, 'deadline') and form.deadline and datetime.utcnow() > form.deadline:
        raise HTTPException(status_code=400, detail="Survey deadline has passed")
    
    if hasattr(form, 'max_responses') and form.max_responses:
        current_responses = len(form.responses) if form.responses else 0
        if current_responses >= form.max_responses:
            raise HTTPException(status_code=400, detail="Survey has reached maximum responses")


def validate_answers(questions: List[Question], answers: List[AnswerData]):
    for answer_data in answers:
        if answer_data.question_index >= len(questions):
            raise HTTPException(status_code=400, detail=f"Invalid question index: {answer_data.question_index}")
        
        question = questions[answer_data.question_index]
        
        if question.required and not answer_data.answer:
            raise HTTPException(status_code=400, detail=f"Question '{question.title}' is required")
        
        if question.question_type == "MULTIPLE_CHOICE" and question.options:
            if answer_data.answer not in question.options:
                raise HTTPException(status_code=400, detail=f"Invalid option for question '{question.title}'")
        
        if question.question_type == "NUMBER":
            try:
                float(answer_data.answer)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Question '{question.title}' requires a number")


def check_duplicate_response(form: Form, user: Optional[User], respondent_email: str, db: Session):
    if form.limit_one_response:
        existing = None
        if user:
            existing = db.query(FormResponse).filter(
                FormResponse.form_id == form.id,
                FormResponse.respondent_id == user.id
            ).first()
        elif respondent_email:
            existing = db.query(FormResponse).filter(
                FormResponse.form_id == form.id,
                FormResponse.respondent_email == respondent_email
            ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="You have already submitted a response")


def create_form_response(form_id: int, respondent_email: str, user_id: Optional[int], db: Session):
    response = FormResponse(
        form_id=form_id,
        respondent_email=respondent_email,
        respondent_id=user_id
    )
    db.add(response)
    db.flush()
    return response


def create_answer(response_id: int, question_id: int, answer_text: str, db: Session):
    answer = Answer(
        response_id=response_id,
        question_id=question_id,
        text_answer=answer_text
    )
    db.add(answer)
    return answer


@router.post("/", response_model=ResponseData)
def submit_response(
    response: ResponseCreate, 
    db: Session = Depends(get_db)
):
    form = get_form_with_questions(response.survey_id, db)
    validate_survey_access(form, None)
    
    questions = form.questions
    validate_answers(questions, response.answers)
    
    respondent_email = response.respondent or "Anonymous"
    user_id = None
    
    check_duplicate_response(form, None, respondent_email, db)
    
    db_response = create_form_response(form.id, respondent_email, user_id, db)
    
    for answer_data in response.answers:
        question = questions[answer_data.question_index]
        create_answer(db_response.id, question.id, answer_data.answer, db)
    
    db.commit()
    db.refresh(db_response)
    
    return ResponseData(
        id=db_response.id,
        survey_id=db_response.form_id,
        respondent=db_response.respondent_email or "Anonymous",
        answers=[
            {"question_index": i, "answer": ans.answer}
            for i, ans in enumerate(response.answers)
        ],
        created_at=db_response.submitted_at
    )


@router.get("/{response_id}", response_model=ResponseData)
def get_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response = db.query(FormResponse).filter(FormResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    form = response.form
    if form.owner_id != current_user.id and response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    answers = [
        {
            "question_id": ans.question_id,
            "answer": ans.text_answer,
            "question": ans.question.title if ans.question else None
        }
        for ans in response.answers
    ]
    
    return ResponseData(
        id=response.id,
        survey_id=response.form_id,
        respondent=response.respondent_email or "Anonymous",
        answers=answers,
        created_at=response.submitted_at
    )


@router.put("/{response_id}", response_model=ResponseData)
def update_response(
    response_id: int,
    response_update: ResponseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response = db.query(FormResponse).filter(FormResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    if response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    form = response.form
    questions = form.questions
    validate_answers(questions, response_update.answers)
    
    db.query(Answer).filter(Answer.response_id == response_id).delete()
    
    for answer_data in response_update.answers:
        question = questions[answer_data.question_index]
        create_answer(response.id, question.id, answer_data.answer, db)
    
    db.commit()
    db.refresh(response)
    
    return ResponseData(
        id=response.id,
        survey_id=response.form_id,
        respondent=response.respondent_email or "Anonymous",
        answers=[
            {"question_index": i, "answer": ans.answer}
            for i, ans in enumerate(response_update.answers)
        ],
        created_at=response.submitted_at
    )


@router.delete("/{response_id}")
def delete_response(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response = db.query(FormResponse).filter(FormResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    form = response.form
    if form.owner_id != current_user.id and response.respondent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(response)
    db.commit()
    return {"message": "Response deleted successfully"}