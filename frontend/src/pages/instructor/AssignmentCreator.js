// frontend/src/pages/instructor/AssignmentCreator.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';

function AssignmentCreator() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    due_date: '',
    available_from: '',
    available_until: '',
    points_possible: 100,
    submission_type: 'online_text',
    is_published: false,
    allow_late_submissions: true,
    late_submission_penalty: 0
  });

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchCourse() {
      try {
        // Get course details to check permissions
        const courseData = await api.getCourseById(courseId);
        setCourse(courseData);

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
      [name]: type === 'checkbox' ? checked :
              type === 'number' ? parseFloat(value) : value
    });
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Create assignment
      const assignmentData = {
        ...formData,
        course_id: parseInt(courseId)
      };

      const response = await api.createAssignment(assignmentData);

      // Upload attached file if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('assignment_id', response.id);
        formData.append('description', 'Assignment instructions');
        formData.append('is_public', 'true');

        await api.uploadFile(formData);
      }

      // Redirect to the course page
      navigate(`/courses/${courseId}`);
    } catch (err) {
      setError('Failed to create assignment. Please try again.');
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

      <h1 className="text-3xl font-bold mb-6">Create Assignment for {course.title}</h1>

      {error && (
        <div className="alert alert-error mb-6">
          <p>{error}</p>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block font-semibold mb-2">
              Assignment Title:
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
              Description/Instructions:
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              className="form-input h-32"
              placeholder="Enter assignment instructions..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="due_date" className="block font-semibold mb-2">
                Due Date:
              </label>
              <input
                type="datetime-local"
                id="due_date"
                name="due_date"
                value={formData.due_date}
                onChange={handleChange}
                className="form-input"
              />
            </div>

            <div>
              <label htmlFor="points_possible" className="block font-semibold mb-2">
                Points Possible:
              </label>
              <input
                type="number"
                id="points_possible"
                name="points_possible"
                value={formData.points_possible}
                onChange={handleChange}
                className="form-input"
                min="0"
                step="0.1"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="available_from" className="block font-semibold mb-2">
                Available From:
              </label>
              <input
                type="datetime-local"
                id="available_from"
                name="available_from"
                value={formData.available_from}
                onChange={handleChange}
                className="form-input"
              />
            </div>

            <div>
              <label htmlFor="available_until" className="block font-semibold mb-2">
                Available Until:
              </label>
              <input
                type="datetime-local"
                id="available_until"
                name="available_until"
                value={formData.available_until}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          </div>

          <div className="mb-4">
            <label htmlFor="submission_type" className="block font-semibold mb-2">
              Submission Type:
            </label>
            <select
              id="submission_type"
              name="submission_type"
              value={formData.submission_type}
              onChange={handleChange}
              className="form-input"
              required
            >
              <option value="online_text">Text Entry</option>
              <option value="online_upload">File Upload</option>
              <option value="online_quiz">Online Quiz</option>
              <option value="discussion">Discussion</option>
              <option value="external_tool">External Tool</option>
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="assignment_file" className="block font-semibold mb-2">
              Attach Instructions File (Optional):
            </label>
            <input
              type="file"
              id="assignment_file"
              onChange={handleFileChange}
              className="form-input"
            />
            <p className="text-gray-500 text-sm mt-1">
              {selectedFile ? `Selected: ${selectedFile.name}` : 'No file selected'}
            </p>
          </div>

          <div className="mb-4">
            <div className="flex items-center mb-2">
              <input
                type="checkbox"
                id="allow_late_submissions"
                name="allow_late_submissions"
                checked={formData.allow_late_submissions}
                onChange={handleChange}
                className="mr-2"
              />
              <label htmlFor="allow_late_submissions" className="font-semibold">
                Allow Late Submissions
              </label>
            </div>

            {formData.allow_late_submissions && (
              <div className="ml-6 mt-2">
                <label htmlFor="late_submission_penalty" className="block font-semibold mb-2">
                  Late Submission Penalty (%):
                </label>
                <input
                  type="number"
                  id="late_submission_penalty"
                  name="late_submission_penalty"
                  value={formData.late_submission_penalty}
                  onChange={handleChange}
                  className="form-input w-20"
                  min="0"
                  max="100"
                  step="1"
                />
                <p className="text-gray-500 text-sm mt-1">
                  Percentage deducted from the score for late submissions
                </p>
              </div>
            )}
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
              Published assignments are visible to students enrolled in the course
            </p>
          </div>

          <div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Creating...' : 'Create Assignment'}
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

export default AssignmentCreator;