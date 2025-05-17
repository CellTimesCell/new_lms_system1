import axios from 'axios';

// API Base URLs
const CORE_API_URL = process.env.REACT_APP_CORE_API_URL;
const FILES_API_URL = process.env.REACT_APP_FILES_API_URL;
const ANALYTICS_API_URL = process.env.REACT_APP_ANALYTICS_API_URL;
const AI_API_URL = process.env.REACT_APP_AI_API_URL;
const NOTIFICATIONS_API_URL = process.env.REACT_APP_NOTIFICATIONS_API_URL;

// Create axios instances for different services
const createApiClient = (baseURL) => {
  const client = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // Add request interceptor to include auth token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor to handle errors
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle token expiration
      if (error.response && error.response.status === 401) {
        // Try to refresh token or redirect to login
        // This can be improved with a token refresh mechanism
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
};

// Create API clients
export const coreApi = createApiClient(CORE_API_URL);
export const filesApi = createApiClient(FILES_API_URL);
export const analyticsApi = createApiClient(ANALYTICS_API_URL);
export const aiApi = createApiClient(AI_API_URL);
export const notificationsApi = createApiClient(NOTIFICATIONS_API_URL);

// Helper function for error handling
export const handleApiError = (error) => {
  const errorMessage =
    error.response?.data?.detail ||
    error.response?.data?.message ||
    error.message ||
    'An unexpected error occurred';

  return errorMessage;
};