# MLS-GOAT: Gathering Of AI Talent Hackathon Platform

**MLS-GOAT** (Machine Learning Systems - Gathering Of AI Talent) is a comprehensive hackathon platform designed to evaluate machine learning models across multiple tasks. The platform features a distributed architecture with GPU-accelerated scoring and a user-friendly submission framework.

## 🏆 Hackathon Overview

This platform was created for the **GOAT Hackathon** (Gathering Of AI Talent), where participants compete on two challenging machine learning tasks:

- **Task 1**: Image Reconstruction - Participants submit reconstructed images evaluated using PSNR metrics
- **Task 2**: Model Inference - Participants submit ONNX models evaluated on GPU infrastructure

## 🏗️ Architecture

The platform consists of four main components working together:

```
┌─────────────────────────────────────────────────────────────────┐
│                          GOAT Hackathon                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐       ┌──────────▼──────────┐      ┌────────▼────────┐
│  Frontend UI   │       │  Backend Service    │      │  GPU Service    │
│  (React+Vite)  │◄─────►│  (CPU-based)        │◄────►│  (GPU-enabled)  │
│                │       │  - Auth & Teams     │      │  - Task 2 Eval  │
│                │       │  - DB Management    │      │  - ONNX Runtime │
│                │       │  - Task 1 Scoring   │      │  - Redis Queue  │
│                │       │  - Leaderboard      │      │                 │
└────────────────┘       └─────────────────────┘      └─────────────────┘
                                    ▲
                                    │
                         ┌──────────┴──────────┐
                         │   GOAT Framework    │
                         │  (Submission SDK)   │
                         │  - submit.py        │
                         │  - leaderboard.py   │
                         └─────────────────────┘
```

### Components

1. **Backend Service** (CPU-based)
   - FastAPI-based REST API
   - SQLite database for team management and submissions
   - Authentication with JWT tokens
   - Task 1 scoring (PSNR calculation)
   - Leaderboard management
   - Admin panel
   - Located in: `./backend/`

2. **GPU Service** (GPU-enabled)
   - GPU-accelerated ONNX model evaluation
   - Redis queue for job management
   - Docker-based deployment with CUDA support
   - Task 2 scoring (model inference benchmarking)
   - Located in: `./gpu-service/`

3. **GOAT Framework** (Submission Helper)
   - Python package for easy submissions
   - Simple API for challenge1() and challenge2()
   - Leaderboard viewing utilities
   - Handles authentication and file uploads
   - Located in: `./GOAT/`

4. **Frontend** (React + TypeScript)
   - Web UI for participants
   - Team registration and login
   - Submission interface
   - Real-time leaderboard
   - Admin dashboard
   - Located in: `./frontend/`

## 🚀 Quick Start

### Prerequisites

- **For Backend**: Python 3.8+, pip
- **For GPU Service**: Docker, Docker Compose, NVIDIA GPU with CUDA support
- **For Frontend**: Node.js 16+, npm
- **For GOAT Framework**: Python 3.8+, pip

### 1. Setup Backend Service (CPU-based)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create initial admin user (optional)
python create_initial_admin.py

# Run the backend server
uvicorn main:app --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

See [backend/README.md](./backend/README.md) for detailed documentation.

### 2. Setup GPU Service

```bash
cd gpu-service

# Install NVIDIA Container Toolkit (first time only)
./install_nvidia_docker.sh

# Build and start services
docker compose up -d

# Check status
docker compose ps
```

See [gpu-service/README.md](./gpu-service/README.md) for detailed documentation.

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

See [frontend/README.md](./frontend/README.md) for detailed documentation.

### 4. Using the GOAT Framework

```bash
# Install the GOAT package
pip install -e GOAT/

# Or add GOAT to your Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/MLS-GOAT"
```

See [GOAT/README.md](./GOAT/README.md) for usage examples.

## 📝 For Participants

### Submitting to Task 1 (Image Reconstruction)

```python
from GOAT.submit import challenge1

# Submit your reconstructed images
result = challenge1(
    folder_path="./my_reconstructions",
    team_id="team_awesome",
    password="my_password"
)
print(f"Score: {result['score']}")
```

### Submitting to Task 2 (Model Inference)

```python
from GOAT.submit import challenge2

# Submit your ONNX model
result = challenge2(
    model_path="./my_model.onnx",
    team_id="team_awesome",
    password="my_password"
)
print(f"Score: {result['score']}")
```

### Viewing Leaderboards

```python
from GOAT.leaderboard import getLB_chall1, getLB_chall2

# View Task 1 leaderboard
getLB_chall1(team_name="team_awesome")

# View Task 2 leaderboard
getLB_chall2(team_name="team_awesome")
```

## 🔧 Configuration

### Backend Configuration

The backend service uses environment variables and can be configured via `.env` file:

```env
DATABASE_URL=sqlite:///./sql_app.db
SECRET_KEY=your-secret-key-here
GPU_SERVER_URL=http://gpu-service:8000
```

### GPU Service Configuration

Configure GPU service in `gpu-service/docker-compose.yml`:

```yaml
environment:
  - GPU_MEMORY_FRACTION=0.25  # Adjust GPU memory per worker
  - REDIS_HOST=redis
  - REDIS_PORT=6379
```

## 📊 Tasks Description

### Task 1: Image Reconstruction (PSNR-based)
- Participants receive corrupted/incomplete images
- Goal: Reconstruct the original images
- Evaluation: Peak Signal-to-Noise Ratio (PSNR)
- Submission: Folder of `.pt` files (PyTorch tensors)
- Scoring: CPU-based, runs on backend service

### Task 2: Model Inference (Performance-based)
- Participants create ONNX models for a specific task
- Goal: Achieve best accuracy and/or speed
- Evaluation: GPU-accelerated inference benchmarking
- Submission: Single `.onnx` file
- Scoring: GPU-based, runs on dedicated GPU service

## 🛠️ Development

### Project Structure

```
MLS-GOAT/
├── backend/              # CPU-based backend service
│   ├── routers/         # API endpoints
│   ├── models.py        # Database models
│   ├── database.py      # Database configuration
│   ├── main.py          # FastAPI application
│   └── README.md        # Backend documentation
├── gpu-service/         # GPU-accelerated scoring service
│   ├── backend/         # Worker and API code
│   ├── docker-compose.yml
│   └── README.md        # GPU service documentation
├── GOAT/                # Submission framework
│   ├── submit.py        # Submission utilities
│   ├── leaderboard.py   # Leaderboard utilities
│   └── README.md        # GOAT framework documentation
├── frontend/            # React web interface
│   ├── src/
│   └── README.md        # Frontend documentation
└── README.md            # This file
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# GPU service tests
cd gpu-service
python test_api.py

# Frontend tests
cd frontend
npm test
```

## 🔐 Security Notes

- The platform uses JWT tokens for authentication
- Passwords are hashed using bcrypt
- CORS is configured for frontend-backend communication
- Admin endpoints are protected with role-based access control

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## 🤝 Contributing

This is a hackathon platform. For modifications:

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project was created for the GOAT (Gathering Of AI Talent) hackathon.

## 🆘 Support & Troubleshooting

### Common Issues

**Backend won't start**
- Check Python version (3.8+)
- Verify all dependencies are installed
- Ensure database file has write permissions

**GPU Service fails**
- Verify NVIDIA drivers are installed
- Check NVIDIA Container Toolkit installation
- Ensure Docker has GPU access: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`

**Submissions fail**
- Verify API URL in GOAT framework
- Check authentication credentials
- Ensure file formats match requirements

### Getting Help

For detailed documentation:
- Backend Service: [backend/README.md](./backend/README.md)
- GPU Service: [gpu-service/README.md](./gpu-service/README.md)
- GOAT Framework: [GOAT/README.md](./GOAT/README.md)
- Frontend: [frontend/README.md](./frontend/README.md)

---

**Built with ❤️ for the GOAT Hackathon - Gathering Of AI Talent**
