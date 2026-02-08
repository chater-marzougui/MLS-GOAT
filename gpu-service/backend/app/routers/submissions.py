"""GPU Server - Submissions router with CPU callback"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Header
from fastapi.responses import JSONResponse
import redis
import json
import os
import uuid
import time
import requests
from pathlib import Path
from typing import Optional

router = APIRouter()

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
CPU_SERVER_URL = os.getenv('CPU_SERVER_URL', 'http://cpu-server:8000')
GPU_SCORER_SECRET_KEY = os.getenv('GPU_SCORER_SECRET_KEY')

if not GPU_SCORER_SECRET_KEY:
    raise ValueError("GPU_SCORER_SECRET_KEY environment variable not set")

# Redis connection
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

# Upload directory
UPLOAD_DIR = Path("/app/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Test data path - defaults to public test during hackathon
TEST_DATA_PATH = "/app/data/test_data/public_test"


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "connected" if redis_client and redis_client.ping() else "disconnected"
    return {"status": "ok", "redis": redis_status}


@router.post("/task2")
async def submit_task2_model(
    file: UploadFile = File(...),
    team_token: str = Form(...),
    batch_size: Optional[int] = Form(8),
    is_private: Optional[bool] = Form(False)
):
    """
    Submit an ONNX model for Task 2 evaluation
    
    - **file**: ONNX model file (.onnx)
    - **team_token**: JWT token from CPU server authentication
    - **batch_size**: Batch size for inference (default: 8)
    - **is_private**: Evaluate on private test set (default: False)
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Verify token with CPU server and get team info
        try:
            headers = {'Authorization': f'Bearer {team_token}'}
            cpu_response = requests.get(
                f"{CPU_SERVER_URL}/api/auth/me",
                headers=headers,
                timeout=5
            )
            
            if cpu_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid authentication token")
            
            team_info = cpu_response.json()
            team_id = team_info['id']
            team_name = team_info['name']
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Cannot verify token with CPU server: {str(e)}")
        
        # Check submission limit with CPU server
        try:
            limit_response = requests.get(
                f"{CPU_SERVER_URL}/api/submit/check-limit/task2/{team_id}",
                headers={'X-GPU-Secret': GPU_SCORER_SECRET_KEY},
                timeout=5
            )
            
            if limit_response.status_code == 429:
                raise HTTPException(status_code=429, detail="Submission limit reached for Task 2")
            elif limit_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to check submission limit")
                
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Cannot check limit with CPU server: {str(e)}")
        
        # Validate file type
        if not file.filename.endswith('.onnx'):
            raise HTTPException(status_code=400, detail="Only .onnx files are accepted")
        
        # Validate batch_size
        if batch_size < 1 or batch_size > 32:
            raise HTTPException(status_code=400, detail=f"Batch size must be between 1 and 32 (provided: {batch_size})")
        
        # Check file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 100:
            raise HTTPException(status_code=400, detail=f"Model file too large: {file_size_mb:.1f}MB (max 100MB)")
        
        # Generate unique submission ID
        submission_id = f"sub_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Save uploaded file
        model_filename = f"{submission_id}.onnx"
        model_path = UPLOAD_DIR / model_filename
        
        # Write file
        with open(model_path, "wb") as f:
            f.write(content)
        
        # Set test data path and task based on is_private flag
        if is_private:
            test_data_path = "/app/data/test_data/private_test"
            task_type = "task2_private"
        else:
            test_data_path = TEST_DATA_PATH
            task_type = "task2"
        
        # Create job for queue
        job_data = {
            'submission_id': submission_id,
            'team_id': team_id,
            'team_name': team_name,
            'model_path': str(model_path),
            'test_data_path': test_data_path,
            'batch_size': batch_size,
            'task': task_type,
            'timestamp': time.time(),
            'model_size_mb': file_size_mb,
            'original_filename': file.filename
        }
        
        # Push to Redis queue
        redis_client.lpush('evaluation_queue', json.dumps(job_data))
        queue_position = redis_client.llen('evaluation_queue')
        
        # Notify CPU server about pending submission
        try:
            notify_data = {
                'submission_id': submission_id,
                'team_id': team_id,
                'task_id': 2,
                'filename': file.filename,
                'status': 'queued'
            }
            requests.post(
                f"{CPU_SERVER_URL}/api/gpu-callback/submission-queued",
                json=notify_data,
                headers={'X-GPU-Secret': GPU_SCORER_SECRET_KEY},
                timeout=5
            )
        except:
            pass  # Non-critical, continue even if notification fails
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Model submitted successfully",
                "submission_id": submission_id,
                "status": "queued",
                "queue_position": queue_position,
                "model_size_mb": round(file_size_mb, 2),
                "batch_size": batch_size,
                "is_private": is_private,
                "test_set": "private_test" if is_private else "public_test",
                "team_name": team_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")


@router.get("/task2/status/{submission_id}")
async def get_submission_status(submission_id: str):
    """Get the status of a submission"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Check if result exists
        if redis_client.exists(f'result:{submission_id}'):
            result = redis_client.hgetall(f'result:{submission_id}')
            
            # Parse JSON fields
            if 'details' in result:
                try:
                    result['details'] = json.loads(result['details'])
                except:
                    pass
            
            # Convert score to float
            if 'score' in result:
                try:
                    result['score'] = float(result['score'])
                except:
                    pass
            
            return JSONResponse(content=result)
        else:
            # Check if still in queue
            queue_length = redis_client.llen('evaluation_queue')
            
            return JSONResponse(
                status_code=202,
                content={
                    "submission_id": submission_id,
                    "status": "processing",
                    "message": "Model is being evaluated or queued",
                    "queue_length": queue_length
                }
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/queue/status")
async def get_queue_status():
    """Get current queue status"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        queue_length = redis_client.llen('evaluation_queue')
        
        # Get recent results
        result_keys = redis_client.keys('result:*')
        recent_results = []
        
        for key in sorted(result_keys, reverse=True)[:10]:
            result = redis_client.hgetall(key)
            if result:
                recent_results.append({
                    'submission_id': result.get('submission_id', ''),
                    'status': result.get('status', ''),
                    'score': result.get('score', ''),
                    'worker_id': result.get('worker_id', ''),
                    'timestamp': result.get('timestamp', '')
                })
        
        return JSONResponse(content={
            "queue_length": queue_length,
            "total_workers": int(os.getenv("WORKER_COUNT", 1)),
            "recent_results_count": len(recent_results),
            "recent_results": recent_results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue status check failed: {str(e)}")

@router.delete("/task2/{submission_id}")
async def delete_submission(submission_id: str):
    """
    Delete a submission and its results
    
    - **submission_id**: The submission ID to delete
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Delete result from Redis
        deleted = redis_client.delete(f'result:{submission_id}')
        
        # Delete model file if exists
        model_path = UPLOAD_DIR / f"{submission_id}.onnx"
        if model_path.exists():
            model_path.unlink()
        
        if deleted:
            return JSONResponse(content={
                "message": "Submission deleted successfully",
                "submission_id": submission_id
            })
        else:
            raise HTTPException(status_code=404, detail="Submission not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.post("/calculate-private-leaderboard")
async def calculate_private_leaderboard(x_gpu_secret: str = Header(None)):
    """
    Calculate private leaderboard by evaluating all teams' best models on private test set.
    Protected endpoint - requires GPU_SCORER_SECRET_KEY header.
    
    - **X-GPU-Secret**: GPU scorer secret key for authentication
    """
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    # Verify secret key
    if x_gpu_secret != GPU_SCORER_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing GPU secret key")
    
    try:
        # Get all team best model keys from Redis
        team_keys = redis_client.keys('team:*:best_model')
        
        if not team_keys:
            return JSONResponse(content={
                "message": "No teams found with best models",
                "teams_processed": 0
            })
        
        teams_to_evaluate = []
        
        for team_key in team_keys:
            # Extract team_id from key: "team:123:best_model" -> "123"
            team_id = team_key.split(':')[1]
            
            # Get team's best model info
            best_model_path = redis_client.get(f'team:{team_id}:best_model')
            best_submission_id = redis_client.get(f'team:{team_id}:best_submission')
            best_score = redis_client.get(f'team:{team_id}:best_score')
            
            if best_model_path and os.path.exists(best_model_path):
                teams_to_evaluate.append({
                    'team_id': team_id,
                    'model_path': best_model_path,
                    'submission_id': best_submission_id,
                    'public_score': float(best_score) if best_score else 0
                })
        
        if not teams_to_evaluate:
            return JSONResponse(content={
                "message": "No valid best models found",
                "teams_processed": 0
            })
        
        # Queue each team's best model for evaluation on private test set
        private_test_path = "/app/data/test_data/private_test"
        queued_evaluations = []
        
        for team_data in teams_to_evaluate:
            # Create private evaluation job
            private_submission_id = f"private_{team_data['team_id']}_{int(time.time())}"
            
            job_data = {
                'submission_id': private_submission_id,
                'team_id': team_data['team_id'],
                'model_path': team_data['model_path'],
                'test_data_path': private_test_path,
                'batch_size': 8,
                'task': 'task2_private',
                'timestamp': time.time(),
                'original_submission_id': team_data['submission_id'],
                'public_score': team_data['public_score']
            }
            
            # Push to Redis queue
            redis_client.lpush('evaluation_queue', json.dumps(job_data))
            
            queued_evaluations.append({
                'team_id': team_data['team_id'],
                'private_submission_id': private_submission_id,
                'original_submission_id': team_data['submission_id'],
                'public_score': team_data['public_score']
            })
        
        return JSONResponse(content={
            "message": "Private leaderboard calculation started",
            "teams_processed": len(queued_evaluations),
            "evaluations": queued_evaluations,
            "test_set": "private_test",
            "note": "Results will be sent to CPU server as they complete"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Private leaderboard calculation failed: {str(e)}")
