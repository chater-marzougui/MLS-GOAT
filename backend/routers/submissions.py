from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
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

@router.post("/task2", response_model=schemas.SubmissionResult)
async def submit_task2(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_team: models.Team = Depends(utils.get_current_team)):
    # Check limit
    count = db.query(models.Submission).filter(
        models.Submission.team_id == current_team.id,
        models.Submission.task_id == 2
    ).count()
    
    if count >= LIMIT_TASK2:
        raise HTTPException(status_code=400, detail=f"Submission limit reached for Task 2 ({LIMIT_TASK2})")
    
    if not file.filename.endswith('.onnx'):
        raise HTTPException(status_code=400, detail="Task 2 requires a .onnx file")

    submission_id = str(uuid.uuid4())
    temp_dir = os.path.join("temp", submission_id)
    os.makedirs(temp_dir, exist_ok=True)
    model_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(model_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        score, details = scorer.evaluate_task2(model_path)
        
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    sub = models.Submission(
        team_id=current_team.id,
        task_id=2,
        filename=file.filename,
        public_score=score,
        private_score=score,
        details=json.dumps(details)
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    return sub
