// frontend/src/pages/instructor/CourseCreator.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

function CourseCreator() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    title: '',
    code: '',
    description: '',
    start_date: '',
    end_date: '',
    is_active: true,
    is_published: false
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Add instructor_id to the form data
      const courseData = {
        ...formData,
        instructor_id: currentUser.id
      };

      // Create course
      const response = await api.createCourse(courseData);

      // Redirect to the new course page
      navigate(`/courses/${response.id}`);
    } catch (err) {
      setError('Failed to create course. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Create New Course</h1>

      {error && (
        <div className="alert alert-error mb-6">
          <p>{error}</p>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block font-semibold mb-2">
              Course Title:
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="code" className="block font-semibold mb-2">
              Course Code:
            </label>
            <input
              type="text"
              id="code"
              name="code"
              value={formData.code}
              onChange={handleChange}
              className="form-input"
              required
            />
            <p className="text-gray-500 text-sm mt-1">
              A unique code for the course (e.g., MATH101)
            </p>
          </div>

          <div className="mb-4">
            <label htmlFor="description" className="block font-semibold mb-2">
              Description:
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              className="form-input h-32"
              placeholder="Enter course description..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="start_date" className="block font-semibold mb-2">
                Start Date:
              </label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                value={formData.start_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>

            <div>
              <label htmlFor="end_date" className="block font-semibold mb-2">
                End Date:
              </label>
              <input
                type="date"
                id="end_date"
                name="end_date"
                value={formData.end_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          </div>

          <div className="mb-6">
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="is_active"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                className="mr-2"
              />
              <label htmlFor="is_active" className="font-semibold">
                Active
              </label>
            </div>
            <p className="text-gray-500 text-sm ml-6">
              Active courses are visible to enrolled students
            </p>

            <div className="flex items-center mt-4 mb-2">
              <input
                type="checkbox"
                id="is_published"
                name="is_published"
                checked={formData.is_published}
                onChange={handleChange}
                className="mr-2"
              />
              <label htmlFor="is_published" className="font-semibold">
                Published
              </label>
            </div>
            <p className="text-gray-500 text-sm ml-6">
              Published courses are visible in the course catalog
            </p>
          </div>

          <div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Course'}
            </button>
            <button
              type="button"
              className="btn btn-secondary ml-2"
              onClick={() => navigate(-1)}
              disabled={loading}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CourseCreator;