import { coreApi, handleApiError } from './api';

export const courseService = {
  async getCourses(params = {}) {
    try {
      const response = await coreApi.get('/courses/', { params });
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getCourseById(courseId) {
    try {
      const response = await coreApi.get(`/courses/${courseId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async createCourse(courseData) {
    try {
      const response = await coreApi.post('/courses/', courseData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async updateCourse(courseId, courseData) {
    try {
      const response = await coreApi.put(`/courses/${courseId}`, courseData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async deleteCourse(courseId) {
    try {
      const response = await coreApi.delete(`/courses/${courseId}`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getModules(courseId) {
    try {
      const response = await coreApi.get(`/courses/${courseId}/modules`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async createModule(courseId, moduleData) {
    try {
      const response = await coreApi.post(`/courses/${courseId}/modules`, moduleData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getContentItems(moduleId) {
    try {
      const response = await coreApi.get(`/courses/modules/${moduleId}/content`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async createContentItem(moduleId, contentData) {
    try {
      const response = await coreApi.post(`/courses/modules/${moduleId}/content`, contentData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async enrollInCourse(courseId, studentId) {
    try {
      const enrollmentData = {
        student_id: studentId,
        course_id: courseId,
        is_active: true
      };

      const response = await coreApi.post('/courses/enroll', enrollmentData);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getMyEnrollments() {
    try {
      const response = await coreApi.get('/courses/enrollments/me');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  },

  async getCourseEnrollments(courseId) {
    try {
      const response = await coreApi.get(`/courses/${courseId}/enrollments`);
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
};