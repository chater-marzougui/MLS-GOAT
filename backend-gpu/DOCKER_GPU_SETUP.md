# GPU-Accelerated ONNX Evaluation with Docker

This setup creates 7 isolated worker containers, each with:
- 1 CPU core
- ~4GB GPU VRAM (out of 46GB total)
- Dedicated ONNX evaluation environment

The main backend (1 CPU core) handles uploads and job distribution via Redis queue.

## Prerequisites

### 1. Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### 2. Install Docker Compose v2

```bash
# Docker Compose v2 (plugin)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify
docker compose version
```

## Project Structure

```
MLS-GOAT/
├── backend/
│   ├── Dockerfile              # Main backend
│   ├── Dockerfile.worker       # Worker containers
│   ├── worker.py              # Worker evaluation script
│   ├── requirements.txt       # Backend requirements
│   ├── requirements-worker.txt # Worker requirements
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── routers/
│   │       └── submissions.py  # Updated with Redis queue
│   └── data/
│       └── test_task2.npy     # Your test dataset
├── docker-compose.yml
└── .env
```

## Setup Steps

### 1. Create Worker Requirements

Create `backend/requirements-worker.txt`:
```
onnxruntime-gpu==1.16.3
numpy==1.24.3
redis==5.0.1
Pillow==10.1.0
```

### 2. Update Backend Requirements

Add to `backend/requirements.txt`:
```
redis==5.0.1
```

### 3. Create Worker Dockerfile

Create `backend/Dockerfile.worker` (provided in files)

### 4. Create Worker Script

Create `backend/worker.py` (provided in files)

### 5. Update Submissions Router

Replace your `backend/app/routers/submissions.py` with the updated version (provided)

### 6. Configure Environment

Create `.env` file:
```bash
REDIS_HOST=redis
REDIS_PORT=6379
DATABASE_URL=sqlite:///./hackathon.db
WORKER_COUNT=7
```

### 7. Customize Worker Script

Edit `backend/worker.py` to match your evaluation logic:

```python
def load_test_data(test_data_path):
    """Load your test dataset"""
    # Replace with your actual data loading
    test_data = np.load(test_data_path, allow_pickle=True)
    return test_data

def evaluate_model(model_path, test_data_path):
    """Customize evaluation logic"""
    # Adjust input/output processing
    # Modify batch size
    # Add your preprocessing
    pass

def calculate_score(results):
    """Customize scoring formula"""
    # Adjust weights
    # Add more metrics
    # Change scoring logic
    pass
```

## Deployment

### Start All Services

```bash
# Build images
docker compose build

# Start all services (1 backend + 7 workers + redis)
docker compose up -d

# View logs
docker compose logs -f

# View specific worker logs
docker compose logs -f worker-1
```

### Scale Workers

To change number of workers:

```bash
# Scale to 5 workers instead of 7
docker compose up -d --scale worker-1=5

# Or edit docker-compose.yml and adjust
```

### Stop Services

```bash
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Monitoring

### Check Queue Status

```bash
# Enter Redis container
docker compose exec redis redis-cli

# Check queue length
LLEN evaluation_queue

# View queue items
LRANGE evaluation_queue 0 -1

# Check results
KEYS result:*
HGETALL result:123
```

### Monitor GPU Usage

```bash
# Watch GPU usage across all workers
watch -n 1 nvidia-smi
```

### Check Worker Health

```bash
# List running containers
docker compose ps

# Check worker logs
docker compose logs worker-1 --tail 50

# Check resource usage
docker stats
```

## Memory Management

### A40 GPU: 46GB Total

With 7 workers, each gets ~6.5GB, but we limit to 4GB per worker to leave headroom:

```python
# In worker.py
GPU_MEMORY_FRACTION = 0.143  # ~6.5GB per worker
# But ONNX Runtime will be configured to use max 4GB

provider_options = [{
    'gpu_mem_limit': int(0.143 * 46 * 1024 * 1024 * 1024),  # ~6.5GB in bytes
}]
```

Adjust based on your model requirements:
- Smaller models (<20MB): Use 2-3GB per worker → Run 10-12 workers
- Larger models (30-40MB): Use 4-5GB per worker → Run 7-8 workers

### CPU Allocation

8 cores total:
- 1 core: Main backend (uploads, API)
- 7 cores: Workers (1 each)

## Testing

### Test Single Worker

```bash
# Start only redis and one worker
docker compose up -d redis worker-1

# Check logs
docker compose logs -f worker-1
```

### Test Queue System

```bash
# Start all services
docker compose up -d

# Submit a model via API
curl -X POST http://localhost:8000/submit/task2 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@model.onnx"

# Check queue status
curl http://localhost:8000/submit/queue/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check submission status
curl http://localhost:8000/submit/task2/status/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### GPU Not Accessible

```bash
# Verify NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check Docker configuration
cat /etc/docker/daemon.json
# Should contain nvidia runtime

# Restart Docker
sudo systemctl restart docker
```

### Worker Crashes / OOM

```bash
# Check worker logs
docker compose logs worker-1

# Reduce GPU memory per worker
# Edit docker-compose.yml
GPU_MEMORY_FRACTION=0.10  # Use less memory

# Or reduce number of workers
docker compose up -d --scale worker-1=5
```

### Queue Not Processing

```bash
# Check Redis connection
docker compose exec backend python3 -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Check queue
docker compose exec redis redis-cli LLEN evaluation_queue

# Restart workers
docker compose restart worker-1 worker-2 worker-3
```

### Slow Evaluation

```bash
# Check GPU utilization
nvidia-smi dmon -s u

# Check if models are using GPU
docker compose exec worker-1 python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"
# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider']

# Increase batch size in worker.py
batch_size = 64  # Instead of 32
```

## Production Optimizations

### 1. Persistent Storage

```yaml
# Add to docker-compose.yml
volumes:
  - ./models:/app/models
  - ./results:/app/results
```

### 2. Health Checks

```yaml
# Add to worker services
healthcheck:
  test: ["CMD", "python3", "-c", "import redis; redis.Redis(host='redis').ping()"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 3. Resource Limits

```yaml
# Fine-tune resource limits
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 8G
    reservations:
      cpus: '0.5'
      memory: 4G
```

### 4. Logging

```yaml
# Configure logging
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## Performance Metrics

Expected throughput with 7 workers:
- Small models (<10MB): ~2-3 seconds per evaluation
- Medium models (10-25MB): ~5-10 seconds per evaluation
- Large models (25-40MB): ~15-30 seconds per evaluation

Queue processing: ~7 models simultaneously

Total throughput: ~10-40 evaluations per minute depending on model size

## Alternative: MIG Mode (Multi-Instance GPU)

For even better isolation, enable MIG on A40:

```bash
# Enable MIG mode
sudo nvidia-smi -mig 1

# Create 7 instances
sudo nvidia-smi mig -cgi 7g.40gb -C

# List instances
nvidia-smi mig -lgi
```

Then update docker-compose.yml to use specific MIG devices.
