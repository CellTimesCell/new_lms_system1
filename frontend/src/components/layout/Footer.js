import React from 'react';

function Footer() {
  return (
    <footer className="bg-gray-800 text-white py-6">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="mb-4 md:mb-0">
            <h3 className="text-xl font-bold">LMS System</h3>
            <p className="text-gray-400">Learning Management System</p>
          </div>

          <div className="text-center md:text-right">
            <p>&copy; {new Date().getFullYear()} LMS System. All rights reserved.</p>
            <p className="text-sm text-gray-400 mt-1">Created for educational purposes</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;