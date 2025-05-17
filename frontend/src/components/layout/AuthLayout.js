import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from '../components/ui/LanguageSwitcher';

const AuthLayout = () => {
  const { currentUser, isLoading } = useAuth();
  const { t } = useTranslation();

  // If user is already logged in, redirect to dashboard
  if (currentUser && !isLoading) {
    if (currentUser.roles.includes('admin')) {
      return <Navigate to="/admin/dashboard" />;
    } else if (currentUser.roles.includes('instructor')) {
      return <Navigate to="/instructor/dashboard" />;
    } else {
      return <Navigate to="/student/dashboard" />;
    }
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="w-full max-w-md mx-auto p-6">
        <div className="mt-7 bg-white rounded-xl shadow-lg">
          <div className="p-4 sm:p-7">
            <div className="absolute top-4 right-4">
              <LanguageSwitcher />
            </div>

            <div className="text-center mb-8">
              <h1 className="block text-2xl font-bold text-gray-800">{t('lms.title')}</h1>
              <p className="mt-2 text-sm text-gray-600">{t('lms.subtitle')}</p>
            </div>

            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;