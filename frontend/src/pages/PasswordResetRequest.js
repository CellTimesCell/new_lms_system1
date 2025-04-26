// frontend/src/pages/PasswordResetRequest.js
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

function PasswordResetRequest() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Send password reset request
      await api.requestPasswordReset(email);

      // Show success message
      setSuccess(true);
      setError('');

      // Clear form
      setEmail('');
    } catch (err) {
      setError('Failed to send password reset email. Please try again.');
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
          <p>Password reset instructions have been sent to your email address.</p>
          <p className="mt-2">Please check your inbox and follow the instructions to reset your password.</p>
          <p className="mt-2">
            <Link to="/login" className="text-blue-500 hover:underline">
              Return to Login
            </Link>
          </p>
        </div>
      ) : (
        <div className="card">
          <p className="mb-4">
            Enter your email address below and we'll send you instructions to reset your password.
          </p>

          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label htmlFor="email" className="block font-semibold mb-2">
                Email Address:
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Sending...' : 'Send Reset Instructions'}
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

export default PasswordResetRequest;