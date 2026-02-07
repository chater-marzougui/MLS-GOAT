from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from . import models, database
from .routers import auth, submissions, leaderboard, admin, teams, qa, gpu_callback

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MLS-GOAT Hackathon Backend")
gpu_server_ip = "https://revolution-imports-thereof-accountability.trycloudflare.com"

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
app.include_router(gpu_callback.router)
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

@app.get("/gpu-server-ip")
def get_gpu_server_ip():
    global gpu_server_ip
    return {"gpu_server_ip": gpu_server_ip}

@app.post("/gpu-server-ip")
def set_gpu_server_ip(ip: str):
    global gpu_server_ip
    gpu_server_ip = ip
    return {"message": f"GPU server IP updated to {gpu_server_ip}"}

@app.get("/")
def read_root():
    return {"message": "Welcome to MLS-GOAT Hackathon API"}
