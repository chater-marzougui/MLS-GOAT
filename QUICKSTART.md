# Quick Start Guide

## Backend
Already running on `http://localhost:8000`

## Frontend
```bash
cd frontend
npm run dev
```
Access at `http://localhost:5173`

## Login Credentials
- **Admin**: `admin` / `admin`
- **Teams**: Created via admin dashboard

## Key Features
1. **JWT Authentication** - Secure token-based login
2. **Team Dashboard** - View leaderboards and submission history
3. **Admin Dashboard** - Manage teams and toggle private scores
4. **GOAT Branding** - Custom Electric Cyan (#11C5E8) theme

## New API Endpoints
- `GET /auth/me` - Current user info
- `GET /teams/me/submissions` - Submission history
- `GET /leaderboard/settings` - Check if private scores enabled
- `POST /admin/settings/leaderboard?show_private=true` - Toggle private scores

## File Structure
```
frontend/src/
├── lib/
│   ├── api.ts          # API client with JWT
│   └── auth.tsx        # Auth context
├── pages/
│   ├── Login.tsx       # Login page
│   ├── TeamDashboard.tsx
│   └── AdminDashboard.tsx
├── components/
│   ├── Leaderboard.tsx
│   └── SubmissionHistory.tsx
└── App.tsx             # Routes & protected routes
```
