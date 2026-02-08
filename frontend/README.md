# Frontend - MLS-GOAT Hackathon

This is the **web frontend** for the MLS-GOAT hackathon platform. Built with React, TypeScript, and Vite, it provides a modern, responsive interface for participants to register, submit solutions, and view leaderboards.

## 🎯 Purpose

The frontend provides a user-friendly interface for:
- **Team Registration & Login**: Secure authentication for hackathon participants
- **Submission Interface**: Upload Task 1 and Task 2 submissions
- **Live Leaderboards**: Real-time rankings for both tasks
- **Team Dashboard**: View submission history and statistics
- **Admin Panel**: Manage teams, moderate Q&A, and monitor platform
- **Q&A System**: Ask questions and view announcements

## 🏗️ Tech Stack

- **React 18**: UI library with hooks and functional components
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Shadcn/ui**: Component library (if configured)
- **Tailwind CSS**: Utility-first CSS framework (if configured)

## 🚀 Quick Start

### Prerequisites

- Node.js 16.0 or higher
- npm or yarn

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### Development

```bash
# Start development server with hot reload
npm run dev

# The app will be available at:
# http://localhost:5173
```

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build locally
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Auth/         # Login/registration components
│   │   ├── Leaderboard/  # Leaderboard display
│   │   ├── Submission/   # Submission forms
│   │   └── Admin/        # Admin dashboard components
│   ├── pages/            # Page components (routes)
│   │   ├── Home.tsx      # Landing page
│   │   ├── Login.tsx     # Login page
│   │   ├── Dashboard.tsx # Team dashboard
│   │   ├── Submit.tsx    # Submission page
│   │   └── Admin.tsx     # Admin panel
│   ├── services/         # API service layer
│   │   └── api.ts        # Backend API calls
│   ├── hooks/            # Custom React hooks
│   ├── utils/            # Helper functions
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Application entry point
├── public/               # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
└── README.md            # This file
```

## 🔌 API Integration

The frontend communicates with the backend service via REST API.

### Configuration

Update the API base URL in your environment or config:

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

Or create a `.env` file:

```env
VITE_API_URL=https://mls-goat.eastus2.cloudapp.azure.com/api
```

### Example API Service

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (name: string, password: string) => {
  const response = await api.post('/auth/login', { name, password });
  return response.data;
};

export const submitTask1 = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/submissions/task1', formData);
  return response.data;
};

export const getLeaderboard = async (task: number) => {
  const response = await api.get(`/leaderboard/task${task}`);
  return response.data;
};
```

## 🎨 Features

### 1. Authentication

- Team login with JWT tokens
- Token stored in localStorage
- Protected routes for authenticated users
- Auto-redirect on logout/token expiry

### 2. Submission Interface

**Task 1: Image Reconstruction**
- Upload ZIP file containing `.pt` files
- File validation before upload
- Progress indicator during upload
- Immediate score display

**Task 2: Model Inference**
- Upload ONNX model file
- File size validation
- Submission to GPU service
- Score display when available

### 3. Leaderboard

- Real-time rankings for both tasks
- Highlight current team's position
- Sortable columns
- Refresh functionality
- Top 10 teams + current team position

### 4. Dashboard

- Submission history
- Personal best scores
- Team statistics
- Recent submissions

### 5. Admin Panel

- Manage teams (create, edit, delete)
- Bulk team import from CSV
- Q&A moderation
- Platform statistics
- System monitoring

## 🔐 Authentication Flow

```typescript
// Login flow
const handleLogin = async (name: string, password: string) => {
  try {
    const { access_token } = await login(name, password);
    localStorage.setItem('token', access_token);
    localStorage.setItem('team_name', name);
    navigate('/dashboard');
  } catch (error) {
    setError('Invalid credentials');
  }
};

// Protected route
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};
```

## 📱 Responsive Design

The frontend is fully responsive and works on:
- Desktop (1920px and above)
- Laptop (1024px - 1920px)
- Tablet (768px - 1024px)
- Mobile (320px - 768px)

## 🧪 Development

### Running Tests

```bash
# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Linting

```bash
# Run ESLint
npm run lint

# Fix ESLint issues automatically
npm run lint:fix
```

### Type Checking

```bash
# Run TypeScript compiler check
npm run type-check
```

## 🚀 Deployment

### Building for Production

```bash
# Create production build
npm run build

# Output will be in ./dist directory
```

### Deployment Options

1. **Static Hosting (Netlify, Vercel, etc.)**
   ```bash
   # Build and deploy
   npm run build
   # Deploy ./dist folder
   ```

2. **Docker**
   ```dockerfile
   FROM node:16-alpine as build
   WORKDIR /app
   COPY package*.json ./
   RUN npm install
   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=build /app/dist /usr/share/nginx/html
   EXPOSE 80
   ```

3. **Serve with Backend**
   - Build the frontend
   - Copy `dist` folder to backend's static files directory
   - Serve via backend's static file handler

### Environment Variables

Set these for production:

```env
VITE_API_URL=https://your-backend-domain.com/api
VITE_GPU_SERVICE_URL=https://your-gpu-service.com
VITE_APP_NAME=MLS-GOAT Hackathon
```

## 🎨 Customization

### Branding

Update branding in:
- `index.html`: Title and meta tags
- `public/`: Logo and favicon
- `src/App.tsx`: App name and theme

### Theme

If using Tailwind CSS:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#your-color',
        secondary: '#your-color',
      },
    },
  },
};
```

## 🐛 Troubleshooting

### Build Errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite
npm run dev
```

### CORS Issues

If you encounter CORS errors:
- Ensure backend has proper CORS configuration
- Check API URL is correct
- Verify backend is running

### API Connection Failed

```typescript
// Check API connectivity
fetch('http://localhost:8000/')
  .then(res => console.log('Backend is reachable'))
  .catch(err => console.error('Cannot reach backend:', err));
```

## 📚 Dependencies

Key dependencies (see `package.json` for full list):

- **react**: UI library
- **react-dom**: React renderer
- **react-router-dom**: Routing
- **axios**: HTTP client
- **typescript**: Type checking
- **vite**: Build tool and dev server

## 🔧 Vite Configuration

The project uses Vite for fast development and optimized builds:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'  // Proxy API calls during dev
    }
  }
})
```

## 📖 Learn More

- [React Documentation](https://react.dev)
- [TypeScript Documentation](https://www.typescriptlang.org)
- [Vite Documentation](https://vitejs.dev)
- [React Router Documentation](https://reactrouter.com)

## 📄 License

Part of the MLS-GOAT hackathon platform.

---

**Frontend - Modern web interface for GOAT Hackathon participants** 🎨
