import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';  // Наш кастомный Button

import { Input } from '../../shared/ui/Input/Input';
import { useLoginMutation } from '../../entities/auth/api/authApi';
import { inventoryApi } from '../../entities/items/api/inventoryApi';
import { characterStatsApi } from '../../entities/character/api/characterStatsApi';
import { economyApi } from '../../entities/economy/api/economyApi';
import { characterApi } from '../../entities/character/api/characterApi';
import { setActiveCharacterName } from '../../shared/store/activeCharacterNameSlice';
import { setActiveCharacterId } from '../../shared/store/activeCharacterIdSlice';
import { setUserRole } from '../../shared/store/userRoleSlice';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import visitService from '../../shared/services/visitService';
import styles from './LoginPage.module.css';

const LoginComponentPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();  

  const registrationSuccessMessage = location.state?.registrationSuccess;
  const authMessage = location.state?.authRequired;
  
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [login] = useLoginMutation();

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
    
    if (!formData.username.trim()) {
      newErrors.username = 'Введите имя пользователя';
    }
    
    if (!formData.password) {
      newErrors.password = 'Введите пароль';
    }
    // } else if (formData.password.length < 8) {
    //   newErrors.password = 'Пароль должен содержать минимум 8 символов';
    // }
    
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
    const fingerprint = await visitService.getFingerprint();
    
    const loginData = {
      name: formData.username,
      password: formData.password,
      fingerprint: fingerprint
    };
    
    // Отправка данных на сервер
    const dataLogin = await login(loginData).unwrap();
      // Полный сброс кэша ДО прогрева: данных прошлой сессии не остаётся
      dispatch(inventoryApi.util.resetApiState());
      dispatch(characterApi.util.resetApiState());
      dispatch(characterStatsApi.util.resetApiState());
      dispatch(economyApi.util.resetApiState());
    
    dispatch(setActiveCharacterName(dataLogin.character.name));
    dispatch(setActiveCharacterId(dataLogin.character.id));
    // Роль из ответа логина (dataLogin.user.role) — для синхронного гарда /admin
    dispatch(setUserRole(dataLogin.user?.role ?? null));
    // Прогреваем кэш до перехода, чтобы /characters открылся мгновенно и без stale-состояний
    await Promise.all([
      dispatch(characterApi.endpoints.getMyCharacters.initiate(undefined, { forceRefetch: true })),
      dispatch(characterApi.endpoints.getCharacterCreationStatus.initiate(undefined, { forceRefetch: true })),
      dispatch(characterApi.endpoints.checkHasDetachedCharacters.initiate(undefined, { forceRefetch: true })),
    ]);
    // После успешной авторизации перенаправляем на страницу выбора персонажа
    navigate('/characters');
    
  } catch (error) {
    // Обработка ошибок от сервера
    if (error?.status) {
      const { status } = error;
      
      if (status === 403) {
        setErrors({
          general: 'Неверное имя пользователя или пароль'
        });
      } else {
        setErrors({
          general: 'Ошибка авторизации. Попробуйте позже.'
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

  // Используем наш кастомный Button вместо нативной кнопки
  const handleForgotPassword = () => {
    navigate('/reset-password');
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.content}>
        <Card className={styles.loginCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Вход в игру</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>
          {registrationSuccessMessage && (
            <div className={styles.successMessage}>
              {registrationSuccessMessage}
            </div>
          )}
          {authMessage && (
            <div className={styles.infoMessage}>
              {authMessage}
            </div>
          )}

          {errors.general && (
            <div className={styles.generalError}>
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Имя пользователя"
              type="text"
              name="username"
              placeholder="Введите ваш логин"
              value={formData.username}
              onChange={handleInputChange}
              error={errors.username}
              autoComplete="username"
            />

            <Input
              label="Пароль"
              type="password"
              name="password"
              placeholder="Введите ваш пароль"
              value={formData.password}
              onChange={handleInputChange}
              error={errors.password}
              autoComplete="current-password"
            />

            <div className={styles.forgotPassword}>
              {/* Заменяем нативную кнопку на наш кастомный Button */}
              <Button
                type="button"
                variant="outline"
                size="small"                
                onClick={handleForgotPassword}
                className={styles.forgotPasswordButton}
              >
                Забыли пароль?
              </Button>
            </div>

            <div className={styles.actions}>
              <Button
                type="submit"
                variant="primary"
                size="large"                
                disabled={isLoading}
                className={styles.submitButton}
              >
                {isLoading ? 'Вход...' : 'Войти'}
              </Button>
            </div>
          </form>

          <div className={styles.footer}>
            <p className={styles.noAccount}>
              Нет аккаунта?{' '}
              {/* Заменяем нативную кнопку на наш кастомный Button */}
              <Button
                type="button"
                variant="link"                
                onClick={() => navigate('/register')}
                className={styles.registerLink}
              >
                Зарегистрируйтесь
              </Button>
            </p>
            
            {/* Заменяем нативную кнопку на наш кастомный Button */}
            <Button
              type="button"
              variant="link"              
              onClick={handleBackToHome}
              className={styles.backToHome}
            >
              ← Вернуться на главную
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

const LoginPage = withBaseMainPage(LoginComponentPage);

export { LoginPage }