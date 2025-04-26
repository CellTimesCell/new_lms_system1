import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

function AdminDashboard({ profile }) {
  const [stats, setStats] = useState({
    users: 0,
    courses: 0,
    activeEnrollments: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchStats() {
      try {
        // In a real app, you'd fetch actual stats from an API
        // For now, we'll use dummy data

        // Get courses for counting
        const courses = await api.getCourses();

        setStats({
          users: 10, // Dummy value
          courses: courses.length,
          activeEnrollments: 25 // Dummy value
        });
      } catch (err) {
        setError('Failed to load dashboard statistics');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  if (loading) {
    return <div className="spinner"></div>;
  }

  return (
    <div>
      <section className="mb-10">
        <h2 className="text-2xl font-bold mb-6">System Overview</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2 text-blue-600">Total Users</h3>
            <p className="text-3xl font-bold">{stats.users}</p>
            <Link to="/admin/users" className="text-blue-500 hover:text-blue-700 text-sm">
              Manage Users &rarr;
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2 text-green-600">Active Courses</h3>
            <p className="text-3xl font-bold">{stats.courses}</p>
            <Link to="/admin/courses" className="text-green-500 hover:text-green-700 text-sm">
              Manage Courses &rarr;
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-2 text-purple-600">Active Enrollments</h3>
            <p className="text-3xl font-bold">{stats.activeEnrollments}</p>
            <Link to="/admin/enrollments" className="text-purple-500 hover:text-purple-700 text-sm">
              View Details &rarr;
            </Link>
          </div>
        </div>
      </section>

      <section className="mb-10">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Quick Actions</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/admin/users/create"
            className="bg-white rounded-lg shadow-md p-6 hover:bg-blue-50"
          >
            <h3 className="text-lg font-semibold mb-2">Create User</h3>
            <p className="text-gray-600">Add a new user to the system</p>
          </Link>

          <Link
            to="/admin/courses/create"
            className="bg-white rounded-lg shadow-md p-6 hover:bg-blue-50"
          >
            <h3 className="text-lg font-semibold mb-2">Create Course</h3>
            <p className="text-gray-600">Add a new course to the catalog</p>
          </Link>

          <Link
            to="/admin/reports"
            className="bg-white rounded-lg shadow-md p-6 hover:bg-blue-50"
          >
            <h3 className="text-lg font-semibold mb-2">Generate Reports</h3>
            <p className="text-gray-600">Access system activity reports</p>
          </Link>

          <Link
            to="/admin/settings"
            className="bg-white rounded-lg shadow-md p-6 hover:bg-blue-50"
          >
            <h3 className="text-lg font-semibold mb-2">System Settings</h3>
            <p className="text-gray-600">Configure system parameters</p>
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-6">Recent Activity</h2>

        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-gray-500">System activity log will be displayed here.</p>
        </div>
      </section>
    </div>
  );
}

export default AdminDashboard;