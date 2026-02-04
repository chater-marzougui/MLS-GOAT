from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, utils

router = APIRouter(prefix="/qa", tags=["qa"])

@router.get("/questions", response_model=List[schemas.Question])
def get_questions(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_team: models.Team = Depends(utils.get_current_team)
):
    """Get all questions with up to 2 latest answers (prioritizing admin responses)"""
    questions = db.query(models.Question)\
        .order_by(models.Question.created_at.desc())\
        .offset(skip).limit(limit).all()
    
    result = []
    for q in questions:
        # Get all answers for this question
        all_answers = db.query(models.Answer)\
            .filter(models.Answer.question_id == q.id)\
            .join(models.Team)\
            .order_by(models.Answer.created_at.desc())\
            .all()
        
        # Prioritize admin answers
        admin_answers = [a for a in all_answers if a.author.is_admin]
        non_admin_answers = [a for a in all_answers if not a.author.is_admin]
        
        # Take up to 2 answers, prioritizing admin
        latest_answers = (admin_answers[:1] + non_admin_answers)[:2]
        
        result.append({
            "id": q.id,
            "team_id": q.team_id,
            "title": q.title,
            "content": q.content,
            "author_name": q.author.name,
            "author_is_admin": q.author.is_admin,
            "created_at": q.created_at,
            "updated_at": q.updated_at,
            "answer_count": len(all_answers),
            "latest_answers": [
                {
                    "id": a.id,
                    "question_id": a.question_id,
                    "team_id": a.team_id,
                    "content": a.content,
                    "author_name": a.author.name,
                    "author_is_admin": a.author.is_admin,
                    "created_at": a.created_at,
                    "updated_at": a.updated_at
                }
                for a in latest_answers
            ]
        })
    
    return result

@router.get("/questions/{question_id}", response_model=schemas.QuestionDetail)
def get_question(
    question_id: int,
    db: Session = Depends(database.get_db),
    current_team: models.Team = Depends(utils.get_current_team)
):
    """Get a single question with all answers"""
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Get all answers
    all_answers = db.query(models.Answer)\
        .filter(models.Answer.question_id == question_id)\
        .join(models.Team)\
        .order_by(models.Answer.created_at.asc())\
        .all()
    
    return {
        "id": question.id,
        "team_id": question.team_id,
        "title": question.title,
        "content": question.content,
        "author_name": question.author.name,
        "author_is_admin": question.author.is_admin,
        "created_at": question.created_at,
        "updated_at": question.updated_at,
        "answer_count": len(all_answers),
        "latest_answers": [],
        "all_answers": [
            {
                "id": a.id,
                "question_id": a.question_id,
                "team_id": a.team_id,
                "content": a.content,
                "author_name": a.author.name,
                "author_is_admin": a.author.is_admin,
                "created_at": a.created_at,
                "updated_at": a.updated_at
            }
            for a in all_answers
        ]
    }

@router.post("/questions", response_model=schemas.Question)
def create_question(
    question: schemas.QuestionCreate,
    db: Session = Depends(database.get_db),
    current_team: models.Team = Depends(utils.get_current_team)
):
    """Create a new question"""
    new_question = models.Question(
        team_id=current_team.id,
        title=question.title,
        content=question.content
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    return {
        "id": new_question.id,
        "team_id": new_question.team_id,
        "title": new_question.title,
        "content": new_question.content,
        "author_name": current_team.name,
        "author_is_admin": current_team.is_admin,
        "created_at": new_question.created_at,
        "updated_at": new_question.updated_at,
        "answer_count": 0,
        "latest_answers": []
    }

@router.post("/questions/{question_id}/answers", response_model=schemas.Answer)
def create_answer(
    question_id: int,
    answer: schemas.AnswerCreate,
    db: Session = Depends(database.get_db),
    current_team: models.Team = Depends(utils.get_current_team)
):
    """Create an answer to a question"""
    # Check if question exists
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    new_answer = models.Answer(
        question_id=question_id,
        team_id=current_team.id,
        content=answer.content
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    
    return {
        "id": new_answer.id,
        "question_id": new_answer.question_id,
        "team_id": new_answer.team_id,
        "content": new_answer.content,
        "author_name": current_team.name,
        "author_is_admin": current_team.is_admin,
        "created_at": new_answer.created_at,
        "updated_at": new_answer.updated_at
    }

@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Delete a question (admin only)"""
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    return {"message": f"Question {question_id} deleted"}

@router.delete("/answers/{answer_id}")
def delete_answer(
    answer_id: int,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Delete an answer (admin only)"""
    answer = db.query(models.Answer).filter(models.Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    db.delete(answer)
    db.commit()
    return {"message": f"Answer {answer_id} deleted"}
