// frontend/src/pages/SubmissionGrading.js
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function SubmissionGrading() {
  const { submissionId } = useParams();
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [submission, setSubmission] = useState(null);
  const [assignment, setAssignment] = useState(null);
  const [student, setStudent] = useState(null);
  const [score, setScore] = useState('');
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        // Get submission details
        const submissionData = await api.getSubmissionDetail(submissionId);
        setSubmission(submissionData);

        if (submissionData.grade) {
          setScore(submissionData.grade.score);
          setFeedback(submissionData.grade.feedback || '');
        }

        // Get assignment details
        if (submissionData.assignment_id) {
          const assignmentData = await api.getAssignmentById(submissionData.assignment_id);
          setAssignment(assignmentData);
        }

        // Get student details
        if (submissionData.student_id) {
          const studentData = await api.getUserById(submissionData.student_id);
          setStudent(studentData);
        }
      } catch (err) {
        setError('Failed to load submission details');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [submissionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!score) {
      setError('Please provide a score');
      return;
    }

    // Validate score is a number and within range
    const scoreNum = parseFloat(score);
    if (isNaN(scoreNum)) {
      setError('Score must be a number');
      return;
    }

    if (assignment && (scoreNum < 0 || scoreNum > assignment.points_possible)) {
      setError(`Score must be between 0 and ${assignment.points_possible}`);
      return;
    }

    setSubmitting(true);

    try {
      // Submit grade
      const gradeData = {
        score: scoreNum,
        feedback: feedback
      };

      const response = await api.gradeSubmission(submissionId, gradeData);

      // Update submission with new grade
      setSubmission({
        ...submission,
        grade: response,
        status: 'graded'
      });

      // Show success message
      alert('Submission graded successfully!');

      // Navigate back to submissions list
      if (assignment) {
        navigate(`/assignments/${assignment.id}/submissions`);
      }
    } catch (err) {
      setError('Failed to submit grade');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading submission details...</p>
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

  if (!submission || !assignment) {
    return (
      <div className="text-center py-10">
        <p className="text-xl">Submission not found</p>
        <p className="mt-2">
          <Link to="/dashboard" className="btn btn-primary">Return to Dashboard</Link>
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link
          to={`/assignments/${assignment.id}/submissions`}
          className="btn btn-secondary"
        >
          Back to Submissions
        </Link>
      </div>

      <div className="card mb-8">
        <h1 className="text-3xl font-bold mb-4">Grade Submission</h1>

        <div className="mb-4">
          <span className="font-semibold">Assignment:</span>
          <span className="ml-2">{assignment.title}</span>
        </div>

        <div className="mb-4">
          <span className="font-semibold">Student:</span>
          <span className="ml-2">{student ? `${student.first_name} ${student.last_name}` : submission.student_name}</span>
        </div>

        <div className="mb-4">
          <span className="font-semibold">Submitted:</span>
          <span className="ml-2">{new Date(submission.submitted_at).toLocaleString()}</span>
          {submission.is_late && (
            <span className="ml-2 text-red-500">(Late)</span>
          )}
        </div>
      </div>

      <div className="card mb-8">
        <h2 className="text-xl font-bold mb-4">Submission Content</h2>

        {submission.submission_text && (
          <div className="mb-6">
            <h3 className="font-bold mb-2">Text Submission:</h3>
            <div className="p-4 border border-gray-200 rounded bg-gray-50">
              {submission.submission_text}
            </div>
          </div>
        )}

        {submission.submission_files && submission.submission_files.length > 0 && (
          <div>
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
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">Grade Submission</h2>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="score" className="block font-semibold mb-2">
              Score (out of {assignment.points_possible}):
            </label>
            <input
              type="number"
              id="score"
              value={score}
              onChange={(e) => setScore(e.target.value)}
              className="form-input w-24"
              min="0"
              max={assignment.points_possible}
              step="0.1"
              required
            />
          </div>

          <div className="mb-6">
            <label htmlFor="feedback" className="block font-semibold mb-2">
              Feedback:
            </label>
            <textarea
              id="feedback"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="form-input h-40"
              placeholder="Provide feedback to the student..."
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="btn btn-primary"
          >
            {submitting ? 'Submitting...' : (submission.grade ? 'Update Grade' : 'Submit Grade')}
          </button>
        </form>
      </div>
    </div>
  );
}

export default SubmissionGrading;