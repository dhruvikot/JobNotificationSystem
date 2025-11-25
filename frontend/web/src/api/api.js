import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getUser: (userId) => api.get(`/auth/user/${userId}`)
};

// Subscriptions API
export const subscriptionsAPI = {
  getTopics: () => api.get('/subscriptions/topics'),
  getSubscriptions: () => api.get('/subscriptions'),
  createSubscription: (data) => api.post('/subscriptions', data),
  deleteSubscription: (topic) => api.delete(`/subscriptions/${topic}`)
};

// Events API
export const eventsAPI = {
  getEvents: (params) => api.get('/events', { params }),
  getEvent: (eventId) => api.get(`/events/${eventId}`),
  createEvent: (data) => api.post('/events', data),
  updateEvent: (eventId, data) => api.put(`/events/${eventId}`, data),
  publishEvent: (eventId) => api.post(`/events/${eventId}/publish`)
};

// Notifications API
export const notificationsAPI = {
  getNotifications: (userId, params) => api.get(`/notifications/${userId}`, { params })
};

export default api;


