import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is logged in on initial load
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      const refreshToken = localStorage.getItem('refreshToken');

      if (token) {
        try {
          // Set the token in the auth service
          authService.setToken(token);

          // Get current user info
          const userInfo = await authService.getCurrentUser();
          setCurrentUser(userInfo);
        } catch (err) {
          // Token might be expired, try to refresh
          if (refreshToken) {
            try {
              const result = await authService.refreshToken(refreshToken);
              if (result.access_token) {
                localStorage.setItem('token', result.access_token);
                authService.setToken(result.access_token);

                const userInfo = await authService.getCurrentUser();
                setCurrentUser(userInfo);
              } else {
                // Refresh failed, log out
                logout();
              }
            } catch (refreshErr) {
              console.error('Error refreshing token:', refreshErr);
              logout();
            }
          } else {
            // No refresh token, log out
            logout();
          }
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setError(null);
      const result = await authService.login(username, password);

      if (result.access_token) {
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('refreshToken', result.refresh_token || '');

        // Set token in auth service
        authService.setToken(result.access_token);

        // Get user info from token response
        setCurrentUser({
          id: result.user_id,
          username: result.username,
          roles: result.roles,
          firstName: result.first_name,
          lastName: result.last_name,
          preferredLanguage: result.preferred_language || 'en'
        });

        return true;
      }
    } catch (err) {
      setError(err.message || 'Login failed');
      return false;
    }
  };

  const register = async (userData) => {
    try {
      setError(null);
      return await authService.register(userData);
    } catch (err) {
      setError(err.message || 'Registration failed');
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    authService.clearToken();
    setCurrentUser(null);
  };

  const forgotPassword = async (email) => {
    try {
      setError(null);
      return await authService.forgotPassword(email);
    } catch (err) {
      setError(err.message || 'Password reset request failed');
      return false;
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      setError(null);
      return await authService.resetPassword(token, newPassword);
    } catch (err) {
      setError(err.message || 'Password reset failed');
      return false;
    }
  };

  const verifyEmail = async (token) => {
    try {
      setError(null);
      return await authService.verifyEmail(token);
    } catch (err) {
      setError(err.message || 'Email verification failed');
      return false;
    }
  };

  const updateProfile = async (profileData) => {
    try {
      setError(null);
      const updatedUser = await authService.updateProfile(profileData);
      setCurrentUser(prev => ({ ...prev, ...updatedUser }));
      return true;
    } catch (err) {
      setError(err.message || 'Profile update failed');
      return false;
    }
  };

  const value = {
    currentUser,
    isLoading,
    error,
    login,
    register,
    logout,
    forgotPassword,
    resetPassword,
    verifyEmail,
    updateProfile
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};