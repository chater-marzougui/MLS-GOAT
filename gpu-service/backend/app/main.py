"""Main FastAPI application"""

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import sys

# Configure logging to stdout (unbuffered)
logging.basicConfig(
    level=logging.INFO,
    format='[Backend] %(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Import routers
from app.routers import submissions as submissions

app = FastAPI(
    title="ONNX Model Evaluation API",
    description="GPU-accelerated ONNX model evaluation with Redis queue",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check environment variables
secret_key = os.getenv("GPU_SCORER_SECRET_KEY")
cpu_server_url = os.getenv("CPU_SERVER_URL")

if not secret_key:
    logger.error("GPU_SCORER_SECRET_KEY environment variable not set")
    raise ValueError("GPU_SCORER_SECRET_KEY environment variable not set")
else:
    logger.info(f"✓ GPU_SCORER_SECRET_KEY is set: {secret_key[:10]}...")

if not cpu_server_url:
    logger.warning("CPU_SERVER_URL environment variable not set")
else:
    logger.info(f"✓ CPU_SERVER_URL is set: {cpu_server_url}")
    # Test connection to CPU server
    try:
        logger.info(f"Testing connection to CPU server at {cpu_server_url}...")
        response = requests.get(f"{cpu_server_url}/api/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✓ CPU server connection successful: {response.json()}")
        else:
            logger.warning(f"⚠ CPU server returned status {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error(f"✗ CPU server connection timeout")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"✗ CPU server connection failed: {e}")
    except Exception as e:
        logger.error(f"✗ CPU server connection error: {e}")
        
# Include routers
app.include_router(submissions.router, prefix="/submit", tags=["submissions"])

@app.get("/")
def root():
    return {
        "message": "ONNX Model Evaluation API",
        "docs": "/docs",
        "endpoints": {
            "submit_model": "POST /submit/task2",
            "check_status": "GET /submit/task2/status/{submission_id}",
            "queue_status": "GET /submit/queue/status"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "workers": int(os.getenv("WORKER_COUNT", 7)),
        "redis_host": os.getenv("REDIS_HOST", "redis")
    }
