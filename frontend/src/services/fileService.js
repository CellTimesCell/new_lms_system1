import { filesApi, handleApiError } from './api';

export const fileService = {
  async uploadFile(file, options = {}) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      // Add optional parameters
      if (options.description) formData.append('description', options.description);
      if (options.courseId) formData.append('course_id', options.courseId);
      if (options.moduleId) formData.append('module_id', options.moduleId);
      if (options.assignmentId) formData.append('assignment_id', options.assignmentId);
      if (options.submissionId) formData.append('submission_id', options.submissionId);
      if (options.isPublic !== undefined) formData.append('is_public', options.isPublic);

      const response = await filesApi.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getFiles(params = {}) {
    try {
      const response = await filesApi.get('/', { params });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  getFileUrl(fileId) {
    return `${process.env.REACT_APP_FILES_API_URL}/download/${fileId}`;
  },

  async deleteFile(fileId) {
    try {
      const response = await filesApi.delete(`/${fileId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
};