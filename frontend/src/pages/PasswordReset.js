// frontend/src/pages/PasswordReset.js
import React, { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import api from '../services/api';

function PasswordReset() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate passwords
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      // Send password reset request
      await api.resetPassword(token, password);

      // Show success message
      setSuccess(true);
      setError('');

      // Clear form
      setPassword('');
      setConfirmPassword('');

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError('Failed to reset password. The token may be invalid or expired.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <h1 className="text-3xl font-bold mb-6">Reset Password</h1>

      {error && (
        <div className="alert alert-error mb-6">
          <p>{error}</p>
        </div>
      )}

      {success ? (
        <div className="alert alert-success mb-6">
          <p>Your password has been reset successfully!</p>
          <p className="mt-2">You will be redirected to the login page shortly.</p>
          <p className="mt-2">
            <Link to="/login" className="text-blue-500 hover:underline">
              Click here if you are not redirected automatically
            </Link>
          </p>
        </div>
      ) : (
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="password" className="block font-semibold mb-2">
                New Password:
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="form-input"
                required
                minLength={8}
              />
            </div>

            <div className="mb-6">
              <label htmlFor="confirmPassword" className="block font-semibold mb-2">
                Confirm Password:
              </label>
              <input
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="form-input"
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        </div>
      )}

      <div className="text-center mt-4">
        <Link to="/login" className="text-blue-500 hover:underline">
          Back to Login
        </Link>
      </div>
    </div>
  );
}

export default PasswordReset;