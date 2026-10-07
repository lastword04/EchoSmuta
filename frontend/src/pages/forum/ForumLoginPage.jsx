import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { Input } from '../../shared/ui/Input/Input';
import { useLoginToForumMutation } from '../../entities/auth/api/authApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import { clearPendingCreateTopic } from '../../entities/forum/store/pendingCreateTopicSlice';

import styles from './ForumLoginPage.module.css';

  const ForumLoginPageComponent = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const pendingCreateTopic = useSelector((state) => state.session.pendingCreateTopic); 
  
  const [formData, setFormData] = useState({
    characterName: '',
    password: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showWarning, setShowWarning] = useState(true);
  const [loginToForum] = useLoginToForumMutation();

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
    
    if (!formData.characterName.trim()) {
      newErrors.characterName = 'Введите имя персонажа';
    }
    
    if (!formData.password) {
      newErrors.password = 'Введите пароль';
    }
    
    return newErrors;
  };

  // В handleSubmit, при успешном входе:
const handleSubmit = async (e) => {
  e.preventDefault();
  
  const newErrors = validateForm();
  if (Object.keys(newErrors).length > 0) {
    setErrors(newErrors);
    return;
  }
  
  setIsLoading(true);
  setErrors({});
  
  try {
    await loginToForum({
      name: formData.characterName,
      password: formData.password
    }).unwrap();
    
    // Проверяем, есть ли returnUrl в состоянии навигации
    const returnUrl = location.state?.returnUrl;
    const isCommentPage = location.state?.isCommentPage;
    
    if (returnUrl) {
      // Если есть returnUrl, перенаправляем туда
      navigate(returnUrl, {
        state: {
          successMessage: 'Вы успешно вошли в систему форума!',
          // Передаем дополнительные данные для страницы комментариев
          ...(isCommentPage && {
            forumId: location.state?.forumId,
            forumName: location.state?.forumName,
            topicId: location.state?.topicId,
            topicName: location.state?.topicName
          }),
          // Передаем данные для страницы создания темы
          ...(!isCommentPage && {
            forumName: location.state?.forumName
          })
        }
      });
    } else {
            
      if (pendingCreateTopic && pendingCreateTopic.forumId) {
        const { forumId, forumName } = pendingCreateTopic;
          dispatch(clearPendingCreateTopic());
          
          // Перенаправляем на создание темы с сохраненными данными
          navigate(`/forum/${forumId}/create-topic`, { 
            state: { 
              successMessage: 'Вы успешно вошли в систему форума!',
              forumName: forumName
            } 
          });
        } else {
        // Если нет сохраненного контекста, перенаправляем на стандартную страницу
        navigate('/forum', { 
          state: { 
            successMessage: 'Вы успешно вошли в систему форума!'
          } 
        });
      }
    }
    
  } catch (error) {
    console.error('Forum login error:', error);
    
    if (error?.status) {
      const { status } = error;
      
      if (status === 403) {
        setErrors({
          general: 'Вход возможен только за основного персонажа. Убедитесь, что вводите имя основного персонажа.'
        });
      } else if (status === 401) {
        setErrors({
          general: 'Неверное имя персонажа или пароль'
        });
      } else {
        setErrors({
          general: 'Ошибка входа. Попробуйте позже.'
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

  const handleBackToForum = () => {
    navigate('/forum');
  };

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <Card className={styles.loginCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Вход в форум</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>

          {showWarning && (
            <div className={styles.warningMessage}>
              <div className={styles.warningIcon}>⚠️</div>
              <div className={styles.warningContent}>
                <h3 className={styles.warningTitle}>Важно!</h3>
                <p className={styles.warningText}>
                  Вход в форум возможен только за основного персонажа. 
                  Убедитесь, что вы вводите имя и пароль основного персонажа.
                </p>
                <Button
                  variant="outline"
                  size="small"
                  onClick={() => setShowWarning(false)}
                  className={styles.closeWarning}
                >
                  Понятно
                </Button>
              </div>
            </div>
          )}

          {errors.general && (
            <div className={styles.generalError}>
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Имя персонажа"
              type="text"
              name="characterName"
              placeholder="Введите имя основного персонажа"
              value={formData.characterName}
              onChange={handleInputChange}
              error={errors.characterName}
              autoComplete="username"
            />

            <Input
              label="Пароль"
              type="password"
              name="password"
              placeholder="Введите пароль"
              value={formData.password}
              onChange={handleInputChange}
              error={errors.password}
              autoComplete="current-password"
            />

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
            <Button
              type="button"
              variant="link"
              onClick={handleBackToForum}
              className={styles.backButton}
            >
              ← Вернуться к форумам
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

const ForumLoginPage = withBaseMainPage(ForumLoginPageComponent);

export { ForumLoginPage };