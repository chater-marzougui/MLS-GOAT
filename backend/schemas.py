from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    password: str

class Team(TeamBase):
    id: int
    is_admin: bool
    
    class Config:
        orm_mode = True

class SubmissionBase(BaseModel):
    task_id: int
    # metrics/details can be passed back in response

class SubmissionResult(SubmissionBase):
    id: int
    team_id: int
    filename: str
    public_score: float
    private_score: float # Maybe hide this from public view?
    timestamp: datetime
    details: str 

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class LeaderboardEntry(BaseModel):
    team_name: str
    score: float
    rank: int
    private_score: Optional[float] = None
    details: Optional[str] = None

class CombinedLeaderboardEntry(BaseModel):
    team_name: str
    combined_score: float
    task1_score: Optional[float] = None
    task2_score: Optional[float] = None
    rank: int
    private_combined_score: Optional[float] = None
    private_task1_score: Optional[float] = None
    private_task2_score: Optional[float] = None

class TeamInfo(BaseModel):
    id: int
    name: str
    is_admin: bool
    
    class Config:
        orm_mode = True

class SubmissionHistory(BaseModel):
    id: int
    task_id: int
    filename: str
    public_score: float
    private_score: float
    timestamp: datetime
    details: str
    
    class Config:
        orm_mode = True

class LeaderboardSettings(BaseModel):
    show_private_scores: bool
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Q&A Schemas
class AnswerBase(BaseModel):
    content: str

class AnswerCreate(AnswerBase):
    pass

class Answer(AnswerBase):
    id: int
    question_id: int
    team_id: int
    author_name: str
    author_is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class QuestionBase(BaseModel):
    title: str
    content: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    team_id: int
    author_name: str
    author_is_admin: bool
    created_at: datetime
    updated_at: datetime
    answer_count: int
    latest_answers: List[Answer] = []
    
    class Config:
        orm_mode = True

class QuestionDetail(Question):
    all_answers: List[Answer] = []
    
    class Config:
        orm_mode = True
