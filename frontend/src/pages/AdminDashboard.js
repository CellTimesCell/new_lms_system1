// frontend/src/pages/AdminDashboard.js
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

function AdminDashboard() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    users: 0,
    courses: 0,
    activeEnrollments: 0,
    recentActivity: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if user is admin
    if (!currentUser || !currentUser.roles.includes('admin')) {
      navigate('/dashboard');
      return;
    }

    async function fetchAdminData() {
      try {
        // In a real app, you'd fetch actual stats from an API
        // For now, we'll use simulated data

        // Get users count
        const users = await api.getUsers();

        // Get courses count
        const courses = await api.getCourses();

        // Simulated recent activity
        const recentActivity = [
          {
            id: 1,
            user: 'student1',
            action: 'Submitted assignment',
            resource: 'Assignment 1',
            timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30 minutes ago
          },
          {
            id: 2,
            user: 'teacher',
            action: 'Created course',
            resource: 'Introduction to Biology',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString() // 2 hours ago
          },
          {
            id: 3,
            user: 'student2',
            action: 'Enrolled in course',
            resource: 'Algebra 101',
            timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString() // 5 hours ago
          }
        ];

        setStats({
          users: users.length,
          courses: courses.length,
          activeEnrollments: 25, // Simulated value
          recentActivity
        });
      } catch (err) {
        setError('Failed to load admin dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchAdminData();
  }, [currentUser, navigate]);

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="spinner"></div>
        <p>Loading admin dashboard...</p>
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

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Admin Dashboard</h1>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card p-6">
          <h3 className="text-xl font-bold mb-2">Users</h3>
          <p className="text-3xl">{stats.users}</p>
          <Link to="/admin/users" className="text-blue-500 hover:underline mt-2 block">
            Manage Users
          </Link>
        </div>

        <div className="card p-6">
          <h3 className="text-xl font-bold mb-2">Courses</h3>
          <p className="text-3xl">{stats.courses}</p>
          <Link to="/admin/courses" className="text-blue-500 hover:underline mt-2 block">
            Manage Courses
          </Link>
        </div>

        <div className="card p-6">
          <h3 className="text-xl font-bold mb-2">Active Enrollments</h3>
          <p className="text-3xl">{stats.activeEnrollments}</p>
          <Link to="/admin/enrollments" className="text-blue-500 hover:underline mt-2 block">
            View Details
          </Link>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card mb-8">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/admin/users/create" className="card p-4 hover:bg-gray-50">
            <h3 className="font-bold mb-2">Create User</h3>
            <p className="text-gray-600">Add a new user to the system</p>
          </Link>

          <Link to="/admin/courses/create" className="card p-4 hover:bg-gray-50">
            <h3 className="font-bold mb-2">Create Course</h3>
            <p className="text-gray-600">Add a new course to the catalog</p>
          </Link>

          <Link to="/admin/reports" className="card p-4 hover:bg-gray-50">
            <h3 className="font-bold mb-2">View Reports</h3>
            <p className="text-gray-600">Access system analytics</p>
          </Link>

          <Link to="/admin/settings" className="card p-4 hover:bg-gray-50">
            <h3 className="font-bold mb-2">System Settings</h3>
            <p className="text-gray-600">Configure system parameters</p>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>

        {stats.recentActivity.length === 0 ? (
          <p>No recent activity</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100">
                  <th className="p-2 text-left">User</th>
                  <th className="p-2 text-left">Action</th>
                  <th className="p-2 text-left">Resource</th>
                  <th className="p-2 text-left">Time</th>
                </tr>
              </thead>
              <tbody>
                {stats.recentActivity.map(activity => (
                  <tr key={activity.id} className="border-b">
                    <td className="p-2">{activity.user}</td>
                    <td className="p-2">{activity.action}</td>
                    <td className="p-2">{activity.resource}</td>
                    <td className="p-2">{new Date(activity.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4">
          <Link to="/admin/activity" className="text-blue-500 hover:underline">
            View All Activity
          </Link>
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;