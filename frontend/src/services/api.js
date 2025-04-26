// frontend/src/services/api.js

import axios from 'axios';

// Create API service
const api = {
  // Authentication
  login: async (username, password) => {
    const response = await axios.post('/api/v1/auth/token',
      new URLSearchParams({
        'username': username,
        'password': password
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
    return response.data;
  },

  register: async (userData) => {
    const response = await axios.post('/api/v1/users/', userData);
    return response.data;
  },

  // Password reset
  requestPasswordReset: async (email) => {
    const response = await axios.post('/api/v1/auth/request-password-reset', { email });
    return response.data;
  },

  resetPassword: async (token, password) => {
    const response = await axios.post('/api/v1/auth/reset-password', {
      token,
      password
    });
    return response.data;
  },

  // Users
  getUserProfile: async () => {
    const response = await axios.get('/api/v1/users/me');
    return response.data;
  },

  getUsers: async () => {
    const response = await axios.get('/api/v1/users/');
    return response.data;
  },

  getUserById: async (userId) => {
    const response = await axios.get(`/api/v1/users/${userId}`);
    return response.data;
  },

  updateUser: async (userId, userData) => {
    const response = await axios.put(`/api/v1/users/${userId}`, userData);
    return response.data;
  },

  createUserProfile: async (userId, profileData) => {
    const response = await axios.post(`/api/v1/users/profiles/${userId}`, profileData);
    return response.data;
  },

  updateUserProfile: async (userId, profileData) => {
    const response = await axios.put(`/api/v1/users/profiles/${userId}`, profileData);
    return response.data;
  },

  // Courses
  getCourses: async () => {
    const response = await axios.get('/api/v1/courses');
    return response.data;
  },

  getCourseById: async (courseId) => {
    const response = await axios.get(`/api/v1/courses/${courseId}`);
    return response.data;
  },

  createCourse: async (courseData) => {
    const response = await axios.post('/api/v1/courses/', courseData);
    return response.data;
  },

  updateCourse: async (courseId, courseData) => {
    const response = await axios.put(`/api/v1/courses/${courseId}`, courseData);
    return response.data;
  },

  // Modules
  createModule: async (courseId, moduleData) => {
    const response = await axios.post(`/api/v1/courses/${courseId}/modules`, moduleData);
    return response.data;
  },

  getModuleContent: async (moduleId) => {
    const response = await axios.get(`/api/v1/modules/${moduleId}/content`);
    return response.data;
  },

  // Assignments
  getAssignmentById: async (assignmentId) => {
    const response = await axios.get(`/api/v1/assignments/${assignmentId}`);
    return response.data;
  },

  createAssignment: async (assignmentData) => {
    const response = await axios.post('/api/v1/assignments/', assignmentData);
    return response.data;
  },

  submitAssignment: async (assignmentId, submissionData) => {
    const response = await axios.post(`/api/v1/assignments/${assignmentId}/submit`, submissionData);
    return response.data;
  },

  getMySubmission: async (assignmentId) => {
    const response = await axios.get(`/api/v1/assignments/${assignmentId}/my-submission`);
    return response.data;
  },

  // Submissions and grading
  getSubmissionDetail: async (submissionId) => {
    const response = await axios.get(`/api/v1/grading/submissions/${submissionId}`);
    return response.data;
  },

  gradeSubmission: async (submissionId, gradeData) => {
    const response = await axios.post(`/api/v1/grading/submissions/${submissionId}/grade`, gradeData);
    return response.data;
  },

  // Files
  uploadFile: async (formData) => {
    const response = await axios.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  getFiles: async (params = {}) => {
    const response = await axios.get('/api/files', { params });
    return response.data;
  },

  // Enrollments
  enrollInCourse: async (courseId) => {
    const user = JSON.parse(localStorage.getItem('user'));
    const enrollment = {
      student_id: user.id,
      course_id: courseId
    };

    const response = await axios.post('/api/v1/courses/enroll', enrollment);
    return response.data;
  },

  getMyEnrollments: async () => {
    const response = await axios.get('/api/v1/courses/enrollments/me');
    return response.data;
  }
};

// Request interceptor for adding token
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
axios.interceptors.response.use(
  response => response,
  error => {
    // Handle unauthorized errors (401)
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;