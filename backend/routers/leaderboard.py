from fastapi import APIRouter, Depends, Query
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

def get_leaderboard_data(db: Session, task_id: int, team_name: Optional[str] = None, show_private: bool = False):
    """Get leaderboard data with optional private scores and specific team"""
    # Subquery to find best public score per team
    subquery = db.query(
        models.Submission.team_id,
        func.max(models.Submission.public_score).label("max_public_score")
    ).filter(models.Submission.task_id == task_id).group_by(models.Submission.team_id).subquery()
    
    # Get all team names and scores, ordered
    all_results = db.query(
        models.Team.name, 
        subquery.c.max_public_score
    ).join(subquery, models.Team.id == subquery.c.team_id)\
     .order_by(subquery.c.max_public_score.desc()).all()
    
    # Get top 10
    top_10 = all_results[:10]
    
    leaderboard = []
    team_found_in_top_10 = False
    
    # Process top 10
    for i, (name, public_score) in enumerate(top_10):
        entry = {
            "team_name": name,
            "score": public_score,
            "rank": i + 1
        }
        
        if team_name and name == team_name:
            team_found_in_top_10 = True
        
        if show_private:
            team = db.query(models.Team).filter(models.Team.name == name).first()
            if team:
                best_private = db.query(func.max(models.Submission.private_score))\
                    .filter(
                        models.Submission.team_id == team.id,
                        models.Submission.task_id == task_id
                    ).scalar()
                entry["private_score"] = best_private
        
        leaderboard.append(entry)
    
    # If team_name provided and not in top 10, find and append their entry
    if team_name and not team_found_in_top_10:
        for i, (name, public_score) in enumerate(all_results):
            if name == team_name:
                entry = {
                    "team_name": name,
                    "score": public_score,
                    "rank": i + 1
                }
                
                if show_private:
                    team = db.query(models.Team).filter(models.Team.name == name).first()
                    if team:
                        best_private = db.query(func.max(models.Submission.private_score))\
                            .filter(
                                models.Submission.team_id == team.id,
                                models.Submission.task_id == task_id
                            ).scalar()
                        entry["private_score"] = best_private
                
                leaderboard.append(entry)
                break
    
    return leaderboard

@router.get("/task1", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task1(
    team_name: Optional[str] = Query(None, description="Optional team name to include in results if not in top 10"),
    db: Session = Depends(database.get_db)
):
    settings = get_leaderboard_settings(db)
    return get_leaderboard_data(db, 1, team_name=team_name, show_private=settings.show_private_scores)

@router.get("/task2", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task2(
    team_name: Optional[str] = Query(None, description="Optional team name to include in results if not in top 10"),
    db: Session = Depends(database.get_db)
):
    settings = get_leaderboard_settings(db)
    return get_leaderboard_data(db, 2, team_name=team_name, show_private=settings.show_private_scores)

@router.get("/settings", response_model=schemas.LeaderboardSettings)
def get_settings(db: Session = Depends(database.get_db)):
    return get_leaderboard_settings(db)