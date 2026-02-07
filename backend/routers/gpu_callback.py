"""GPU callback endpoints - receive results from GPU server"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from .. import models, database
import json
import os

router = APIRouter(prefix="/gpu-callback", tags=["gpu-callback"])

GPU_SCORER_SECRET_KEY = os.getenv('GPU_SCORER_SECRET_KEY')

if not GPU_SCORER_SECRET_KEY:
    raise ValueError("GPU_SCORER_SECRET_KEY environment variable not set")

def verify_gpu_secret(x_gpu_secret: str = Header(...)):
    """Verify the GPU secret key"""
    if x_gpu_secret != GPU_SCORER_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid GPU secret key")
    return True


@router.post("/submission-queued")
async def submission_queued(
    request: Request,
    db: Session = Depends(database.get_db),
    _: bool = Depends(verify_gpu_secret)
):
    """
    GPU server notifies that a submission has been queued
    Create pending entry in database
    """
    data = await request.json()
    
    submission_id = data['submission_id']
    team_id = data['team_id']
    task_id = data['task_id']
    filename = data['filename']
    
    # Create pending submission
    sub = models.Submission(
        team_id=team_id,
        task_id=task_id,
        filename=filename,
        public_score=0.0,
        private_score=0.0,
        details=json.dumps({
            "status": "queued",
            "submission_id": submission_id
        })
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return {
        "status": "ok",
        "message": "Submission recorded",
        "db_id": sub.id
    }


@router.post("/result")
async def receive_result(
    request: Request,
    db: Session = Depends(database.get_db),
    _: bool = Depends(verify_gpu_secret)
):
    """
    GPU server sends evaluation results
    Update database with scores
    """
    data = await request.json()
    
    submission_id = data['submission_id']
    team_id = data.get('team_id')
    status = data['status']
    score = data.get('score', 0)
    details = data.get('details', {})
    
    # Find submission by team_id and recent timestamp
    # (since we don't store submission_id in DB initially)
    submission = db.query(models.Submission).filter(
        models.Submission.team_id == team_id,
        models.Submission.task_id == 2
    ).order_by(models.Submission.timestamp.desc()).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Update with results
    if status == 'completed':
        submission.public_score = score
        submission.private_score = score
        submission.details = json.dumps({
            "status": "completed",
            "submission_id": submission_id,
            **details
        })
    else:
        # Failed
        submission.details = json.dumps({
            "status": "failed",
            "submission_id": submission_id,
            "error": data.get('error', 'Unknown error')
        })
    
    db.commit()
    
    return {
        "status": "ok",
        "message": "Results recorded",
        "db_id": submission.id
    }