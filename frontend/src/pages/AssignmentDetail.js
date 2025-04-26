// frontend/src/pages/AssignmentDetail.js
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function AssignmentDetail() {
  const { assignmentId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [assignment, setAssignment] = useState(null);
  const [course, setCourse] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [submissionText, setSubmissionText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        // Get assignment details
        const assignmentData = await api.getAssignmentById(assignmentId);
        setAssignment(assignmentData);

        // Get course details
        if (assignmentData.course_id) {
          const courseData = await api.getCourseById(assignmentData.course_id);
          setCourse(courseData);
        }

        // Check if user has already submitted
        if (currentUser) {
          try {
            const existingSubmission = await api.getMySubmission(assignmentId);
            setSubmission(existingSubmission);
            setSubmissionText(existingSubmission.submission_text || '');
          } catch (submissionErr) {
            // No submission exists, continue
          }
        }
      } catch (err) {
        setError('Failed to load assignment details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [assignmentId, currentUser]);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!submissionText && !selectedFile) {
      setError('Please provide a text submission or upload a file');
      return;
    }

    setSubmitting(true);

    try {
      let submissionFiles = [];

      // Upload file if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('assignment_id', assignmentId);
        formData.append('description', 'Assignment submission');

        const fileResponse = await api.uploadFile(formData);
        submissionFiles.push({
          file_id: fileResponse.id,
          file_name: fileResponse.original_filename,
          file_url: fileResponse.url
        });
      }

      // Create submission
      const submissionData = {
        assignment_id: assignmentId,
        submission_text: submissionText,
        submission_files: submissionFiles
      };

      const response = await api.submitAssignment(assignmentId, submissionData);

      // Update the submission state
      setSubmission(response);

      // Show success message
      alert('Assignment submitted successfully!');

      // Reset file input
      setSelectedFile(null);
      document.getElementById('file-upload').value = '';
    } catch (err) {
      setError('Failed to submit assignment');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading assignment details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <p>{error}</p>
        <button onClick={() => setError('')} className="btn btn-secondary mt-2">
          Try Again
        </button>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="text-center py-10">
        <p className="text-xl">Assignment not found</p>
        <p className="mt-2">
          <Link to="/dashboard" className="btn btn-primary">Return to Dashboard</Link>
        </p>
      </div>
    );
  }

  const isInstructor = currentUser && course && (
    currentUser.roles.includes('admin') ||
    currentUser.id === course.instructor_id
  );

  const isPastDue = assignment.due_date && new Date(assignment.due_date) < new Date();

  return (
    <div>
      <div className="mb-6">
        {course && (
          <Link to={`/courses/${course.id}`} className="btn btn-secondary">
            Back to Course
          </Link>
        )}
      </div>

      <div className="card mb-8">
        <h1 className="text-3xl font-bold mb-2">{assignment.title}</h1>
        <p className="mb-4">{assignment.description}</p>

        <div className="mb-4">
          <span className="font-semibold">Points:</span>
          <span className="ml-2">{assignment.points_possible}</span>
        </div>

        {assignment.due_date && (
          <div className="mb-4">
            <span className="font-semibold">Due Date:</span>
            <span className={`ml-2 ${isPastDue ? 'text-red-500' : ''}`}>
              {new Date(assignment.due_date).toLocaleString()}
              {isPastDue && ' (Past Due)'}
            </span>
          </div>
        )}

        {/* Files related to this assignment */}
        {assignment.files && assignment.files.length > 0 && (
          <div className="mb-4">
            <h3 className="font-bold mb-2">Assignment Materials:</h3>
            <ul>
              {assignment.files.map(file => (
                <li key={file.id} className="mb-1">
                  <a
                    href={file.url}
                    className="text-blue-500 hover:underline"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {file.original_filename}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {isInstructor ? (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Instructor View</h2>
          <p>You are viewing this assignment as an instructor.</p>
          <div className="mt-4">
            <Link
              to={`/assignments/${assignmentId}/submissions`}
              className="btn btn-primary"
            >
              View Submissions
            </Link>
            <Link
              to={`/assignments/${assignmentId}/edit`}
              className="btn btn-secondary ml-2"
            >
              Edit Assignment
            </Link>
          </div>
        </div>
      ) : (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">
            {submission ? 'Your Submission' : 'Submit Assignment'}
          </h2>

          {submission ? (
            <div>
              <div className="mb-4">
                <span className="font-semibold">Submission Status:</span>
                <span className="ml-2">{submission.status}</span>
              </div>

              <div className="mb-4">
                <span className="font-semibold">Submitted At:</span>
                <span className="ml-2">{new Date(submission.submitted_at).toLocaleString()}</span>
              </div>

              {submission.is_late && (
                <div className="mb-4 text-red-500">
                  This submission was late.
                </div>
              )}

              {submission.submission_text && (
                <div className="mb-4">
                  <h3 className="font-bold mb-2">Text Submission:</h3>
                  <div className="p-4 border border-gray-200 rounded bg-gray-50">
                    {submission.submission_text}
                  </div>
                </div>
              )}

              {submission.submission_files && submission.submission_files.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-bold mb-2">Submitted Files:</h3>
                  <ul>
                    {submission.submission_files.map((file, index) => (
                      <li key={index} className="mb-1">
                        <a
                          href={file.file_url}
                          className="text-blue-500 hover:underline"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {file.file_name}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {submission.grade && (
                <div className="mt-6 p-4 border border-green-200 rounded bg-green-50">
                  <h3 className="font-bold mb-2">Grade:</h3>
                  <div className="mb-2">
                    <span className="font-semibold">Score:</span>
                    <span className="ml-2">
                      {submission.grade.score} / {assignment.points_possible}
                    </span>
                  </div>

                  {submission.grade.feedback && (
                    <div>
                      <h4 className="font-semibold mb-1">Feedback:</h4>
                      <p>{submission.grade.feedback}</p>
                    </div>
                  )}
                </div>
              )}

              {submission.status !== 'graded' && (
                <div className="mt-4">
                  <button
                    onClick={() => setSubmission(null)}
                    className="btn btn-primary"
                  >
                    Resubmit
                  </button>
                </div>
              )}
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="submission-text" className="block font-semibold mb-2">
                  Text Submission:
                </label>
                <textarea
                  id="submission-text"
                  value={submissionText}
                  onChange={(e) => setSubmissionText(e.target.value)}
                  className="form-input h-40"
                  placeholder="Enter your submission text here..."
                />
              </div>

              <div className="mb-6">
                <label htmlFor="file-upload" className="block font-semibold mb-2">
                  File Upload:
                </label>
                <input
                  type="file"
                  id="file-upload"
                  onChange={handleFileChange}
                  className="form-input"
                />
                <p className="text-gray-500 text-sm mt-1">
                  {selectedFile ? `Selected: ${selectedFile.name}` : 'No file selected'}
                </p>
              </div>

              <button
                type="submit"
                disabled={submitting || (!submissionText && !selectedFile)}
                className="btn btn-primary"
              >
                {submitting ? 'Submitting...' : 'Submit Assignment'}
              </button>

              {isPastDue && (
                <p className="text-red-500 mt-2">
                  Note: This assignment is past due. Late penalties may apply.
                </p>
              )}
            </form>
          )}
        </div>
      )}
    </div>
  );
}

export default AssignmentDetail;