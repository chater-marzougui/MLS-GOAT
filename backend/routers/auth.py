from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, database, utils
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    name: str
    password: str

@router.post("/login", response_model=schemas.Token)
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    team = db.query(models.Team).filter(models.Team.name == request.name).first()
    if not team:
        raise HTTPException(status_code=400, detail="Incorrect team name or password")
    if not utils.verify_password(request.password, team.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect team name or password")
    
    access_token = utils.create_access_token_simple(team.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.TeamInfo)
def get_current_user(current_team: models.Team = Depends(utils.get_current_team)):
    return current_team
