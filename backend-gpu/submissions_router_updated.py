from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
import redis
import json
import time
from .. import models, schemas, database
from ..auth import get_current_team

router = APIRouter(prefix="/submit", tags=["submissions"])

# Redis connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Existing task1 submission (unchanged)
@router.post("/task1", response_model=schemas.SubmissionResult)
async def submit_task1(
    file: UploadFile = File(...),
    current_team: models.Team = Depends(get_current_team),
    db: Session = Depends(database.get_db)
):
    """Submit Task 1 - Image reconstruction"""
    # Your existing task1 implementation
    pass


@router.post("/task2", response_model=schemas.SubmissionResult)
async def submit_task2(
    file: UploadFile = File(...),
    current_team: models.Team = Depends(get_current_team),
    db: Session = Depends(database.get_db)
):
    """Submit Task 2 - ONNX Model Evaluation (Queued)"""
    
    if not file.filename.endswith('.onnx'):
        raise HTTPException(status_code=400, detail="Only .onnx files are accepted")
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > 40 * 1024 * 1024:  # 40 MB
        raise HTTPException(status_code=400, detail="Model file must be less than 40MB")
    
    # Save uploaded file
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = int(time.time())
    temp_filename = f"{current_team.name}_task2_{timestamp}.onnx"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create submission record
    submission = models.Submission(
        team_id=current_team.id,
        task_id=2,
        filename=temp_filename,
        public_score=0.0,  # Will be updated by worker
        private_score=0.0,
        details=json.dumps({"status": "queued"})
    )
    
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Queue evaluation job
    job_data = {
        'submission_id': submission.id,
        'team_id': current_team.id,
        'model_path': temp_path,
        'test_data_path': './data/test_task2.npy',  # Adjust to your test data path
        'timestamp': timestamp
    }
    
    try:
        # Push job to Redis queue
        redis_client.lpush('evaluation_queue', json.dumps(job_data))
        
        # Set submission as pending
        redis_client.hset(
            f'result:{submission.id}',
            mapping={'status': 'queued', 'submission_id': str(submission.id)}
        )
        redis_client.expire(f'result:{submission.id}', 3600)
        
    except Exception as e:
        # Cleanup on failure
        db.delete(submission)
        db.commit()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")
    
    return schemas.SubmissionResult(
        id=submission.id,
        team_id=submission.team_id,
        task_id=submission.task_id,
        public_score=0.0,
        private_score=0.0,
        timestamp=submission.timestamp,
        details=json.dumps({"status": "queued", "message": "Your submission is in the queue and will be evaluated shortly"})
    )


@router.get("/task2/status/{submission_id}")
async def get_submission_status(
    submission_id: int,
    current_team: models.Team = Depends(get_current_team),
    db: Session = Depends(database.get_db)
):
    """Check the status of a Task 2 submission"""
    
    # Verify submission belongs to team
    submission = db.query(models.Submission).filter(
        models.Submission.id == submission_id,
        models.Submission.team_id == current_team.id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Check Redis for results
    result_data = redis_client.hgetall(f'result:{submission_id}')
    
    if not result_data:
        return {
            "submission_id": submission_id,
            "status": "queued",
            "message": "Your submission is in the queue"
        }
    
    status = result_data.get('status', 'unknown')
    
    if status == 'completed':
        # Update submission with results
        score = float(result_data.get('score', 0))
        details = result_data.get('details', '{}')
        
        submission.public_score = score
        submission.private_score = score  # Or different scoring logic
        submission.details = details
        db.commit()
        
        return {
            "submission_id": submission_id,
            "status": "completed",
            "score": score,
            "details": json.loads(details) if isinstance(details, str) else details
        }
    
    elif status == 'failed':
        return {
            "submission_id": submission_id,
            "status": "failed",
            "error": result_data.get('error', 'Unknown error')
        }
    
    else:
        return {
            "submission_id": submission_id,
            "status": status,
            "message": "Evaluation in progress"
        }


@router.get("/queue/status")
async def get_queue_status(current_team: models.Team = Depends(get_current_team)):
    """Get current queue status"""
    try:
        queue_length = redis_client.llen('evaluation_queue')
        return {
            "queue_length": queue_length,
            "message": f"There are {queue_length} submissions in the queue"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")
