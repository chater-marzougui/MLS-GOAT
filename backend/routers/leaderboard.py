from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from .. import models, schemas, database

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

def get_leaderboard_settings(db: Session):
    """Get current leaderboard settings"""
    settings = db.query(models.LeaderboardSettings).first()
    if not settings:
        # Create default settings
        settings = models.LeaderboardSettings(show_private_scores=False)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def get_leaderboard_data(db: Session, task_id: int, limit: Optional[int] = None, show_private: bool = False):
    """Get leaderboard data with optional private scores"""
    # Subquery to find best public score per team
    subquery = db.query(
        models.Submission.team_id,
        func.max(models.Submission.public_score).label("max_public_score")
    ).filter(models.Submission.task_id == task_id).group_by(models.Submission.team_id).subquery()
    
    # Get team names and scores
    query = db.query(
        models.Team.name, 
        subquery.c.max_public_score
    ).join(subquery, models.Team.id == subquery.c.team_id)\
     .order_by(subquery.c.max_public_score.desc())
    
    if limit:
        query = query.limit(limit)
    
    results = query.all()
    
    # If private scores should be shown, get them too
    leaderboard = []
    for i, (team_name, public_score) in enumerate(results):
        entry = {
            "team_name": team_name,
            "score": public_score,
            "rank": i + 1
        }
        
        if show_private:
            # Get best private score for this team
            team = db.query(models.Team).filter(models.Team.name == team_name).first()
            if team:
                best_private = db.query(func.max(models.Submission.private_score))\
                    .filter(
                        models.Submission.team_id == team.id,
                        models.Submission.task_id == task_id
                    ).scalar()
                entry["private_score"] = best_private
        
        leaderboard.append(entry)
    
    return leaderboard

@router.get("/task1", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task1(db: Session = Depends(database.get_db)):
    settings = get_leaderboard_settings(db)
    return get_leaderboard_data(db, 1, limit=None, show_private=settings.show_private_scores)

@router.get("/task2", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task2(db: Session = Depends(database.get_db)):
    settings = get_leaderboard_settings(db)
    return get_leaderboard_data(db, 2, limit=None, show_private=settings.show_private_scores)

@router.get("/settings", response_model=schemas.LeaderboardSettings)
def get_settings(db: Session = Depends(database.get_db)):
    return get_leaderboard_settings(db)
