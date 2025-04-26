import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function CourseDetail() {
  const { courseId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [courseFiles, setCourseFiles] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchCourseData() {
      try {
        const [courseData, filesData] = await Promise.all([
          api.getCourseById(courseId),
          api.getFiles({ course_id: courseId })
        ]);

        setCourse(courseData);
        setCourseFiles(filesData);
      } catch (err) {
        setError('Failed to load course details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchCourseData();
  }, [courseId]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploadingFile(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('course_id', courseId);
      formData.append('description', 'Course material');
      formData.append('is_public', 'true');

      await api.uploadFile(formData);

      // Refresh file list
      const filesData = await api.getFiles({ course_id: courseId });
      setCourseFiles(filesData);

      // Reset file input
      setSelectedFile(null);
      document.getElementById('file-upload').value = '';
    } catch (err) {
      setError('Failed to upload file');
      console.error(err);
    } finally {
      setUploadingFile(false);
    }
  };

  const isInstructor = currentUser && course && (
    currentUser.roles.includes('admin') ||
    currentUser.id === course.instructor_id
  );

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading course details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <p>{error}</p>
        <p className="mt-2">
          <Link to="/courses" className="btn btn-primary">Return to courses</Link>
        </p>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="text-center py-10">
        <p className="text-xl">Course not found</p>
        <p className="mt-2">
          <Link to="/courses" className="btn btn-primary">Return to courses</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link to="/courses" className="btn btn-secondary">
          Back to Courses
        </Link>
      </div>

      <div className="card mb-8">
        <h1 className="text-3xl font-bold mb-2">{course.title}</h1>
        <p className="mb-4">{course.description}</p>

        <div className="mb-4">
          <span className="font-semibold">Course Code:</span>
          <span className="ml-2">{course.code}</span>
        </div>

        {course.start_date && (
          <div className="mb-4">
            <span className="font-semibold">Start Date:</span>
            <span className="ml-2">{new Date(course.start_date).toLocaleDateString()}</span>
          </div>
        )}

        {course.end_date && (
          <div className="mb-4">
            <span className="font-semibold">End Date:</span>
            <span className="ml-2">{new Date(course.end_date).toLocaleDateString()}</span>
          </div>
        )}
      </div>

      {/* Course Materials Section */}
      <div className="card mb-8">
        <h2 className="text-xl font-bold mb-4">Course Materials</h2>

        {courseFiles.length === 0 ? (
          <p>No materials available for this course yet.</p>
        ) : (
          <ul className="mb-4">
            {courseFiles.map(file => (
              <li key={file.id} className="mb-2">
                <a
                  href={file.url}
                  className="text-blue-500 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {file.original_filename}
                </a>
                <span className="text-gray-500 ml-2">
                  ({(file.file_size / 1024).toFixed(2)} KB)
                </span>
              </li>
            ))}
          </ul>
        )}

        {/* File Upload for Instructors */}
        {isInstructor && (
          <div className="mt-4">
            <h3 className="font-bold mb-2">Upload Course Material</h3>
            <div className="flex items-center">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                className="form-input"
              />
              <button
                onClick={handleFileUpload}
                disabled={!selectedFile || uploadingFile}
                className="btn btn-primary ml-2"
              >
                {uploadingFile ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modules Section */}
      <div className="card mb-8">
        <h2 className="text-xl font-bold mb-4">Modules</h2>

        {!course.modules || course.modules.length === 0 ? (
          <p>No modules available for this course yet.</p>
        ) : (
          <div className="space-y-4">
            {course.modules.map(module => (
              <div key={module.id} className="card">
                <h3 className="text-lg font-bold mb-2">{module.title}</h3>
                <p className="mb-4">{module.description}</p>
                <Link
                  to={`/modules/${module.id}`}
                  className="btn btn-primary"
                >
                  View Module
                </Link>
              </div>
            ))}
          </div>
        )}

        {/* Add Module Button for Instructors */}
        {isInstructor && (
          <div className="mt-4">
            <button
              onClick={() => navigate(`/courses/${courseId}/modules/create`)}
              className="btn btn-success"
            >
              Add Module
            </button>
          </div>
        )}
      </div>

      {/* Assignments Section */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Assignments</h2>

        {!course.assignments || course.assignments.length === 0 ? (
          <p>No assignments available for this course yet.</p>
        ) : (
          <div className="space-y-4">
            {course.assignments.map(assignment => (
              <div key={assignment.id} className="card">
                <h3 className="text-lg font-bold mb-2">{assignment.title}</h3>
                <p className="mb-4">{assignment.description}</p>

                <div className="mb-2">
                  <span className="font-semibold">Due Date:</span>
                  <span className="ml-2">
                    {assignment.due_date ? new Date(assignment.due_date).toLocaleString() : 'No due date'}
                  </span>
                </div>

                <div className="mb-4">
                  <span className="font-semibold">Points:</span>
                  <span className="ml-2">{assignment.points_possible}</span>
                </div>

                <Link
                  to={`/assignments/${assignment.id}`}
                  className="btn btn-primary"
                >
                  View Assignment
                </Link>

                {isInstructor && (
                  <Link
                    to={`/assignments/${assignment.id}/submissions`}
                    className="btn btn-secondary ml-2"
                  >
                    View Submissions
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Add Assignment Button for Instructors */}
        {isInstructor && (
          <div className="mt-4">
            <button
              onClick={() => navigate(`/courses/${courseId}/assignments/create`)}
              className="btn btn-success"
            >
              Add Assignment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default CourseDetail;