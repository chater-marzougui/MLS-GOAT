# Project Documentation

## Project Overview
GPU-accelerated ONNX model evaluation system with 7 parallel workers, FastAPI backend, and Redis queue management.

---

## 📁 Important Files

### Core Application Files

#### `backend/worker.py`
**Purpose**: GPU-accelerated model evaluation logic  
**Key Functions**:
- `load_test_data()` - Generates 96 test images for evaluation
- `evaluate_model()` - Runs ONNX inference with batch processing
- `calculate_score()` - Computes performance metrics
- `process_jobs()` - Redis queue consumer loop

**Key Variables**:
```python
BATCH_SIZE = 8              # Images per inference batch
IMAGE_SIZE = 448            # Input image dimensions
NUM_SAMPLES = 96            # Total test samples
GPU_MEMORY_FRACTION = 0.143 # ~6.5GB per worker
```

#### `backend/app/main.py`
**Purpose**: FastAPI application entry point  
**Endpoints**: Health checks, submission routes  
**Key Features**: CORS middleware, router registration

#### `backend/app/routers/submissions_simple.py`
**Purpose**: Model submission and status API  
**Endpoints**:
- `POST /submit/task2` - Upload model for evaluation
- `GET /submit/task2/status/{submission_id}` - Check evaluation status
- `GET /submit/queue/status` - View queue and worker info
- `GET /submit/health` - Redis connectivity check

**Key Variables**:
```python
UPLOAD_DIR = Path("/app/data/uploads")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
```

#### `backend/app/models.py`
**Purpose**: Pydantic data models  
**Models**: SubmissionResponse, QueueStatus, StatusResponse

### Configuration Files

#### `docker-compose.yml`
**Purpose**: Orchestrates all services (1 backend + 7 workers + Redis)  
**Key Configuration**:
```yaml
services:
  backend:    # Port 8000, FastAPI
  redis:      # Port 6379, Job queue
  worker-1..7: # GPU workers with CUDA 11.8
```

**Critical Settings**:
- `GPU_MEMORY_FRACTION: "0.143"` - Memory per worker
- `deploy.resources.reservations.devices` - GPU device mapping
- `volumes: ./backend/data:/app/data` - Shared storage
- `REDIS_HOST: redis` - Queue connection

#### `.env`
**Purpose**: Environment configuration  
**Variables**:
```bash
REDIS_HOST=redis
REDIS_PORT=6379
WORKER_COUNT=7
```

#### `backend/requirements.txt`
**Purpose**: Backend Python dependencies  
**Key Packages**: fastapi, uvicorn, redis, python-multipart

#### `backend/requirements-worker.txt`
**Purpose**: Worker Python dependencies  
**Key Packages**: onnxruntime-gpu==1.17.1, numpy, redis, Pillow

### Docker Files

#### `backend/Dockerfile`
**Purpose**: Backend container image  
**Base**: python:3.10-slim  
**Workdir**: /app

#### `backend/Dockerfile.worker`
**Purpose**: GPU worker container image  
**Base**: nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04  
**Key Components**: CUDA 11.8, cuDNN 8, Python 3.10, onnxruntime-gpu

### Test & Utility Files

#### `test_api.py`
**Purpose**: Complete API testing script  
**Tests**:
1. Health endpoint check
2. Submit health check
3. Model upload and submission
4. Status polling until completion
5. Queue status verification

**Usage**: `python3 test_api.py`

#### `depth_anything_bs32.onnx`
**Purpose**: Production model file (94.38MB)  
**Specs**:
- Input: (8, 3, 448, 448) - batch_size, channels, height, width
- Output: (8, 448, 448) - depth predictions
- Framework: Depth Anything model

### Documentation Files

#### `GPU_ACCELERATION_COMPLETE.md`
**Purpose**: Final implementation summary with performance metrics

#### `README_FULL.md`
**Purpose**: Complete setup and usage guide

---

## 🔧 Important Configuration Variables

### Where to Find Config Variables

#### Docker Compose (`docker-compose.yml`)
```yaml
environment:
  REDIS_HOST: redis              # Redis connection
  REDIS_PORT: 6379
  GPU_MEMORY_FRACTION: "0.143"   # GPU memory per worker (~6.5GB)
  WORKER_ID: "1"                 # Worker identifier
  
deploy:
  resources:
    reservations:
      devices:
        - capabilities: [gpu]     # GPU access requirement
```

#### Worker Script (`backend/worker.py`)
```python
# Line ~15-20
BATCH_SIZE = 8           # Model batch size
IMAGE_SIZE = 448         # Input image size
NUM_SAMPLES = 96         # Test dataset size

# Line ~70
GPU_MEMORY_FRACTION = float(os.getenv('GPU_MEMORY_FRACTION', '0.143'))

# Line ~80
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
WORKER_ID = os.getenv('WORKER_ID', '1')
```

#### Backend Router (`backend/app/routers/submissions_simple.py`)
```python
# Line ~20-25
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
UPLOAD_DIR = Path("/app/data/uploads")
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Line ~110-115
EVALUATION_QUEUE = "evaluation_queue"
RESULT_KEY_PREFIX = "result:"
RESULT_EXPIRY = 3600  # 1 hour
```

#### Environment File (`.env`)
```bash
REDIS_HOST=redis
REDIS_PORT=6379
WORKER_COUNT=7
```

### Tuning Parameters

**For Smaller Models (<50MB)**:
```yaml
# docker-compose.yml
GPU_MEMORY_FRACTION: "0.10"  # 4.6GB per worker
# Can run 9-10 workers
```

**For Larger Models (>100MB)**:
```yaml
# docker-compose.yml
GPU_MEMORY_FRACTION: "0.20"  # 9.2GB per worker
# Run 4-5 workers
```

**Batch Size Optimization** (`backend/worker.py`):
```python
BATCH_SIZE = 16  # Larger batch = faster throughput (if model supports)
BATCH_SIZE = 4   # Smaller batch = less memory
```

---

## 🐛 Debugging Commands

### Docker Service Management

```bash
# Start all services
cd /home/master1/Desktop/goat
sudo docker compose up -d

# View service status
sudo docker compose ps

# Stop all services
sudo docker compose down

# Rebuild and restart
sudo docker compose build
sudo docker compose up -d

# Restart specific worker
sudo docker compose restart worker-3

# Remove everything (including volumes)
sudo docker compose down -v
```

### Log Viewing

```bash
# View all logs
sudo docker compose logs -f

# View specific worker logs
sudo docker compose logs -f worker-1

# View last 50 lines
sudo docker compose logs --tail 50 worker-3

# View backend logs
sudo docker compose logs -f backend

# View Redis logs
sudo docker compose logs redis

# Filter logs by keyword
sudo docker compose logs | grep -i "error\|cuda\|gpu"
```

### GPU Monitoring

```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# GPU processes
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv

# Check GPU in worker container
sudo docker compose exec worker-1 nvidia-smi

# GPU utilization over time
nvidia-smi dmon -s u

# Detailed GPU info
nvidia-smi -q
```

### Redis Queue Debugging

```bash
# Access Redis CLI
sudo docker compose exec redis redis-cli

# Inside Redis CLI:
LLEN evaluation_queue          # Check queue length
LRANGE evaluation_queue 0 -1   # View all jobs in queue
KEYS result:*                  # List all result keys
HGETALL result:sub_12345       # Get specific result
FLUSHALL                       # Clear all data (caution!)
INFO                           # Redis server info
exit                           # Exit CLI
```

### Container Inspection

```bash
# Enter worker container shell
sudo docker compose exec worker-1 bash

# Inside container:
python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider']

nvidia-smi                     # Check GPU inside container
ls -lah /app/data/uploads/     # Check uploaded files
env | grep GPU                 # Check environment variables
exit

# Check container resource usage
sudo docker stats

# Inspect container details
sudo docker inspect goat-worker-1-1
```

### API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test submit health
curl http://localhost:8000/submit/health

# Check queue status
curl http://localhost:8000/submit/queue/status

# Submit model
curl -X POST http://localhost:8000/submit/task2 \
  -F "file=@depth_anything_bs32.onnx"

# Check submission status
curl http://localhost:8000/submit/task2/status/sub_1770321145_69dc972f

# Run full test suite
python3 test_api.py
```

### Network Debugging

```bash
# Check Docker network
sudo docker network ls
sudo docker network inspect goat_default

# Test Redis connection from backend
sudo docker compose exec backend python3 -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Check open ports
sudo netstat -tulpn | grep -E "8000|6379"

# Test backend connectivity
curl -v http://localhost:8000/health
```

### Disk Space Management

```bash
# Check disk usage
df -h

# Docker disk usage
sudo docker system df

# Clean up unused Docker resources
sudo docker system prune -f

# Clean up everything (including volumes)
sudo docker system prune -a -f --volumes

# Remove specific images
sudo docker images
sudo docker rmi goat-worker-1

# Remove dangling volumes
sudo docker volume ls -qf dangling=true
sudo docker volume prune -f
```

### Performance Analysis

```bash
# Worker performance in logs
sudo docker compose logs worker-1 | grep "Inference time\|Throughput"

# Backend request timing
curl -w "@-" -o /dev/null -s http://localhost:8000/health <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
      time_redirect:  %{time_redirect}\n
   time_starttransfer:  %{time_starttransfer}\n
                      ----------\n
          time_total:  %{time_total}\n
EOF

# Monitor system resources
htop

# Check I/O wait
iostat -x 1
```

### Build & Image Management

```bash
# Rebuild specific service
sudo docker compose build worker-1

# Rebuild without cache
sudo docker compose build --no-cache

# Pull latest base images
sudo docker compose pull

# List all images
sudo docker images

# Image history
sudo docker history goat-worker-1

# Remove unused images
sudo docker image prune -a
```

### Common Issues & Solutions

#### Issue: Workers not using GPU
```bash
# Check 1: Verify CUDA provider available
sudo docker compose exec worker-1 python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"

# Check 2: Verify GPU accessible
sudo docker compose exec worker-1 nvidia-smi

# Check 3: Check logs for errors
sudo docker compose logs worker-1 | grep -i "cuda\|error"

# Solution: Rebuild with correct base image
# Ensure Dockerfile.worker uses: nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
```

#### Issue: Queue not processing
```bash
# Check 1: Verify Redis is running
sudo docker compose ps redis

# Check 2: Check queue length
sudo docker compose exec redis redis-cli LLEN evaluation_queue

# Check 3: Verify workers are running
sudo docker compose ps | grep worker

# Solution: Restart workers
sudo docker compose restart worker-1 worker-2 worker-3 worker-4 worker-5 worker-6 worker-7
```

#### Issue: Out of disk space
```bash
# Check disk space
df -h

# Clean Docker cache
sudo docker system prune -a -f --volumes

# Remove old containers
sudo docker container prune -f

# Remove build cache
sudo docker builder prune -f
```

#### Issue: Port already in use
```bash
# Find process using port 8000
sudo lsof -i :8000
sudo netstat -tulpn | grep 8000

# Kill process
sudo kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8080:8000"  # Host:Container
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client/User                         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP POST /submit/task2
                    ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                │
│  - Handles file uploads to /app/data/uploads/          │
│  - Pushes jobs to Redis queue                          │
│  - Returns status and results                           │
└───────────────────┬─────────────────────────────────────┘
                    │ Redis Queue
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Redis (Port 6379)                          │
│  - Queue: evaluation_queue                              │
│  - Results: result:{submission_id}                      │
└───────────┬───────────────────────────┬─────────────────┘
            │                           │
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │   Worker 1    │    ...    │   Worker 7    │
    │  GPU: 6.5GB   │           │  GPU: 6.5GB   │
    │  CPU: 1 core  │           │  CPU: 1 core  │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            └──────────┬────────────────┘
                       ▼
            ┌─────────────────────┐
            │   NVIDIA A40 GPU    │
            │   46GB VRAM Total   │
            └─────────────────────┘
```

---

## 🚀 Quick Reference

### Start System
```bash
cd /home/master1/Desktop/goat && sudo docker compose up -d
```

### Run Tests
```bash
python3 test_api.py
```

### Check Logs
```bash
sudo docker compose logs -f worker-1
```

### Monitor GPU
```bash
watch -n 1 nvidia-smi
```

### Stop System
```bash
sudo docker compose down
```

### Emergency Reset
```bash
sudo docker compose down -v
sudo docker system prune -a -f
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

**Last Updated**: 2026-02-05  
**System Status**: Production Ready ✅  
**Performance**: 31x GPU speedup (4.2s inference time)
