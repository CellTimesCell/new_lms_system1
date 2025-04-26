// frontend/src/pages/UserProfile.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function UserProfile() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    preferred_language: 'en',
    bio: '',
    timezone: 'UTC'
  });
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!currentUser) {
      navigate('/login');
      return;
    }

    async function fetchProfile() {
      try {
        const profileData = await api.getUserProfile();
        setProfile(profileData);

        // Initialize form data
        setFormData({
          first_name: profileData.first_name || '',
          last_name: profileData.last_name || '',
          email: profileData.email || '',
          preferred_language: profileData.preferred_language || 'en',
          bio: profileData.profile?.bio || '',
          timezone: profileData.profile?.timezone || 'UTC'
        });
      } catch (err) {
        setError('Failed to load user profile');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, [currentUser, navigate]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUpdating(true);

    try {
      // Update user profile
      const userData = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        email: formData.email,
        preferred_language: formData.preferred_language
      };

      await api.updateUser(currentUser.id, userData);

      // Update profile details
      const profileData = {
        bio: formData.bio,
        timezone: formData.timezone
      };

      if (profile.profile) {
        await api.updateUserProfile(currentUser.id, profileData);
      } else {
        await api.createUserProfile(currentUser.id, profileData);
      }

      // Refresh profile data
      const updatedProfile = await api.getUserProfile();
      setProfile(updatedProfile);

      // Show success message
      alert('Profile updated successfully!');
    } catch (err) {
      setError('Failed to update profile');
      console.error(err);
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading profile...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">My Profile</h1>

      {error && (
        <div className="alert alert-error mb-6">
          <p>{error}</p>
          <button onClick={() => setError('')} className="btn btn-secondary mt-2">
            Dismiss
          </button>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block font-semibold mb-2">
              Username:
            </label>
            <input
              type="text"
              id="username"
              value={profile?.username || ''}
              className="form-input"
              disabled
            />
            <p className="text-gray-500 text-sm mt-1">Username cannot be changed</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="first_name" className="block font-semibold mb-2">
                First Name:
              </label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="form-input"
              />
            </div>

            <div>
              <label htmlFor="last_name" className="block font-semibold mb-2">
                Last Name:
              </label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="form-input"
              />
            </div>
          </div>

          <div className="mb-4">
            <label htmlFor="email" className="block font-semibold mb-2">
              Email:
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="preferred_language" className="block font-semibold mb-2">
              Preferred Language:
            </label>
            <select
              id="preferred_language"
              name="preferred_language"
              value={formData.preferred_language}
              onChange={handleChange}
              className="form-input"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
            </select>
          </div>

          <div className="mb-4">
            <label htmlFor="bio" className="block font-semibold mb-2">
              Bio:
            </label>
            <textarea
              id="bio"
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              className="form-input h-32"
              placeholder="Tell us about yourself..."
            />
          </div>

          <div className="mb-6">
            <label htmlFor="timezone" className="block font-semibold mb-2">
              Timezone:
            </label>
            <select
              id="timezone"
              name="timezone"
              value={formData.timezone}
              onChange={handleChange}
              className="form-input"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="America/Anchorage">Alaska Time (AKT)</option>
              <option value="America/Honolulu">Hawaii Time (HT)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={updating}
            className="btn btn-primary"
          >
            {updating ? 'Updating...' : 'Update Profile'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default UserProfile;