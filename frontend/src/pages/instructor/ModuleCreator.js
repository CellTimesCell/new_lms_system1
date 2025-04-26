// frontend/src/pages/instructor/ModuleCreator.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

function ModuleCreator() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    position: 1,
    is_published: false
  });

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchCourse() {
      try {
        // Get course details to check permissions
        const courseData = await api.getCourseById(courseId);
        setCourse(courseData);

        // Set default position to be after the last module
        if (courseData.modules && courseData.modules.length > 0) {
          const lastPosition = Math.max(...courseData.modules.map(module => module.position));
          setFormData({
            ...formData,
            position: lastPosition + 1
          });
        }

        // Check if user is instructor for this course
        const isInstructor = currentUser && (
          currentUser.roles.includes('admin') ||
          currentUser.id === courseData.instructor_id
        );

        if (!isInstructor) {
          navigate(`/courses/${courseId}`);
        }
      } catch (err) {
        setError('Failed to load course details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchCourse();
  }, [courseId, currentUser, navigate]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Create module
      const moduleData = {
        ...formData,
        position: parseInt(formData.position)
      };

      const response = await api.createModule(courseId, moduleData);

      // Redirect to the course page
      navigate(`/courses/${courseId}`);
    } catch (err) {
      setError('Failed to create module. Please try again.');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading course details...</p>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-10">
        <p className="text-xl">Course not found</p>
        <p className="mt-2">
          <Link to="/dashboard" className="btn btn-primary">Return to Dashboard</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link to={`/courses/${courseId}`} className="btn btn-secondary">
          Back to Course
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-6">Create Module for {course.title}</h1>

      {error && (
        <div className="alert alert-error mb-6">
          <p>{error}</p>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block font-semibold mb-2">
              Module Title:
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
            <label htmlFor="description" className="block font-semibold mb-2">
              Description:
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              className="form-input h-32"
              placeholder="Enter module description..."
            />
          </div>

          <div className="mb-4">
            <label htmlFor="position" className="block font-semibold mb-2">
              Position:
            </label>
            <input
              type="number"
              id="position"
              name="position"
              value={formData.position}
              onChange={handleChange}
              className="form-input w-20"
              min="1"
              required
            />
            <p className="text-gray-500 text-sm mt-1">
              Order in which this module appears in the course
            </p>
          </div>

          <div className="mb-6">
            <div className="flex items-center mb-2">
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
              Published modules are visible to students enrolled in the course
            </p>
          </div>

          <div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Creating...' : 'Create Module'}
            </button>
            <button
              type="button"
              className="btn btn-secondary ml-2"
              onClick={() => navigate(`/courses/${courseId}`)}
              disabled={submitting}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ModuleCreator;