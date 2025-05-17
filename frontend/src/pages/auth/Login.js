import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import Alert from '../../components/ui/Alert';

const Login = () => {
  const { login } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Get the redirect path or default to dashboard
  const from = location.state?.from?.pathname || '/';

  // Form validation schema
  const validationSchema = Yup.object({
    username: Yup.string().required(t('validation.usernameRequired')),
    password: Yup.string().required(t('validation.passwordRequired'))
  });

  const handleSubmit = async (values) => {
    try {
      setError('');
      setIsLoading(true);

      const success = await login(values.username, values.password);

      if (success) {
        navigate(from, { replace: true });
      } else {
        setError(t('login.invalidCredentials'));
      }
    } catch (err) {
      setError(err.message || t('login.error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 text-center mb-6">
        {t('login.title')}
      </h2>

      {error && <Alert type="error" message={error} className="mb-4" />}

      <Formik
        initialValues={{ username: '', password: '' }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, isValid }) => (
          <Form className="space-y-6">
            <div>
              <label htmlFor="username" className="form-label">
                {t('login.username')}
              </label>
              <Field
                type="text"
                id="username"
                name="username"
                className="form-input"
                placeholder={t('login.usernamePlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="username"
                component="div"
                className="mt-1 text-sm text-red-600"
              />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="form-label">
                  {t('login.password')}
                </label>
                <Link
                  to="/forgot-password"
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  {t('login.forgotPassword')}
                </Link>
              </div>
              <Field
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder={t('login.passwordPlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="password"
                component="div"
                className="mt-1 text-sm text-red-600"
              />
            </div>

            <div>
              <button
                type="submit"
                className="btn btn-primary w-full"
                disabled={isLoading || !isValid}
              >
                {isLoading ? t('common.loading') : t('login.signIn')}
              </button>
            </div>

            <div className="text-center mt-4">
              <span className="text-sm text-gray-600">
                {t('login.noAccount')}{' '}
              </span>
              <Link
                to="/register"
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                {t('login.signUp')}
              </Link>
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
};

export default Login;