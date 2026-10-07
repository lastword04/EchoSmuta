import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';

import { Input } from '../../shared/ui/Input/Input';
import { useConfirmResetPasswordMutation } from '../../entities/auth/api/authApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './ConfirmResetPasswordPage.module.css';

  const ConfirmResetPasswordPageComponent = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [confirmResetPassword] = useConfirmResetPasswordMutation();
  
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [tokenError, setTokenError] = useState('');

  // Получаем токен из URL
  const token = searchParams.get('token');

  // Проверяем наличие токена при монтировании
  useEffect(() => {
    if (!token) {
      setTokenError('Отсутствует токен сброса пароля в URL');
    }
  }, [token]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.newPassword) {
      newErrors.newPassword = 'Введите новый пароль';
    } else if (formData.newPassword.length < 8) {
      newErrors.newPassword = 'Пароль должен содержать минимум 8 символов';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Подтвердите новый пароль';
    } else if (formData.newPassword !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Проверяем токен
    if (!token) {
      setTokenError('Отсутствует токен сброса пароля');
      return;
    }
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsLoading(true);
    setTokenError('');
    
    try {
      // Подготовка данных для отправки
      const confirmResetData = {
        token: token,
        new_password: formData.newPassword
      };
      
      // Отправка данных на сервер
     await confirmResetPassword(confirmResetData).unwrap();
      
      // Успешный сброс пароля
      setIsSuccess(true);
      setErrors({});
      
    } catch (error) {
      // Обработка ошибок от сервера
      if (error?.status) {
        const { status, data } = error;
        
        if (status === 404) {
          // Токен не найден или устарел
          setTokenError('Ваша ссылка устарела. Попробуйте сбросить пароль ещё раз.');
        } else if (status === 422) {
          // Ошибки валидации
          if (data.detail && data.detail.includes('password')) {
            setErrors({
              newPassword: 'Пароль не соответствует требованиям безопасности'
            });
          } else {
            setErrors({
              general: 'Ошибка валидации данных. Проверьте введённые данные.'
            });
          }
        } else {
          setErrors({
            general: 'Ошибка при сбросе пароля. Попробуйте позже.'
          });
        }
      } else {
        setErrors({
          general: 'Ошибка подключения к серверу. Проверьте соединение и попробуйте снова.'
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleResetPasswordAgain = () => {
    navigate('/reset-password');
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.content}>
        <Card className={styles.confirmResetCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Сброс пароля</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>

          {tokenError && (
            <div className={styles.tokenError}>
              {tokenError}
            </div>
          )}

          {errors.general && (
            <div className={styles.generalError}>
              {errors.general}
            </div>
          )}

          {isSuccess ? (
            <div className={styles.successSection}>
              <div className={styles.successIcon}>✅</div>
              <h2 className={styles.successTitle}>Пароль успешно изменён!</h2>
              <p className={styles.successMessage}>
                Ваш пароль был успешно сброшен. Теперь вы можете войти в игру под новым паролем.
              </p>
              <div className={styles.successActions}>
                <Button
                  variant="primary"
                  size="large"
                  onClick={handleBackToLogin}
                  className={styles.actionButton}
                >
                  Войти в аккаунт
                </Button>
                <Button
                  variant="outline"
                  size="large"
                  onClick={handleBackToHome}
                  className={styles.actionButton}
                >
                  На главную
                </Button>
              </div>
            </div>
          ) : token ? (
            <>
              <div className={styles.instruction}>
                <p>
                  Введите новый пароль для вашего аккаунта.
                </p>
              </div>

              <form onSubmit={handleSubmit} className={styles.form}>
                <Input
                  label="Новый пароль"
                  type="password"
                  name="newPassword"
                  placeholder="Минимум 8 символов"
                  value={formData.newPassword}
                  onChange={handleInputChange}
                  error={errors.newPassword}
                  autoComplete="new-password"
                />

                <Input
                  label="Подтвердите новый пароль"
                  type="password"
                  name="confirmPassword"
                  placeholder="Повторите новый пароль"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  error={errors.confirmPassword}
                  autoComplete="new-password"
                />

                <div className={styles.actions}>
                  <Button
                    type="submit"
                    variant="primary"
                    size="large"
                    disabled={isLoading}
                    className={styles.submitButton}
                  >
                    {isLoading ? 'Сброс...' : 'Сбросить пароль'}
                  </Button>
                </div>
              </form>

              <div className={styles.footer}>
                <Button
                  type="button"
                  variant="link"
                  onClick={handleBackToHome}
                  className={styles.backToHome}
                >
                  ← Вернуться на главную
                </Button>
              </div>
            </>
          ) : (
            <div className={styles.tokenMissing}>
              <div className={styles.errorIcon}>⚠️</div>
              <h2 className={styles.errorTitle}>Ошибка доступа</h2>
              <p className={styles.errorMessage}>
                Ссылка для сброса пароля некорректна или устарела.
              </p>
              <div className={styles.errorActions}>
                <Button
                  variant="primary"
                  size="medium"
                  onClick={handleResetPasswordAgain}
                  className={styles.actionButton}
                >
                  Сбросить пароль заново
                </Button>
                <Button
                  variant="outline"
                  size="medium"
                  onClick={handleBackToHome}
                  className={styles.actionButton}
                >
                  На главную
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

const ConfirmResetPasswordPage = withBaseMainPage(ConfirmResetPasswordPageComponent);

export { ConfirmResetPasswordPage };