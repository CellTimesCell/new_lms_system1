import { coreApi, handleApiError } from './api';

export const assignmentService = {
  async getAssignments(courseId) {
    try {
      const response = await coreApi.get(`/assignments/course/${courseId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getAssignmentById(assignmentId) {
    try {
      const response = await coreApi.get(`/assignments/${assignmentId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async createAssignment(assignmentData) {
    try {
      const response = await coreApi.post('/assignments/', assignmentData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async updateAssignment(assignmentId, assignmentData) {
    try {
      const response = await coreApi.put(`/assignments/${assignmentId}`, assignmentData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async deleteAssignment(assignmentId) {
    try {
      const response = await coreApi.delete(`/assignments/${assignmentId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async submitAssignment(assignmentId, submissionData) {
    try {
      const response = await coreApi.post(`/assignments/${assignmentId}/submit`, submissionData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getSubmission(submissionId) {
    try {
      const response = await coreApi.get(`/assignments/submission/${submissionId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getSubmissions(assignmentId) {
    try {
      const response = await coreApi.get(`/assignments/${assignmentId}/submissions`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async gradeSubmission(submissionId, gradeData) {
    try {
      const response = await coreApi.post(`/grading/submissions/${submissionId}/grade`, gradeData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
};