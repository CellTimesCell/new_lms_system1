import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import Alert from '../../components/ui/Alert';

const Register = () => {
  const { register } = useAuth();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Form validation schema
  const validationSchema = Yup.object({
    username: Yup.string()
      .min(3, t('validation.usernameMinLength'))
      .max(20, t('validation.usernameMaxLength'))
      .matches(/^[a-zA-Z0-9_]+$/, t('validation.usernameFormat'))
      .required(t('validation.usernameRequired')),
    email: Yup.string()
      .email(t('validation.emailFormat'))
      .required(t('validation.emailRequired')),
    first_name: Yup.string()
      .required(t('validation.firstNameRequired')),
    last_name: Yup.string()
      .required(t('validation.lastNameRequired')),
    password: Yup.string()
      .min(8, t('validation.passwordMinLength'))
      .matches(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
        t('validation.passwordFormat')
      )
      .required(t('validation.passwordRequired')),
    confirmPassword: Yup.string()
      .oneOf([Yup.ref('password'), null], t('validation.passwordsMatch'))
      .required(t('validation.confirmPasswordRequired'))
  });

  const handleSubmit = async (values, { resetForm }) => {
    try {
      setError('');
      setSuccess('');
      setIsLoading(true);

      const { confirmPassword, ...registrationData } = values;

      // Add default roles
      registrationData.roles = ['student'];

      const result = await register(registrationData);

      if (result) {
        setSuccess(t('register.successMessage'));
        resetForm();
        // Redirect to login after a delay
        setTimeout(() => navigate('/login'), 3000);
      } else {
        setError(t('register.error'));
      }
    } catch (err) {
      setError(err.message || t('register.error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 text-center mb-6">
        {t('register.title')}
      </h2>

      {error && <Alert type="error" message={error} className="mb-4" />}
      {success && <Alert type="success" message={success} className="mb-4" />}

      <Formik
        initialValues={{
          username: '',
          email: '',
          first_name: '',
          last_name: '',
          password: '',
          confirmPassword: ''
        }}
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ isSubmitting, isValid }) => (
          <Form className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="form-label">
                  {t('register.firstName')}
                </label>
                <Field
                  type="text"
                  id="first_name"
                  name="first_name"
                  className="form-input"
                  placeholder={t('register.firstNamePlaceholder')}
                  disabled={isLoading}
                />
                <ErrorMessage
                  name="first_name"
                  component="div"
                  className="mt-1 text-sm text-red-600"
                />
              </div>

              <div>
                <label htmlFor="last_name" className="form-label">
                  {t('register.lastName')}
                </label>
                <Field
                  type="text"
                  id="last_name"
                  name="last_name"
                  className="form-input"
                  placeholder={t('register.lastNamePlaceholder')}
                  disabled={isLoading}
                />
                <ErrorMessage
                  name="last_name"
                  component="div"
                  className="mt-1 text-sm text-red-600"
                />
              </div>
            </div>

            <div>
              <label htmlFor="username" className="form-label">
                {t('register.username')}
              </label>
              <Field
                type="text"
                id="username"
                name="username"
                className="form-input"
                placeholder={t('register.usernamePlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="username"
                component="div"
                className="mt-1 text-sm text-red-600"
              />
            </div>

            <div>
              <label htmlFor="email" className="form-label">
                {t('register.email')}
              </label>
              <Field
                type="email"
                id="email"
                name="email"
                className="form-input"
                placeholder={t('register.emailPlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="email"
                component="div"
                className="mt-1 text-sm text-red-600"
              />
            </div>

            <div>
              <label htmlFor="password" className="form-label">
                {t('register.password')}
              </label>
              <Field
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder={t('register.passwordPlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="password"
                component="div"
                className="mt-1 text-sm text-red-600"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="form-label">
                {t('register.confirmPassword')}
              </label>
              <Field
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                className="form-input"
                placeholder={t('register.confirmPasswordPlaceholder')}
                disabled={isLoading}
              />
              <ErrorMessage
                name="confirmPassword"
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
                {isLoading ? t('common.loading') : t('register.signUp')}
              </button>
            </div>

            <div className="text-center mt-4">
              <span className="text-sm text-gray-600">
                {t('register.alreadyRegistered')}{' '}
              </span>
              <Link
                to="/login"
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                {t('register.signIn')}
              </Link>
            </div>
          </Form>
        )}
      </Formik>
    </div>
  );
};

export default Register;