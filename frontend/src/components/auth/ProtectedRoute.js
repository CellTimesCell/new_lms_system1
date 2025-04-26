import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

function ProtectedRoute({ children, requiredRoles = [] }) {
  const { currentUser } = useAuth();

  // Check if user is logged in
  if (!currentUser) {
    return <Navigate to="/login" />;
  }

  // Check if user has required roles (if specified)
  if (requiredRoles.length > 0) {
    const hasRequiredRole = currentUser.roles.some(role =>
      requiredRoles.includes(role)
    );

    if (!hasRequiredRole) {
      return <Navigate to="/dashboard" />;
    }
  }

  return children;
}

export default ProtectedRoute;