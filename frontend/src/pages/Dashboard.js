import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

// Different dashboard components
import StudentDashboard from '../components/dashboard/StudentDashboard';
import InstructorDashboard from '../components/dashboard/InstructorDashboard';
import AdminDashboard from '../components/dashboard/AdminDashboard';

function Dashboard() {
  const { currentUser } = useAuth();
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchUserProfile() {
      try {
        const profile = await api.getUserProfile();
        setUserProfile(profile);
      } catch (err) {
        setError('Failed to load user profile');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchUserProfile();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <p>{error}</p>
        <p className="mt-2">
          <Link to="/" className="text-red-700 font-bold">Return home</Link>
        </p>
      </div>
    );
  }

  // Determine which dashboard to show based on user role
  const getDashboardComponent = () => {
    if (currentUser.roles.includes('admin')) {
      return <AdminDashboard profile={userProfile} />;
    } else if (currentUser.roles.includes('instructor')) {
      return <InstructorDashboard profile={userProfile} />;
    } else {
      return <StudentDashboard profile={userProfile} />;
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Welcome, {userProfile?.first_name || currentUser.username}!</h1>

      {getDashboardComponent()}
    </div>
  );
}

export default Dashboard;