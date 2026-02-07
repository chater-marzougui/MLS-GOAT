from fastapi import Header, APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, date
import shutil
import os
import zipfile
import uuid
import json
from .. import models, schemas, database, utils
from ..scoring import scorer

router = APIRouter(prefix="/submit", tags=["submission"])

# CONFIG (Should be in env)
GT_TASK1_DIR = "./data/gt_task1"
GPU_SCORER_SECRET_KEY = os.getenv('GPU_SCORER_SECRET_KEY')

# Ensure the scorer knows about GT
scorer.gt_dir_task1 = GT_TASK1_DIR

LIMIT_TASK1 = 20
LIMIT_TASK2 = 30

@router.post("/task1", response_model=schemas.SubmissionResult)
async def submit_task1(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_team: models.Team = Depends(utils.get_current_team)):
    # Check limit
    count = db.query(models.Submission).filter(
        models.Submission.team_id == current_team.id,
        models.Submission.task_id == 1
    ).count()
    
    if count >= LIMIT_TASK1:
        raise HTTPException(status_code=400, detail=f"Submission limit reached for Task 1 ({LIMIT_TASK1})")
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Task 1 requires a .zip file")

    # Save and Process
    submission_id = str(uuid.uuid4())
    temp_dir = os.path.join("temp", submission_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    zip_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Call Scorer
        # Scorer expects a directory containing .pt files
        # We need to find where they are (could be in a subfolder in the zip)
        # Simple walk to find first folder with .pt files?
        # Or assume flat? Prompt says "one folder of images we zip it". 
        # Usually it unzips to a folder.
        
        target_dir = temp_dir
        # simple heuristic: if temp_dir contains only one folder, enter it
        items = os.listdir(temp_dir)
        # Filter out the zip itself
        items = [i for i in items if i != file.filename]
        
        if len(items) == 1 and os.path.isdir(os.path.join(temp_dir, items[0])):
            target_dir = os.path.join(temp_dir, items[0])
            
        score, details = scorer.evaluate_task1(target_dir)
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Save to DB
    sub = models.Submission(
        team_id=current_team.id,
        task_id=1,
        filename=file.filename,
        public_score=score,
        private_score=score, # Same for now
        details=json.dumps(details)
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return sub

def verify_gpu_secret(x_gpu_secret: str = Header(...)):
    """Verify the GPU secret key"""
    if x_gpu_secret != GPU_SCORER_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid GPU secret key")
    return True

@router.get("/check-limit/task2/{team_id}")
def check_task2_limit(
    team_id: int,
    db: Session = Depends(database.get_db),
    _: bool = Depends(verify_gpu_secret)
):
    """Check if team has reached submission limit for Task 2"""
    count = db.query(models.Submission).filter(
        models.Submission.team_id == team_id,
        models.Submission.task_id == 2
    ).count()
    
    if count >= LIMIT_TASK2:
        raise HTTPException(status_code=429, detail=f"Limit reached ({LIMIT_TASK2})")
    
    return {
        "team_id": team_id,
        "count": count,
        "limit": LIMIT_TASK2,
        "remaining": LIMIT_TASK2 - count
    }