import React from 'react';
import { useTranslation } from 'react-i18next';

const Footer = () => {
  const { t } = useTranslation();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t py-4">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between">
          <div className="text-sm text-gray-500">
            &copy; {currentYear} {t('footer.copyright')}
          </div>

          <div className="mt-3 sm:mt-0">
            <ul className="flex space-x-4 text-sm text-gray-500">
              <li>
                <a href="#" className="hover:text-gray-700">
                  {t('footer.privacy')}
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-gray-700">
                  {t('footer.terms')}
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-gray-700">
                  {t('footer.contact')}
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;