from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from . import models, database
from .routers import auth, submissions, leaderboard, admin, teams, qa

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MLS-GOAT Hackathon Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(submissions.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)
app.include_router(qa.router)

@app.on_event("startup")
async def startup_event():
    os.makedirs("temp", exist_ok=True)
    gt_path = "./data/gt_task1"
    if not os.path.exists(gt_path):
        print(f"WARNING: Ground Truth directory not found at {gt_path}. Task 1 scoring will fail.")
        os.makedirs(gt_path, exist_ok=True) 

@app.get("/")
def read_root():
    return {"message": "Welcome to MLS-GOAT Hackathon API"}
