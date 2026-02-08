# GPU-Accelerated ONNX Model Evaluation Setup

This setup runs GPU-accelerated ONNX model evaluation using Docker containers with Redis queue management.

## Quick Start

### 1. Install NVIDIA Container Toolkit (First Time Only)

```bash
./install_nvidia_docker.sh
```

This will:
- Install NVIDIA Container Toolkit
- Configure Docker to use NVIDIA runtime
- Test GPU access in Docker

### 2. Verify Prerequisites

```bash
./check_prerequisites.sh
```

This checks:
- Docker installation
- Docker Compose
- NVIDIA Container Toolkit
- GPU availability
- Model file exists

### 3. Build Docker Images

```bash
docker compose -f docker-compose.test.yml build
```

This builds the worker container with:
- CUDA 12.1 runtime
- ONNX Runtime GPU
- Python dependencies

### 4. Start Services

```bash
# Start Redis and 2 GPU workers
docker compose -f docker-compose.test.yml up -d

# Check status
docker compose -f docker-compose.test.yml ps

# View logs
docker compose -f docker-compose.test.yml logs -f
```

### 5. Test the Setup

```bash
# Install Python Redis client (if not already installed)
pip install redis

# Run test evaluation
python3 test_evaluation.py
```

This will:
- Connect to Redis
- Push a test job to the queue
- Wait for a worker to process it
- Display results

## Understanding the Setup

### Architecture

```
┌─────────────────┐
│  Redis Queue    │  ← Job queue and result storage
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Worker1│ │Worker2│  ← GPU-accelerated evaluation
│ GPU   │ │ GPU   │
└───────┘ └───────┘
```

### File Structure

```
goat/
├── backend/
│   ├── Dockerfile.worker       # Worker container definition
│   ├── worker.py              # Worker evaluation logic
│   ├── requirements-worker.txt # Python dependencies
│   ├── data/
│   │   └── depth_anything_bs32.onnx  # Model to evaluate
│   └── app/
│       ├── __init__.py
│       ├── main.py            # FastAPI app (future)
│       ├── models.py          # Data models
│       └── routers/
│           └── submissions.py  # API routes (future)
├── docker-compose.test.yml    # Docker services config
├── test_evaluation.py         # Test script
├── check_prerequisites.sh     # Prerequisite checker
├── install_nvidia_docker.sh   # NVIDIA toolkit installer
└── README.md                  # This file
```

### Model Information

- **Model**: Depth Anything (depth_anything_bs32.onnx)
- **Input**: (batch, 3, 518, 518) - RGB images
- **Output**: Depth maps
- **Batch Size**: Optimized for 32

## Commands Reference

### Docker Operations

```bash
# Build images
docker compose -f docker-compose.test.yml build

# Start all services
docker compose -f docker-compose.test.yml up -d

# Stop all services
docker compose -f docker-compose.test.yml down

# View logs (all services)
docker compose -f docker-compose.test.yml logs -f

# View logs (specific worker)
docker compose -f docker-compose.test.yml logs -f worker-1

# Check container status
docker compose -f docker-compose.test.yml ps

# Restart a worker
docker compose -f docker-compose.test.yml restart worker-1

# Scale workers
docker compose -f docker-compose.test.yml up -d --scale worker-1=4
```

### Monitoring

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Check Redis queue
docker compose -f docker-compose.test.yml exec redis redis-cli

# Inside Redis CLI:
LLEN evaluation_queue          # Check queue length
LRANGE evaluation_queue 0 -1   # View all jobs
KEYS result:*                  # List all results
HGETALL result:test_001        # View specific result
```

### Worker Operations

```bash
# Enter worker container
docker compose -f docker-compose.test.yml exec worker-1 bash

# Inside container:
nvidia-smi                     # Check GPU
python3 -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

## Customization

### Adjust Number of Workers

Edit `docker-compose.test.yml` and add more worker services, or use scaling:

```bash
docker compose -f docker-compose.test.yml up -d --scale worker-1=4
```

### Adjust GPU Memory per Worker

Edit `docker-compose.test.yml`:

```yaml
environment:
  - GPU_MEMORY_FRACTION=0.25  # Adjust this value (0.0 to 1.0)
```

### Modify Evaluation Logic

Edit `backend/worker.py`:

- `load_test_data()`: Change how test data is loaded
- `evaluate_model()`: Modify inference logic
- `calculate_score()`: Adjust scoring formula

### Use Different Models

1. Place your ONNX model in `backend/data/`
2. Update the test job in `test_evaluation.py`:
   ```python
   'model_path': '/app/data/your_model.onnx'
   ```

## Troubleshooting

### GPU Not Accessible

```bash
# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If fails, reinstall NVIDIA Container Toolkit
./install_nvidia_docker.sh
```

### Worker Fails to Start

```bash
# Check logs
docker compose -f docker-compose.test.yml logs worker-1

# Common issues:
# - Model file not found: Check backend/data/depth_anything_bs32.onnx exists
# - Redis connection failed: Check redis service is running
# - CUDA error: Check GPU memory availability with nvidia-smi
```

### Queue Not Processing

```bash
# Check if workers are running
docker compose -f docker-compose.test.yml ps

# Check Redis connection
docker compose -f docker-compose.test.yml exec redis redis-cli ping

# Check queue
docker compose -f docker-compose.test.yml exec redis redis-cli LLEN evaluation_queue

# Restart workers
docker compose -f docker-compose.test.yml restart worker-1 worker-2
```

### Out of Memory Errors

```bash
# Check GPU memory usage
nvidia-smi

# Reduce GPU memory per worker in docker-compose.test.yml
GPU_MEMORY_FRACTION=0.15  # Use less memory

# Or reduce batch size in worker.py
batch_size = 16  # Instead of 32
```

## Performance Tips

1. **Batch Size**: Adjust in `worker.py` based on your GPU memory
2. **Number of Workers**: More workers = more parallelism, but each needs GPU memory
3. **Model Optimization**: Use ONNX optimization tools to reduce model size
4. **Test Data**: Reduce test set size for faster evaluation during development

## Next Steps

1. **Add Full Backend**: Implement FastAPI backend for file uploads
2. **Add Database**: Store submission results in PostgreSQL/SQLite
3. **Add Authentication**: Secure API with JWT tokens
4. **Add Monitoring**: Use Grafana/Prometheus for metrics
5. **Add Production Config**: Use full docker-compose.yml with 7 workers

## Support

- Check [DOCKER_GPU_SETUP.md](DOCKER_GPU_SETUP.md) for detailed documentation
- View worker logs for debugging: `docker compose logs -f worker-1`
- Test Redis connection: `docker compose exec redis redis-cli ping`
