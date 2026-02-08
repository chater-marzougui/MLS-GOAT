# Backend Service - MLS-GOAT Hackathon

This is the **CPU-based backend service** for the MLS-GOAT hackathon platform. It handles authentication, team management, database operations, Task 1 scoring, and provides REST API endpoints for the frontend and GOAT framework.

## 🎯 Purpose

The backend service is responsible for:
- **Authentication & Authorization**: JWT-based auth for teams and admins
- **Database Management**: SQLite database with SQLAlchemy ORM
- **Team Management**: Registration, profile management
- **Task 1 Scoring**: CPU-based PSNR calculation for image reconstruction
- **Leaderboard**: Real-time rankings for both tasks
- **Admin Panel**: Team management, Q&A moderation
- **GPU Service Integration**: Callback handling for Task 2 scores

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│              Backend Service (CPU-based)             │
│                                                      │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   FastAPI  │  │   SQLAlchemy │  │  JWT Auth   ││
│  │   Server   │──│   + SQLite   │──│  + bcrypt   ││
│  └─────┬──────┘  └──────────────┘  └─────────────┘│
│        │                                            │
│  ┌─────▼────────────────────────────────────────┐  │
│  │              API Routers                     │  │
│  │  • auth       - Login/authentication         │  │
│  │  • teams      - Team management              │  │
│  │  • submissions- Submit & score Task 1        │  │
│  │  • leaderboard- Rankings & stats             │  │
│  │  • admin      - Admin operations             │  │
│  │  • qa         - Q&A system                   │  │
│  │  • gpu_callback - Task 2 score updates      │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
    ┌────┴────────┐                   ┌──────┴──────┐
    │  Frontend   │                   │ GPU Service │
    │  (React)    │                   │  (Task 2)   │
    └─────────────┘                   └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Ground truth data for Task 1 (in `./data/gt_task1/`)

### Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Create initial admin user (optional but recommended)
python create_initial_admin.py
```

### Running the Server

```bash
# Development mode (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will start at: **http://localhost:8000**

### First-Time Setup

1. **Create Admin User**:
   ```bash
   python create_initial_admin.py
   ```
   This creates an admin account for managing the platform.

2. **Prepare Ground Truth Data**:
   Place Task 1 ground truth images in `./data/gt_task1/`
   - Files should be named: `sample_0000.pt`, `sample_0001.pt`, etc.
   - Format: PyTorch tensor files

3. **Configure GPU Server** (if using Task 2):
   Update the GPU server URL in `main.py` or via API:
   ```python
   # In main.py
   gpu_server_ip = "https://your-gpu-service-url.com"
   ```

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── models.py                  # SQLAlchemy database models
├── schemas.py                 # Pydantic schemas for validation
├── database.py                # Database configuration
├── utils.py                   # Helper functions (auth, etc.)
├── scoring.py                 # Task 1 scoring logic (PSNR)
├── create_initial_admin.py    # Admin user creation script
├── requirements.txt           # Python dependencies
├── routers/                   # API endpoint modules
│   ├── auth.py               # Login/authentication endpoints
│   ├── teams.py              # Team management endpoints
│   ├── submissions.py        # Submission & Task 1 scoring
│   ├── leaderboard.py        # Leaderboard endpoints
│   ├── admin.py              # Admin operations
│   ├── qa.py                 # Q&A system
│   └── gpu_callback.py       # GPU service callbacks
├── data/                      # Data directory
│   └── gt_task1/             # Ground truth for Task 1
└── temp/                      # Temporary upload files
```

## 🔌 API Endpoints

### Authentication

- `POST /auth/login` - Team/admin login
  ```json
  {
    "name": "team_awesome",
    "password": "password123"
  }
  ```
  Returns: JWT access token

- `GET /auth/me` - Get current user info (requires auth)

### Teams

- `GET /teams/` - List all teams (admin only)
- `GET /teams/{team_id}` - Get team details
- `POST /teams/` - Create new team (admin only)
- `PUT /teams/{team_id}` - Update team info

### Submissions (Task 1)

- `POST /submissions/task1` - Submit Task 1 (image reconstruction)
  - Upload: ZIP file containing `.pt` tensor files
  - Expected files: `sample_0000.pt` to `sample_0299.pt`
  - Returns: PSNR score

- `GET /submissions/` - Get team's submission history
- `GET /submissions/{submission_id}` - Get specific submission details

### Leaderboard

- `GET /leaderboard/task1` - Task 1 leaderboard (PSNR-based)
  - Optional: `?team_name=team_awesome` to highlight specific team

- `GET /leaderboard/task2` - Task 2 leaderboard (model performance)
  - Optional: `?team_name=team_awesome` to highlight specific team

### Admin

- `GET /admin/teams` - Manage all teams
- `POST /admin/teams` - Bulk create teams from CSV
- `DELETE /admin/teams/{team_id}` - Delete a team
- `GET /admin/stats` - Platform statistics

### Q&A

- `GET /qa/questions` - List all questions
- `POST /qa/questions` - Submit a question
- `PUT /qa/questions/{question_id}` - Update question/answer (admin)

### GPU Callback

- `POST /gpu-callback/task2` - Receive Task 2 scores from GPU service
  ```json
  {
    "team_id": 1,
    "score": 0.95,
    "metrics": {...}
  }
  ```

### Configuration

- `GET /gpu-server-ip` - Get GPU server URL
- `POST /gpu-server-ip` - Set GPU server URL (admin)

## 💾 Database

### Technology

- **SQLite** with WAL mode for better concurrency
- **SQLAlchemy** ORM for database operations
- Connection pooling and timeout configuration for stability

### Models

1. **Team**: Stores team information
   - `id`, `name`, `password_hash`, `is_admin`, `created_at`

2. **Submission**: Records all submissions
   - `id`, `team_id`, `task_number`, `score`, `submitted_at`, `file_path`

3. **Question**: Q&A system
   - `id`, `team_id`, `question`, `answer`, `answered`, `created_at`

### Database Configuration

```python
# database.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Enhanced configuration:
- WAL mode for concurrent access
- Pool size: 20 connections
- Max overflow: 40
- Connection pre-ping enabled
- Connection recycling: 1 hour
```

## 🔐 Authentication & Security

### JWT Tokens

- Uses JWT (JSON Web Tokens) for stateless authentication
- Tokens contain team ID and expiration
- Secret key configured in `utils.py`

### Password Hashing

- Passwords hashed with **bcrypt**
- Salted hashing for security
- Verification on login

### Example Login Flow

```python
# 1. Team submits credentials
POST /auth/login
{
  "name": "team_awesome",
  "password": "secret_password"
}

# 2. Backend verifies password hash
# 3. Returns JWT token
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# 4. Include token in subsequent requests
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📊 Task 1 Scoring (PSNR)

Task 1 evaluates image reconstruction quality using **Peak Signal-to-Noise Ratio (PSNR)**.

### Scoring Process

1. Team uploads ZIP file with reconstructed images
2. Backend extracts and validates files:
   - Expected: `sample_0000.pt` to `sample_0299.pt` (300 files)
   - Format: PyTorch tensors
3. For each image:
   - Load submission tensor
   - Load ground truth tensor from `data/gt_task1/`
   - Calculate PSNR between them
4. Return average PSNR score

### PSNR Formula

```python
def calculate_psnr(img1, img2):
    mse = torch.mean((img1 - img2) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 1.0  # Assuming normalized images
    psnr = 20 * torch.log10(max_pixel / torch.sqrt(mse))
    return psnr.item()
```

Higher PSNR = Better reconstruction quality

### File Requirements

- **Count**: Exactly 300 files
- **Names**: `sample_0000.pt`, `sample_0001.pt`, ..., `sample_0299.pt`
- **Format**: PyTorch tensor files (`.pt`)
- **Content**: Reconstructed images matching ground truth dimensions

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./sql_app.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# GPU Service
GPU_SERVER_URL=http://gpu-service:8000

# Server
HOST=0.0.0.0
PORT=8000
```

### CORS Configuration

The backend allows cross-origin requests for frontend integration:

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📈 Monitoring & Logging

### Startup Checks

On startup, the backend:
1. Creates database tables if they don't exist
2. Creates `temp/` directory for uploads
3. Verifies `data/gt_task1/` exists (warns if missing)

### Logs

The server logs:
- API requests and responses
- Authentication attempts
- Submission processing
- Errors and warnings

```bash
# View logs when running
uvicorn main:app --log-level info
```

## 🧪 Testing

### Manual Testing

```bash
# Test server is running
curl http://localhost:8000/

# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name":"admin","password":"admin_password"}'

# Test leaderboard
curl http://localhost:8000/leaderboard/task1
```

### Using the API Documentation

Visit http://localhost:8000/docs for interactive API testing with Swagger UI.

## 🐛 Troubleshooting

### Database Locked Error

```bash
# SQLite is locked due to concurrent access
# Solution: The backend already uses WAL mode, but if issues persist:

# 1. Check database file permissions
chmod 666 sql_app.db

# 2. Ensure no other processes are accessing the database
# 3. Increase timeout in database.py
```

### Ground Truth Not Found

```bash
# Error: Ground truth directory not found
# Solution: Create the directory and add ground truth files

mkdir -p data/gt_task1
# Copy ground truth .pt files to this directory
```

### Port Already in Use

```bash
# Error: Address already in use
# Solution: Use a different port

uvicorn main:app --port 8001
```

### Import Errors

```bash
# Error: Module not found
# Solution: Reinstall dependencies

pip install -r requirements.txt --force-reinstall
```

## 🚀 Deployment

### Production Recommendations

1. **Use a Production Server**:
   ```bash
   # Install gunicorn
   pip install gunicorn
   
   # Run with multiple workers
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8000
   ```

2. **Use PostgreSQL Instead of SQLite**:
   ```python
   # database.py
   SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/mlsgoat"
   ```

3. **Configure CORS Properly**:
   ```python
   # main.py - only allow your frontend domain
   allow_origins=["https://your-frontend-domain.com"]
   ```

4. **Use Environment Variables**:
   ```bash
   export SECRET_KEY=$(openssl rand -hex 32)
   export DATABASE_URL="postgresql://..."
   ```

5. **Enable HTTPS**:
   Use a reverse proxy like Nginx with SSL certificates

6. **Set Up Monitoring**:
   - Application logs
   - Database performance
   - API response times

## 📚 Dependencies

Key dependencies (see `requirements.txt` for full list):

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **sqlalchemy**: Database ORM
- **python-multipart**: File upload support
- **torch**: PyTorch for PSNR calculation
- **numpy**: Numerical operations
- **python-jose**: JWT token handling
- **passlib**: Password hashing
- **requests**: HTTP client for GPU service

## 🤝 Integration with Other Services

### With GPU Service (Task 2)

The backend communicates with the GPU service for Task 2:

1. Team submits ONNX model via GOAT framework
2. Backend forwards model to GPU service
3. GPU service evaluates model and returns score
4. GPU service calls back to `/gpu-callback/task2` with results
5. Backend updates leaderboard

### With Frontend

The frontend connects to the backend via REST API:

1. Users login via `/auth/login`
2. Submit files via `/submissions/*`
3. View leaderboards via `/leaderboard/*`
4. Admins manage platform via `/admin/*`

### With GOAT Framework

The GOAT submission framework calls the backend API:

```python
# GOAT/submit.py uses these endpoints:
- POST /auth/login
- POST /submissions/task1
- POST /submissions/task2 (forwards to GPU service)
```

## 📄 License

Part of the MLS-GOAT hackathon platform.

---

**Backend Service - CPU-based scoring, authentication, and database management for GOAT Hackathon**
