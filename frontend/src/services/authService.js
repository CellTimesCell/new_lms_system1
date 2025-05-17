import axios from 'axios';

const API_URL = process.env.REACT_APP_CORE_API_URL;

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor to add auth token
apiClient.interceptors.request.use(
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

// Auth service functions
export const authService = {
  token: null,

  setToken(token) {
    this.token = token;
  },

  clearToken() {
    this.token = null;
  },

  async login(username, password) {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post(`${API_URL}/auth/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  async register(userData) {
    try {
      const response = await axios.post(`${API_URL}/auth/register`, userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  },

  async getCurrentUser() {
    try {
      const response = await apiClient.get('/auth/me');
      return {
        id: response.data.id,
        username: response.data.username,
        email: response.data.email,
        firstName: response.data.first_name,
        lastName: response.data.last_name,
        roles: response.data.roles,
        isActive: response.data.is_active,
        isVerified: response.data.is_verified,
        preferredLanguage: response.data.preferred_language
      };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get user information');
    }
  },

  async refreshToken(refreshToken) {
    try {
      const response = await axios.post(`${API_URL}/auth/refresh`, {
        refresh_token: refreshToken
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Token refresh failed');
    }
  },

  async forgotPassword(email) {
    try {
      const response = await axios.post(`${API_URL}/auth/request-password-reset`, {
        email
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Password reset request failed');
    }
  },

  async resetPassword(token, password) {
    try {
      const response = await axios.post(`${API_URL}/auth/reset-password`, {
        token,
        password
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Password reset failed');
    }
  },

  async verifyEmail(token) {
    try {
      const response = await axios.post(`${API_URL}/auth/verify-email`, {
        token
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Email verification failed');
    }
  },

  async updateProfile(profileData) {
    try {
      const response = await apiClient.put(`/users/${profileData.userId}`, profileData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Profile update failed');
    }
  },

  async updateUserProfile(userId, profileData) {
    try {
      const response = await apiClient.put(`/users/profiles/${userId}`, profileData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Profile update failed');
    }
  }
};