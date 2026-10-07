import { useState, useEffect } from 'react';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { Modal } from '../../../../shared/ui/Modal/Modal';
import { useLazyCheckForumAuthQuery } from '../../api/forumApi';
import styles from './AuthCheckModal.module.css';

export const AuthCheckModal = ({ isOpen, onClose, onAuthSuccess, onLoginClick, message }) => {
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState('');
  const [checkForumAuth] = useLazyCheckForumAuthQuery();

  const checkAuth = async () => {
    setChecking(true);
    setError('');
    
    try {
      const isAuthenticated = await checkForumAuth(undefined, false).unwrap().catch(() => false);
      if (isAuthenticated) {
        onAuthSuccess();
        onClose();
      } else {
        setError(message || 'Вы не вошли в систему. Для выполнения этого действия требуется вход за основного персонажа.');
      }
    } catch (error) {
      console.error('Auth check error:', error);
      setError(message || 'Вы не вошли в систему. Для выполнения этого действия требуется вход за основного персонажа.');
    } finally {
      setChecking(false);
    }
  };

  const handleLogin = () => {
    onClose();
    // Открываем страницу входа
    if (onLoginClick) {
      onLoginClick(); // ← ВОТ ТАК ПРАВИЛЬНО!
    }
  };

  const handleStay = () => {
    onClose();
  };

  // При открытии модального окна сразу проверяем авторизацию
  // checkAuth без useCallback — новая ссылка каждый рендер; добавление в deps
  useEffect(() => {
    if (isOpen) {
      checkAuth();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <Card className={styles.authCheckCard}>
        <div className={styles.header}>
          <h2 className={styles.title}>Требуется авторизация</h2>
        </div>

        {error && (
          <div className={styles.errorMessage}>
            {error}
          </div>
        )}

        <div className={styles.actions}>
          <Button
            variant="primary"
            size="medium"
            onClick={handleLogin}
            disabled={checking}
            className={styles.loginButton}
          >
            Войти
          </Button>
          <Button
            variant="outline"
            size="medium"
            onClick={handleStay}
            disabled={checking}
            className={styles.stayButton}
          >
            Остаться
          </Button>
        </div>
      </Card>
    </Modal>
  );
};