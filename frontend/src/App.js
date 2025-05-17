import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';

// Layouts
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Auth Pages
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import VerifyEmail from './pages/auth/VerifyEmail';

// Dashboard Pages
import AdminDashboard from './pages/dashboard/AdminDashboard';
import InstructorDashboard from './pages/dashboard/InstructorDashboard';
import StudentDashboard from './pages/dashboard/StudentDashboard';

// Course Pages
import CoursesList from './pages/courses/CoursesList';
import CourseDetail from './pages/courses/CourseDetail';
import CourseCreate from './pages/courses/CourseCreate';
import CourseEdit from './pages/courses/CourseEdit';

// Assignment Pages
import AssignmentDetail from './pages/assignments/AssignmentDetail';
import AssignmentCreate from './pages/assignments/AssignmentCreate';
import AssignmentSubmit from './pages/assignments/AssignmentSubmit';
import GradeAssignments from './pages/assignments/GradeAssignments';

// User Management Pages
import UserProfile from './pages/users/UserProfile';
import UsersList from './pages/users/UsersList';

// Not Found
import NotFound from './pages/NotFound';

// Protected Route Component
const ProtectedRoute = ({ children, roles = [] }) => {
  const { currentUser, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (!currentUser) {
    return <Navigate to="/login" />;
  }

  if (roles.length > 0 && !roles.some(role => currentUser.roles.includes(role))) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

function App() {
  const { currentUser } = useAuth();

  // Determine the dashboard route based on user role
  const getDashboardRoute = () => {
    if (!currentUser) return "/login";

    if (currentUser.roles.includes('admin')) {
      return "/admin/dashboard";
    } else if (currentUser.roles.includes('instructor')) {
      return "/instructor/dashboard";
    } else {
      return "/student/dashboard";
    }
  };

  return (
    <Routes>
      {/* Auth Routes */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route path="/verify-email/:token" element={<VerifyEmail />} />
      </Route>

      {/* Main App Routes */}
      <Route element={<MainLayout />}>
        {/* Redirect to appropriate dashboard */}
        <Route path="/" element={<Navigate to={getDashboardRoute()} />} />

        {/* Dashboard Routes */}
        <Route path="/admin/dashboard" element={
          <ProtectedRoute roles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } />

        <Route path="/instructor/dashboard" element={
          <ProtectedRoute roles={['instructor']}>
            <InstructorDashboard />
          </ProtectedRoute>
        } />

        <Route path="/student/dashboard" element={
          <ProtectedRoute roles={['student']}>
            <StudentDashboard />
          </ProtectedRoute>
        } />

        {/* Course Routes */}
        <Route path="/courses" element={
          <ProtectedRoute>
            <CoursesList />
          </ProtectedRoute>
        } />

        <Route path="/courses/:id" element={
          <ProtectedRoute>
            <CourseDetail />
          </ProtectedRoute>
        } />

        <Route path="/courses/create" element={
          <ProtectedRoute roles={['admin', 'instructor']}>
            <CourseCreate />
          </ProtectedRoute>
        } />

        <Route path="/courses/:id/edit" element={
          <ProtectedRoute roles={['admin', 'instructor']}>
            <CourseEdit />
          </ProtectedRoute>
        } />

        {/* Assignment Routes */}
        <Route path="/assignments/:id" element={
          <ProtectedRoute>
            <AssignmentDetail />
          </ProtectedRoute>
        } />

        <Route path="/courses/:courseId/assignments/create" element={
          <ProtectedRoute roles={['admin', 'instructor']}>
            <AssignmentCreate />
          </ProtectedRoute>
        } />

        <Route path="/assignments/:id/submit" element={
          <ProtectedRoute roles={['student']}>
            <AssignmentSubmit />
          </ProtectedRoute>
        } />

        <Route path="/assignments/:id/grade" element={
          <ProtectedRoute roles={['admin', 'instructor']}>
            <GradeAssignments />
          </ProtectedRoute>
        } />

        {/* User Routes */}
        <Route path="/profile" element={
          <ProtectedRoute>
            <UserProfile />
          </ProtectedRoute>
        } />

        <Route path="/admin/users" element={
          <ProtectedRoute roles={['admin']}>
            <UsersList />
          </ProtectedRoute>
        } />
      </Route>

      {/* Not Found */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;