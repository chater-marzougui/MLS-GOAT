from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, utils

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/teams", response_model=schemas.Team)
def create_team(team: schemas.TeamCreate, db: Session = Depends(database.get_db), current_admin: models.Team = Depends(utils.get_current_admin)):
    db_team = db.query(models.Team).filter(models.Team.name == team.name).first()
    if db_team:
        raise HTTPException(status_code=400, detail="Team already registered")
    
    hashed_password = utils.get_password_hash(team.password)
    new_team = models.Team(name=team.name, password_hash=hashed_password)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

@router.get("/teams", response_model=List[schemas.Team])
def read_teams(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db), current_admin: models.Team = Depends(utils.get_current_admin)):
    teams = db.query(models.Team).offset(skip).limit(limit).all()
    return teams

@router.delete("/teams/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Delete a team and all their submissions (admin only)"""
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Delete all submissions first
    db.query(models.Submission).filter(models.Submission.team_id == team_id).delete()
    
    # Delete the team
    db.delete(team)
    db.commit()
    return {"message": f"Team {team.name} and all submissions deleted"}

@router.post("/teams/batch")
async def create_teams_batch(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Batch create teams from CSV file (admin only)
    
    CSV format: name,password
    Example:
    team1,password123
    team2,password456
    
    Logic:
    - If team doesn't exist: create it
    - If team exists with different password: update password
    - If team exists with same password: skip (no change needed)
    """
    import csv
    import io
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    created_teams = []
    updated_teams = []
    skipped_teams = []
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header
        try:
            name = row.get('name', '').strip()
            password = row.get('password', '').strip()
            
            if not name or not password:
                errors.append(f"Row {row_num}: Missing name or password")
                continue
            
            # Check if team already exists
            existing = db.query(models.Team).filter(models.Team.name == name).first()
            
            if existing:
                # Check if password is the same
                if utils.verify_password(password, existing.password_hash):
                    # Same password - skip
                    skipped_teams.append(f"{name} (unchanged)")
                else:
                    # Different password - update it
                    existing.password_hash = utils.get_password_hash(password)
                    updated_teams.append(name)
            else:
                # Team doesn't exist - create it
                hashed_password = utils.get_password_hash(password)
                new_team = models.Team(name=name, password_hash=hashed_password)
                db.add(new_team)
                created_teams.append(name)
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "created": len(created_teams),
        "updated": len(updated_teams),
        "skipped": len(skipped_teams),
        "teams": created_teams,
        "updated_teams": updated_teams,
        "skipped_teams": skipped_teams,
        "errors": errors
    }

@router.get("/submissions", response_model=List[schemas.SubmissionResult])
def get_all_submissions(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Get all submissions (admin only)"""
    submissions = db.query(models.Submission)\
        .order_by(models.Submission.timestamp.desc())\
        .offset(skip).limit(limit).all()
    return submissions

@router.delete("/submissions/{submission_id}")
def delete_submission(
    submission_id: int,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Delete a specific submission (admin only)"""
    submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    db.delete(submission)
    db.commit()
    return {"message": f"Submission {submission_id} deleted"}

@router.get("/settings/leaderboard", response_model=schemas.LeaderboardSettings)
def get_leaderboard_settings(
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Get leaderboard settings (admin only)"""
    settings = db.query(models.LeaderboardSettings).first()
    if not settings:
        settings = models.LeaderboardSettings(show_private_scores=False)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@router.post("/settings/leaderboard", response_model=schemas.LeaderboardSettings)
def update_leaderboard_settings(
    show_private: bool,
    db: Session = Depends(database.get_db),
    current_admin: models.Team = Depends(utils.get_current_admin)
):
    """Toggle private score visibility (admin only)"""
    settings = db.query(models.LeaderboardSettings).first()
    if not settings:
        settings = models.LeaderboardSettings(show_private_scores=show_private) 
        db.add(settings)
    else:
        settings.show_private_scores = show_private
    
    db.commit()
    db.refresh(settings)
    return settings
