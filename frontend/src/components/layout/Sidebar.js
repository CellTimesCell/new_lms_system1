import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import {
  HiHome,
  HiAcademicCap,
  HiClipboardList,
  HiUsers,
  HiCog,
  HiChartBar,
  HiFolder,
  HiChatAlt
} from 'react-icons/hi';

const Sidebar = () => {
  const { currentUser } = useAuth();
  const { t } = useTranslation();

  // Define navigation items based on user role
  const isAdmin = currentUser?.roles.includes('admin');
  const isInstructor = currentUser?.roles.includes('instructor');
  const isStudent = currentUser?.roles.includes('student');

  // Define navigation items
  const navigationItems = [
    // Dashboard - Different based on role
    {
      name: t('sidebar.dashboard'),
      icon: HiHome,
      to: isAdmin ? '/admin/dashboard' : isInstructor ? '/instructor/dashboard' : '/student/dashboard',
      roles: ['admin', 'instructor', 'student']
    },
    // Courses
    {
      name: t('sidebar.courses'),
      icon: HiAcademicCap,
      to: '/courses',
      roles: ['admin', 'instructor', 'student']
    },
    // Assignments
    {
      name: t('sidebar.assignments'),
      icon: HiClipboardList,
      to: isInstructor ? '/instructor/assignments' : '/student/assignments',
      roles: ['instructor', 'student']
    },
    // Analytics
    {
      name: t('sidebar.analytics'),
      icon: HiChartBar,
      to: '/analytics',
      roles: ['admin', 'instructor']
    },
    // Files
    {
      name: t('sidebar.files'),
      icon: HiFolder,
      to: '/files',
      roles: ['admin', 'instructor', 'student']
    },
    // Messages
    {
      name: t('sidebar.messages'),
      icon: HiChatAlt,
      to: '/messages',
      roles: ['admin', 'instructor', 'student']
    },
    // User Management (Admin only)
    {
      name: t('sidebar.users'),
      icon: HiUsers,
      to: '/admin/users',
      roles: ['admin']
    },
    // Settings
    {
      name: t('sidebar.settings'),
      icon: HiCog,
      to: '/settings',
      roles: ['admin', 'instructor', 'student']
    }
  ];

  // Filter navigation items based on user role
  const filteredItems = navigationItems.filter(item =>
    item.roles.some(role => currentUser?.roles.includes(role))
  );

  return (
    <div className="h-full flex flex-col bg-white border-r">
      <div className="flex-shrink-0 px-4 py-4 flex items-center justify-center">
        <img
          className="h-12 w-auto"
          src="/logo.svg"
          alt="LMS Logo"
        />
        <span className="ml-2 text-lg font-bold text-gray-900">
          {t('lms.name')}
        </span>
      </div>

      <div className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {filteredItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.to}
            className={({ isActive }) => `
              flex items-center px-4 py-2 text-sm font-medium rounded-md
              ${isActive
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }
            `}
          >
            <item.icon className="mr-3 h-5 w-5" aria-hidden="true" />
            {item.name}
          </NavLink>
        ))}
      </div>

      <div className="flex-shrink-0 px-4 py-4 border-t">
        <div className="flex items-center">
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">
              {currentUser?.firstName} {currentUser?.lastName}
            </p>
            <p className="text-xs text-gray-500">
              {currentUser?.roles.map(role => t(`roles.${role}`)).join(', ')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;