import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Home() {
  const { currentUser } = useAuth();

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
            Welcome to the Learning Management System
          </h1>
          <p className="mt-5 max-w-xl mx-auto text-xl text-gray-500">
            An innovative platform for online learning and teaching
          </p>

          <div className="mt-8">
            {currentUser ? (
              <Link
                to="/dashboard"
                className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300"
              >
                Go to Dashboard
              </Link>
            ) : (
              <div className="space-x-4">
                <Link
                  to="/login"
                  className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="inline-block bg-white hover:bg-gray-100 text-blue-600 font-bold py-3 px-6 rounded-lg border border-blue-600 transition duration-300"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>

        <div className="mt-16">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">For Students</h2>
              <p className="text-gray-600">
                Access course materials, submit assignments, and track your progress.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">For Instructors</h2>
              <p className="text-gray-600">
                Create and manage courses, grade assignments, and monitor student activity.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-xl font-bold text-gray-900 mb-4">For Administrators</h2>
              <p className="text-gray-600">
                Manage users, oversee course offerings, and analyze platform usage.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;