from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import secrets

from app.db.base import get_db
from app.models import Form, Question, FormResponse, Answer, User
from app.api.auth import get_current_user

router = APIRouter()


class QuestionData(BaseModel):
    question: str
    type: str
    options: List[str]
    required: bool = True


class SurveyCreate(BaseModel):
    title: str
    description: str
    questions: List[QuestionData]
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = None
    requires_login: bool = False


class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = None


class SurveyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    questions: List[dict]
    created_at: datetime
    share_link: Optional[str] = None
    response_count: int = 0
    deadline: Optional[datetime] = None
    max_responses: Optional[int] = None


class SurveyStats(BaseModel):
    total_responses: int
    questions: List[dict]


def create_form(title: str, description: str, owner_id: int, deadline: Optional[datetime], max_responses: Optional[int], requires_login: bool, db: Session):
    share_token = secrets.token_urlsafe(16)
    form = Form(
        title=title,
        description=description,
        owner_id=owner_id,
        is_public=True,
        is_active=True,
        share_token=share_token,
        deadline=deadline,
        max_responses=max_responses,
        requires_login=requires_login,
    )
    db.add(form)
    db.flush()
    return form


def create_question(form_id: int, title: str, type: str, options: List[str], required: bool, order: int, db: Session):
    question = Question(
        form_id=form_id,
        title=title,
        question_type=type,
        options=options,
        required=required,
        order=order,
    )
    db.add(question)
    return question


def form_to_response(form: Form, include_share_link: bool = False) -> SurveyResponse:
    response_count = len(form.responses) if form.responses else 0
    return SurveyResponse(
        id=form.id,
        title=form.title,
        description=form.description,
        questions=[
            {
                "id": q.id,
                "question": q.title,
                "type": q.question_type,
                "options": q.options,
                "required": q.required,
                "order": q.order,
            }
            for q in form.questions
        ],
        created_at=form.created_at,
        share_link=f"/s/{form.share_token}" if include_share_link and hasattr(form, 'share_token') else None,
        response_count=response_count,
        deadline=form.deadline if hasattr(form, 'deadline') else None,
        max_responses=form.max_responses if hasattr(form, 'max_responses') else None,
    )


def check_survey_limits(form: Form):
    if hasattr(form, 'deadline') and form.deadline and datetime.utcnow() > form.deadline:
        raise HTTPException(status_code=400, detail="Survey deadline has passed")
    
    if hasattr(form, 'max_responses') and form.max_responses:
        current_responses = len(form.responses) if form.responses else 0
        if current_responses >= form.max_responses:
            raise HTTPException(status_code=400, detail="Survey has reached maximum responses")


@router.post("/", response_model=SurveyResponse)
def create_survey(
    survey: SurveyCreate, 
    db: Session = Depends(get_db)
):
    owner_id = 1
    
    db_form = create_form(
        survey.title, 
        survey.description, 
        owner_id, 
        survey.deadline,
        survey.max_responses,
        survey.requires_login,
        db=db
    )
    
    for idx, q_data in enumerate(survey.questions):
        create_question(
            db_form.id, 
            q_data.question, 
            q_data.type, 
            q_data.options,
            q_data.required, 
            idx, 
            db
        )
    
    db.commit()
    db.refresh(db_form)
    return form_to_response(db_form, include_share_link=True)


@router.get("/", response_model=List[SurveyResponse])
def get_surveys(
    skip: int = 0, 
    limit: int = 100, 
    my_surveys: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Form).filter(Form.is_active == True)
    
    if not my_surveys:
        query = query.filter(Form.is_public == True)
    
    forms = query.offset(skip).limit(limit).all()
    return [form_to_response(form) for form in forms]


@router.get("/s/{share_token}", response_model=SurveyResponse)
def get_survey_by_share_link(share_token: str, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.share_token == share_token).first()
    if not form or not form.is_active:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    check_survey_limits(form)
    return form_to_response(form)


@router.get("/{survey_id}", response_model=SurveyResponse)
def get_survey(survey_id: int, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    return form_to_response(form, include_share_link=True)


@router.put("/{survey_id}", response_model=SurveyResponse)
def update_survey(
    survey_id: int,
    survey_update: SurveyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if survey_update.title is not None:
        form.title = survey_update.title
    if survey_update.description is not None:
        form.description = survey_update.description
    if survey_update.is_active is not None:
        form.is_active = survey_update.is_active
    if survey_update.deadline is not None:
        form.deadline = survey_update.deadline
    if survey_update.max_responses is not None:
        form.max_responses = survey_update.max_responses
    
    db.commit()
    db.refresh(form)
    return form_to_response(form, include_share_link=True)


@router.delete("/{survey_id}")
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(form)
    db.commit()
    return {"message": "Survey deleted successfully"}


@router.get("/{survey_id}/stats", response_model=SurveyStats)
def get_survey_stats(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    stats = {"total_responses": len(form.responses), "questions": []}
    
    for question in form.questions:
        q_stats = {
            "id": question.id,
            "question": question.title,
            "type": question.question_type,
            "answers": {}
        }
        
        for answer in question.answers:
            answer_text = answer.text_answer or str(answer.json_answer)
            q_stats["answers"][answer_text] = q_stats["answers"].get(answer_text, 0) + 1
        
        stats["questions"].append(q_stats)
    
    return stats


@router.post("/{survey_id}/duplicate", response_model=SurveyResponse)
def duplicate_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    original = db.query(Form).filter(Form.id == survey_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="Survey not found")
    
    new_form = Form(
        title=f"{original.title} (Copy)",
        description=original.description,
        owner_id=current_user.id,
        is_public=True,
        is_active=True,
        share_token=secrets.token_urlsafe(16),
        requires_login=original.requires_login if hasattr(original, 'requires_login') else False,
    )
    db.add(new_form)
    db.flush()
    
    for q in original.questions:
        new_question = Question(
            form_id=new_form.id,
            title=q.title,
            question_type=q.question_type,
            options=q.options,
            required=q.required,
            order=q.order,
        )
        db.add(new_question)
    
    db.commit()
    db.refresh(new_form)
    return form_to_response(new_form, include_share_link=True)