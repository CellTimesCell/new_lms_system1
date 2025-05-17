import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import UserMenu from './UserMenu';
import NotificationsMenu from './NotificationsMenu';
import LanguageSwitcher from '../ui/LanguageSwitcher';
import { HiMenu } from 'react-icons/hi';

const Header = ({ toggleSidebar }) => {
  const { currentUser } = useAuth();
  const { t } = useTranslation();

  return (
    <header className="bg-white shadow-sm z-10">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side - Menu button and logo */}
          <div className="flex items-center">
            <button
              type="button"
              className="md:hidden inline-flex items-center justify-center p-2 rounded-md text-gray-500 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
              onClick={toggleSidebar}
            >
              <span className="sr-only">{t('header.openSidebar')}</span>
              <HiMenu className="block h-6 w-6" aria-hidden="true" />
            </button>

            <Link to="/" className="flex-shrink-0 flex items-center ml-4 md:ml-0">
              <img
                className="block h-8 w-auto"
                src="/logo.svg"
                alt="LMS Logo"
              />
              <span className="ml-2 text-xl font-bold text-gray-900 hidden sm:block">
                {t('lms.name')}
              </span>
            </Link>
          </div>

          {/* Right side - User and notification menus */}
          <div className="flex items-center space-x-4">
            <div className="hidden md:block">
              <LanguageSwitcher />
            </div>

            <NotificationsMenu />

            <UserMenu user={currentUser} />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;