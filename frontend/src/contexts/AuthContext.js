import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      setCurrentUser(JSON.parse(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    setLoading(false);
  }, []);

  // Login function
 const login = async (username, password) => {
  try {
    // Add debug console logs
    console.log('Attempting login for:', username);

    const response = await axios.post('/api/v1/auth/token',
      new URLSearchParams({
        'username': username,
        'password': password
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    console.log('Login response:', response.data);

    const { access_token, user_id, username: user_name, roles } = response.data;

    const userData = {
      id: user_id,
      username: user_name,
      roles: roles || [] // Default to empty array if roles is undefined
    };

    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));

    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

    setCurrentUser(userData);
    setError('');

    return userData;
  } catch (err) {
    console.error('Login error:', err);
    // More detailed error handling
    if (err.response) {
      console.error('Error response:', err.response.data);
      setError(`Login failed: ${err.response.data.detail || 'Please check your credentials'}`);
    } else if (err.request) {
      console.error('No response received');
      setError('Server not responding. Please try again later.');
    } else {
      console.error('Error setting up request:', err.message);
      setError('An error occurred during login. Please try again.');
    }
    throw err;
  }
};}