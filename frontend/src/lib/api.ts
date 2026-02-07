import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: (name: string, password: string) =>
    api.post('/auth/login', { name, password }),
  getCurrentUser: () => api.get('/auth/me'),
};

// Teams API
export const teamsAPI = {
  getMySubmissions: () => api.get('/teams/me/submissions'),
  getMySubmissionsByTask: (taskId: number) =>
    api.get(`/teams/me/submissions/${taskId}`),
};

// Leaderboard API
export const leaderboardAPI = {
  getTask1: () => api.get('/leaderboard/task1'),
  getTask2: () => api.get('/leaderboard/task2'),
  getSettings: () => api.get('/leaderboard/settings'),
};

// Admin API
export const adminAPI = {
  getTeams: () => api.get('/admin/teams'),
  createTeam: (name: string, password: string) =>
    api.post('/admin/teams', { name, password }),
  deleteTeam: (teamId: number) => api.delete(`/admin/teams/${teamId}`),
  batchCreateTeams: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/admin/teams/batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getAllSubmissions: () => api.get('/admin/submissions'),
  deleteSubmission: (submissionId: number) =>
    api.delete(`/admin/submissions/${submissionId}`),
  getLeaderboardSettings: () => api.get('/admin/settings/leaderboard'),
  updateLeaderboardSettings: (showPrivate: boolean) =>
    api.post(`/admin/settings/leaderboard?show_private=${showPrivate}`),
};

// QA API
export const qaAPI = {
  getQuestions: () => api.get('/qa/questions'),
  getQuestion: (id: number) => api.get(`/qa/questions/${id}`),
  createQuestion: (title: string, content: string) => api.post('/qa/questions', { title, content }),
  createAnswer: (questionId: number, content: string) => api.post(`/qa/questions/${questionId}/answers`, { content }),
  deleteQuestion: (id: number) => api.delete(`/qa/questions/${id}`),
  deleteAnswer: (id: number) => api.delete(`/qa/answers/${id}`),
};

export default api;
