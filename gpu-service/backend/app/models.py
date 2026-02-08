"""Database models for hackathon backend"""

from datetime import datetime
from typing import Optional

class Submission:
    """Model submission record"""
    def __init__(self, id: int, team_id: int, task: str, status: str, 
                 score: Optional[float] = None, created_at: Optional[datetime] = None):
        self.id = id
        self.team_id = team_id
        self.task = task
        self.status = status
        self.score = score
        self.created_at = created_at or datetime.now()
