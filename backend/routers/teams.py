from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, utils

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/me/submissions", response_model=List[schemas.SubmissionHistory])
def get_my_submissions(
    current_team: models.Team = Depends(utils.get_current_team),
    db: Session = Depends(database.get_db)
):
    """Get all submissions for the current team"""
    submissions = db.query(models.Submission)\
        .filter(models.Submission.team_id == current_team.id)\
        .order_by(models.Submission.timestamp.desc())\
        .all()
    return submissions

@router.get("/me/submissions/{task_id}", response_model=List[schemas.SubmissionHistory])
def get_my_submissions_by_task(
    task_id: int,
    current_team: models.Team = Depends(utils.get_current_team),
    db: Session = Depends(database.get_db)
):
    """Get submissions for a specific task for the current team"""
    submissions = db.query(models.Submission)\
        .filter(
            models.Submission.team_id == current_team.id,
            models.Submission.task_id == task_id
        )\
        .order_by(models.Submission.timestamp.desc())\
        .all()
    return submissions
