from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from .. import models, schemas, database, utils

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
    
    leaderboard = []
    team_found = False
    
    # Process all results
    for i, (name, public_score) in enumerate(all_results):
        entry = {
            "team_name": name,
            "score": public_score,
            "rank": i + 1
        }
        
        if team_name and name == team_name:
            team_found = True
        
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
    
    return leaderboard

@router.get("/task1", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task1(
    team_name: Optional[str] = Query(None, description="Optional team name to include in results if not in top 10"),
    db: Session = Depends(database.get_db),
    current_team: Optional[models.Team] = Depends(utils.get_current_team_optional)
):
    settings = get_leaderboard_settings(db)
    # Only show private scores if settings allow it AND user is authenticated AND user is admin
    show_private = True
    return get_leaderboard_data(db, 1, team_name=team_name, show_private=show_private)

@router.get("/task2", response_model=List[schemas.LeaderboardEntry])
def leaderboard_task2(
    team_name: Optional[str] = Query(None, description="Optional team name to include in results if not in top 10"),
    db: Session = Depends(database.get_db),
    current_team: Optional[models.Team] = Depends(utils.get_current_team_optional)
):
    settings = get_leaderboard_settings(db)
    # Only show private scores if settings allow it AND user is authenticated AND user is admin
    show_private = True
    return get_leaderboard_data(db, 2, team_name=team_name, show_private=show_private)

@router.get("/settings", response_model=schemas.LeaderboardSettings)
def get_settings(db: Session = Depends(database.get_db)):
    return get_leaderboard_settings(db)

@router.get("/combined", response_model=List[schemas.CombinedLeaderboardEntry])
def leaderboard_combined(
    db: Session = Depends(database.get_db),
    current_team: Optional[models.Team] = Depends(utils.get_current_team_optional)
):
    """
    Combined leaderboard: 60% Task 1 + 30% Task 2 (10% reserved for IRL presentations)
    """
    settings = get_leaderboard_settings(db)
    show_private = True
    
    # Get best public scores for task 1
    task1_subquery = db.query(
        models.Submission.team_id,
        func.max(models.Submission.public_score).label("max_public_score")
    ).filter(models.Submission.task_id == 1).group_by(models.Submission.team_id).subquery()
    
    task1_scores = db.query(
        models.Team.name,
        task1_subquery.c.max_public_score
    ).join(task1_subquery, models.Team.id == task1_subquery.c.team_id).all()
    
    # Get best public scores for task 2
    task2_subquery = db.query(
        models.Submission.team_id,
        func.max(models.Submission.public_score).label("max_public_score")
    ).filter(models.Submission.task_id == 2).group_by(models.Submission.team_id).subquery()
    
    task2_scores = db.query(
        models.Team.name,
        task2_subquery.c.max_public_score
    ).join(task2_subquery, models.Team.id == task2_subquery.c.team_id).all()
    
    # Convert to dictionaries for easy lookup
    task1_dict = {name: score for name, score in task1_scores}
    task2_dict = {name: score for name, score in task2_scores}
    
    # Get all team names that have at least one submission
    all_teams = set(task1_dict.keys()) | set(task2_dict.keys())
    
    # Get private scores if needed
    task1_private_dict = {}
    task2_private_dict = {}
    
    if show_private:
        # Get best private scores for task 1
        task1_private_subquery = db.query(
            models.Submission.team_id,
            func.max(models.Submission.private_score).label("max_private_score")
        ).filter(models.Submission.task_id == 1).group_by(models.Submission.team_id).subquery()
        
        task1_private_scores = db.query(
            models.Team.name,
            task1_private_subquery.c.max_private_score
        ).join(task1_private_subquery, models.Team.id == task1_private_subquery.c.team_id).all()
        
        # Get best private scores for task 2
        task2_private_subquery = db.query(
            models.Submission.team_id,
            func.max(models.Submission.private_score).label("max_private_score")
        ).filter(models.Submission.task_id == 2).group_by(models.Submission.team_id).subquery()
        
        task2_private_scores = db.query(
            models.Team.name,
            task2_private_subquery.c.max_private_score
        ).join(task2_private_subquery, models.Team.id == task2_private_subquery.c.team_id).all()
        
        task1_private_dict = {name: score for name, score in task1_private_scores if score is not None}
        task2_private_dict = {name: score for name, score in task2_private_scores if score is not None}
    
    # Calculate combined scores
    leaderboard = []
    for team_name in all_teams:
        task1_score = task1_dict.get(team_name, 0.0)
        task2_score = task2_dict.get(team_name, 0.0)
        
        # Combined score: 60% task1 + 30% task2
        combined_score = (task1_score * 0.6) + (task2_score * 0.3)
        
        entry = {
            "team_name": team_name,
            "combined_score": combined_score,
            "task1_score": task1_score if task1_score > 0 else None,
            "task2_score": task2_score if task2_score > 0 else None,
            "rank": 0  # Will be assigned after sorting
        }
        
        if show_private:
            task1_private = task1_private_dict.get(team_name, 0.0)
            task2_private = task2_private_dict.get(team_name, 0.0)
            private_combined = (task1_private * 0.6) + (task2_private * 0.3)
            
            entry["private_combined_score"] = private_combined if (task1_private > 0 or task2_private > 0) else None
            entry["private_task1_score"] = task1_private if task1_private > 0 else None
            entry["private_task2_score"] = task2_private if task2_private > 0 else None
        
        leaderboard.append(entry)
    
    # Sort by combined score (descending) and assign ranks
    leaderboard.sort(key=lambda x: x["combined_score"], reverse=True)
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1
    
    return leaderboard