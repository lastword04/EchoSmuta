import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';

import { Input } from '../../shared/ui/Input/Input';
import { useResetPasswordMutation } from '../../entities/auth/api/authApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './ResetPasswordPage.module.css';

  const ResetPasswordPageComponent = () => {
  const navigate = useNavigate();
  const [resetPassword] = useResetPasswordMutation();
  
  const [formData, setFormData] = useState({
    email: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

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
    
    if (!formData.email.trim()) {
      newErrors.email = 'Введите email';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Неверный формат email';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Подготовка данных для отправки
      const resetData = {
        email: formData.email
      };
      
      // Отправка данных на сервер
      await resetPassword(resetData).unwrap();
      
      // Успешный запрос - показываем сообщение
      setIsSuccess(true);
      setErrors({});
      
    } catch (error) {
      // Обработка ошибок от сервера
      if (error?.status) {
        const { status } = error;
        
        if (status === 422) {
          setErrors({
            email: 'Неверный формат email'
          });
        } else {
          setErrors({
            general: 'Ошибка при отправке запроса. Попробуйте позже.'
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

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.content}>
        <Card className={styles.resetPasswordCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Сброс пароля</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>

          {errors.general && (
            <div className={styles.generalError}>
              {errors.general}
            </div>
          )}

          {isSuccess ? (
            <div className={styles.successSection}>
              <div className={styles.successIcon}>📧</div>
              <h2 className={styles.successTitle}>Письмо отправлено!</h2>
              <p className={styles.successMessage}>
                Если аккаунт с email <strong>{formData.email}</strong> существует, 
                мы отправили на него инструкции по восстановлению пароля.
              </p>
              <p className={styles.successHint}>
                Проверьте вашу почту и спам, если письмо не пришло в течение нескольких минут.
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
          ) : (
            <>
              <div className={styles.instruction}>
                <p>
                  Введите ваш email, и мы отправим вам инструкции по восстановлению пароля.
                </p>
              </div>

              <form onSubmit={handleSubmit} className={styles.form}>
                <Input
                  label="Email"
                  type="email"
                  name="email"
                  placeholder="your@email.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  error={errors.email}
                  autoComplete="email"
                />

                <div className={styles.actions}>
                  <Button
                    type="submit"
                    variant="primary"
                    size="large"
                    disabled={isLoading}
                    className={styles.submitButton}
                  >
                    {isLoading ? 'Отправка...' : 'Сбросить пароль'}
                  </Button>
                </div>
              </form>

              <div className={styles.footer}>
                <p className={styles.backToLogin}>
                  Вспомнили пароль?{' '}
                  <Button
                    type="button"
                    variant="link"
                    onClick={handleBackToLogin}
                    className={styles.loginLink}
                  >
                    Войдите
                  </Button>
                </p>
                
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
          )}
        </Card>
      </div>
    </div>
  );
};

const ResetPasswordPage = withBaseMainPage(ResetPasswordPageComponent);

export { ResetPasswordPage };