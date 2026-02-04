from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    
    submissions = relationship("Submission", back_populates="team")
    questions = relationship("Question", back_populates="author")
    answers = relationship("Answer", back_populates="author")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    task_id = Column(Integer) # 1 or 2
    filename = Column(String)
    public_score = Column(Float, default=0.0)
    private_score = Column(Float, default=0.0)
    details = Column(String, default="{}") # JSON string for extra details like accuracy, size, time
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    team = relationship("Team", back_populates="submissions")

class LeaderboardSettings(Base):
    __tablename__ = "leaderboard_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    show_private_scores = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    author = relationship("Team", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    question = relationship("Question", back_populates="answers")
    author = relationship("Team", back_populates="answers")
