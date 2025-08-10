from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.base import get_db
from app.models import Form, Question, User
from app.schemas.form import (
    FormCreate, FormUpdate, Form as FormSchema, 
    FormWithStats, QuestionCreate, QuestionUpdate,
    Question as QuestionSchema
)
from app.api.users import get_current_user

router = APIRouter()


@router.post("/", response_model=FormSchema)
def create_form(
    form: FormCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Create form
    db_form = Form(
        **form.dict(exclude={"questions"}),
        owner_id=current_user.id
    )
    db.add(db_form)
    db.flush()  # Get form ID without committing
    
    # Add questions if provided
    for idx, question_data in enumerate(form.questions):
        db_question = Question(
            **question_data.dict(),
            form_id=db_form.id,
            order=idx
        )
        db.add(db_question)
    
    db.commit()
    db.refresh(db_form)
    return db_form


@router.get("/", response_model=List[FormWithStats])
def list_forms(
    skip: int = 0,
    limit: int = 100,
    my_forms_only: bool = False,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Form)
    
    if my_forms_only and current_user:
        query = query.filter(Form.owner_id == current_user.id)
    elif not current_user:
        query = query.filter(Form.is_public == True)
    
    forms = query.offset(skip).limit(limit).all()
    
    # Add response count
    result = []
    for form in forms:
        form_dict = form.__dict__.copy()
        form_dict["response_count"] = len(form.responses)
        result.append(FormWithStats(**form_dict))
    
    return result


@router.get("/{form_id}", response_model=FormSchema)
def get_form(form_id: int, db: Session = Depends(get_db)):
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Check if form is public or user is owner
    # TODO: Add proper permission checking
    
    return form


@router.put("/{form_id}", response_model=FormSchema)
def update_form(
    form_id: int,
    form_update: FormUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Check ownership
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this form")
    
    # Update form
    for field, value in form_update.dict(exclude_unset=True).items():
        setattr(form, field, value)
    
    db.commit()
    db.refresh(form)
    return form


@router.delete("/{form_id}")
def delete_form(
    form_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    # Check ownership
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this form")
    
    db.delete(form)
    db.commit()
    return {"message": "Form deleted successfully"}


# Question management endpoints
@router.post("/{form_id}/questions", response_model=QuestionSchema)
def add_question(
    form_id: int,
    question: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form exists and user owns it
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this form")
    
    # Get next order number
    max_order = db.query(Question).filter(Question.form_id == form_id).count()
    
    db_question = Question(
        **question.dict(),
        form_id=form_id,
        order=question.order if question.order else max_order
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


@router.put("/{form_id}/questions/{question_id}", response_model=QuestionSchema)
def update_question(
    form_id: int,
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form and question exist
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this form")
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.form_id == form_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Update question
    for field, value in question_update.dict(exclude_unset=True).items():
        setattr(question, field, value)
    
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{form_id}/questions/{question_id}")
def delete_question(
    form_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check form and question exist
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this form")
    
    question = db.query(Question).filter(
        Question.id == question_id,
        Question.form_id == form_id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}