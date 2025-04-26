import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Layout components
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

// Public pages
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';

// Protected pages
import Dashboard from './pages/Dashboard';
import UserProfile from './pages/UserProfile';
import CourseList from './pages/CourseList';
import CourseDetail from './pages/CourseDetail';
import ModuleDetail from './pages/ModuleDetail';
import AssignmentDetail from './pages/AssignmentDetail';
import SubmissionsList from './pages/SubmissionsList';
import SubmissionGrading from './pages/SubmissionGrading';

// Admin pages
import AdminDashboard from './pages/AdminDashboard';
import UserList from './pages/admin/UserList';
import UserEdit from './pages/admin/UserEdit';
import AdminCourseList from './pages/admin/AdminCourseList';
import SystemSettings from './pages/admin/SystemSettings';
import ActivityLog from './pages/admin/ActivityLog';

// Instructor pages
import CourseCreator from './pages/instructor/CourseCreator';
import ModuleCreator from './pages/instructor/ModuleCreator';
import AssignmentCreator from './pages/instructor/AssignmentCreator';

// Protected route component
import ProtectedRoute from './components/auth/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-8">
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected routes for all authenticated users */}
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } />

              <Route path="/profile" element={
                <ProtectedRoute>
                  <UserProfile />
                </ProtectedRoute>
              } />

              <Route path="/courses" element={
                <ProtectedRoute>
                  <CourseList />
                </ProtectedRoute>
              } />

              <Route path="/courses/:courseId" element={
                <ProtectedRoute>
                  <CourseDetail />
                </ProtectedRoute>
              } />

              <Route path="/modules/:moduleId" element={
                <ProtectedRoute>
                  <ModuleDetail />
                </ProtectedRoute>
              } />

              <Route path="/assignments/:assignmentId" element={
                <ProtectedRoute>
                  <AssignmentDetail />
                </ProtectedRoute>
              } />

              {/* Instructor and admin routes */}
              <Route path="/assignments/:assignmentId/submissions" element={
                <ProtectedRoute requiredRoles={['admin', 'instructor']}>
                  <SubmissionsList />
                </ProtectedRoute>
              } />

              <Route path="/submissions/:submissionId" element={
                <ProtectedRoute requiredRoles={['admin', 'instructor']}>
                  <SubmissionGrading />
                </ProtectedRoute>
              } />

              <Route path="/courses/create" element={
                <ProtectedRoute requiredRoles={['admin', 'instructor']}>
                  <CourseCreator />
                </ProtectedRoute>
              } />

              <Route path="/courses/:courseId/modules/create" element={
                <ProtectedRoute requiredRoles={['admin', 'instructor']}>
                  <ModuleCreator />
                </ProtectedRoute>
              } />

              <Route path="/courses/:courseId/assignments/create" element={
                <ProtectedRoute requiredRoles={['admin', 'instructor']}>
                  <AssignmentCreator />
                </ProtectedRoute>
              } />

              {/* Admin routes */}
              <Route path="/admin" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <AdminDashboard />
                </ProtectedRoute>
              } />

              <Route path="/admin/users" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <UserList />
                </ProtectedRoute>
              } />

              <Route path="/admin/users/:userId" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <UserEdit />
                </ProtectedRoute>
              } />

              <Route path="/admin/courses" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <AdminCourseList />
                </ProtectedRoute>
              } />

              <Route path="/admin/settings" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <SystemSettings />
                </ProtectedRoute>
              } />

              <Route path="/admin/activity" element={
                <ProtectedRoute requiredRoles={['admin']}>
                  <ActivityLog />
                </ProtectedRoute>
              } />
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;