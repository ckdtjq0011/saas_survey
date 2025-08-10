from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
import json
from typing import List

from app.db.base import get_db
from app.models import Form, FormResponse, User
from app.api.auth import get_current_user

router = APIRouter()


def generate_csv(form: Form):
    output = io.StringIO()
    
    headers = ["Response ID", "Respondent", "Submitted At"]
    for q in form.questions:
        headers.append(q.title)
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for response in form.responses:
        row = [response.id, response.respondent_email or "Anonymous", response.submitted_at]
        
        answer_dict = {a.question_id: a.text_answer for a in response.answers}
        for q in form.questions:
            row.append(answer_dict.get(q.id, ""))
        
        writer.writerow(row)
    
    output.seek(0)
    return output


def generate_json(form: Form):
    data = {
        "survey": {
            "id": form.id,
            "title": form.title,
            "description": form.description,
            "created_at": str(form.created_at),
        },
        "questions": [
            {
                "id": q.id,
                "title": q.title,
                "type": q.question_type,
                "options": q.options
            }
            for q in form.questions
        ],
        "responses": [
            {
                "id": r.id,
                "respondent": r.respondent_email or "Anonymous",
                "submitted_at": str(r.submitted_at),
                "answers": [
                    {
                        "question_id": a.question_id,
                        "answer": a.text_answer
                    }
                    for a in r.answers
                ]
            }
            for r in form.responses
        ]
    }
    return json.dumps(data, indent=2)


@router.get("/{survey_id}/csv")
def export_csv(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    csv_data = generate_csv(form)
    
    return StreamingResponse(
        csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=survey_{survey_id}_responses.csv"
        }
    )


@router.get("/{survey_id}/json")
def export_json(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    form = db.query(Form).filter(Form.id == survey_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Survey not found")
    if form.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    json_data = generate_json(form)
    
    return StreamingResponse(
        io.StringIO(json_data),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=survey_{survey_id}_responses.json"
        }
    )