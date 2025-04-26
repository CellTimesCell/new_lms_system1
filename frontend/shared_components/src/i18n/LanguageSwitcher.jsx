// Language Switcher Component
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Select, Tooltip } from 'antd';
import { GlobalOutlined } from '@ant-design/icons';

const { Option } = Select;

/**
 * LanguageSwitcher Component
 *
 * Allows users to change the application language
 */
const LanguageSwitcher = ({ placement = 'bottomRight' }) => {
  const { t, i18n } = useTranslation();

  // Available languages
  const languages = [
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Español' }
  ];

  // Handle language change
  const handleChange = (langCode) => {
    i18n.changeLanguage(langCode);

    // Store language preference
    localStorage.setItem('preferredLanguage', langCode);

    // Update HTML lang attribute
    document.documentElement.setAttribute('lang', langCode);
  };

  return (
    <div className="language-switcher">
      <Tooltip title={t('settings.changeLanguage')} placement={placement}>
        <Select
          defaultValue={i18n.language}
          onChange={handleChange}
          dropdownMatchSelectWidth={false}
          aria-label={t('accessibility.selectLanguage')}
        >
          {languages.map(lang => (
            <Option key={lang.code} value={lang.code}>
              <div className="language-option">
                <GlobalOutlined className="language-icon" />
                <span className="language-name">{t(`languages.${lang.code}`)}</span>
              </div>
            </Option>
          ))}
        </Select>
      </Tooltip>
    </div>
  );
};

export default LanguageSwitcher;