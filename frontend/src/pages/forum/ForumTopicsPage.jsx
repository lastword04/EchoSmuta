import { useState, useEffect, useMemo, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { TopicCard } from '../../entities/forum/ui/TopicCard/TopicCard';
import { AuthCheckModal } from '../../entities/forum/components/AuthCheckModal/AuthCheckModal';
import { 
  useGetForumTopicsQuery, 
  useLazyCheckForumAuthQuery 
} from '../../entities/forum/api/forumApi';
import { setPendingCreateTopic, clearPendingCreateTopic } from '../../entities/forum/store/pendingCreateTopicSlice';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './ForumTopicsPage.module.css';

const ForumTopicsPageComponent = () => {
  const { forumId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  const [checkForumAuth] = useLazyCheckForumAuthQuery();

  const pendingCreateTopic = useSelector((state) => state.session.pendingCreateTopic);
  
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [notification, setNotification] = useState(null);
  const [forumName, setForumName] = useState(location.state?.forumName || '');
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);

  const { 
    data: topicsData = { objects: [], count: 0 }, 
    isLoading: loading,
    isError,
    isFetching
  } = useGetForumTopicsQuery({ forumId, limit, offset });

  const topics = useMemo(
    () => topicsData.objects || [],
    [topicsData.objects]
  );
  const totalCount = topicsData.count || 0;
  const totalPages = Math.ceil(totalCount / limit);

  // Устанавливаем forumName из данных, когда они приходят
  useEffect(() => {
    if (topics.length > 0 && !forumName) {
      const apiForumName = topics[0]?.topic?.forum_name;
      const navigationForumName = location.state?.forumName;
      setForumName(apiForumName || navigationForumName || 'Форум');
    }
  }, [topics, location.state?.forumName, forumName]);


  const error = isError ? 'Ошибка загрузки тем. Попробуйте позже.' : null;

  // Обработчик создания новой темы с комментарием
  const handleTopicCreated = useCallback(() => {
    // Создаём уведомление, если мы не на первой странице
    const currentPage = Math.floor(offset / limit) + 1;
    const targetPage = 1;
    
    if (currentPage !== targetPage) {
      // Если мы НЕ на первой странице, показываем уведомление
      setNotification({
        message: 'Ваша тема создана!',
        actionText: 'Перейти к теме',
        onAction: () => {
          setOffset(0); // Переход на первую страницу
          setNotification(null);
        }
      });
      
      // Автоматически скрываем уведомление через 5 секунд
      setTimeout(() => {
        setNotification(null);
      }, 5000);
    }
  }, [offset, limit]);

  // useEffect для отслеживания успешного создания темы
  useEffect(() => {
    if (location.state?.newTopicData) {
      handleTopicCreated();
      
      // Очищаем состояние, чтобы не показывать уведомление при обновлении
      window.history.replaceState(
        { ...location.state, newTopicData: undefined },
        '',
        location.pathname
      );
    }
  }, [location.state, location.pathname, handleTopicCreated]);

  const handleEnterTopic = (topicId, topicName) => {
    navigate(`/forum/${forumId}/topics/${topicId}/comments`, {
      state: {
        topicName: topicName,
        forumName: forumName
      }
    });
  };

  const handleBackToForums = () => {
    navigate('/forum');
  };

  const handleCreateTopic = async () => {
    try {
      const isAuthenticated = await checkForumAuth(undefined, false).unwrap().catch(() => false);
      
      if (isAuthenticated) {
        navigate(`/forum/${forumId}/create-topic`, {
          state: {
            forumName: forumName
          }
        });
      } else {
        dispatch(setPendingCreateTopic({
          forumId: forumId,
          forumName: forumName
        }));
        setShowAuthModal(true);
      }
    } catch (error) {
      console.error('Auth check error:', error);
      dispatch(setPendingCreateTopic({
        forumId: forumId,
        forumName: forumName
      }));
      setShowAuthModal(true);
    }
  };

  const handleAuthSuccess = () => {
        
    if (pendingCreateTopic) {
        const { forumId: savedForumId, forumName: savedForumName } = pendingCreateTopic;
        dispatch(clearPendingCreateTopic());
        
        navigate(`/forum/${savedForumId}/create-topic`, {
        state: { forumName: savedForumName } // ← Используем сохранённые значения!
        });
    } else {
      navigate(`/forum/${forumId}/create-topic`, {
        state: {
          forumName: forumName
        }
      });
    }
  };

  const handleLoginClick = () => {
    setShowAuthModal(false);
    navigate('/forum/login', {
      state: {
        returnUrl: `/forum/${forumId}/create-topic`,
        forumName: forumName
      }
    });
  };

  const handlePageChange = (newPage) => {
    const newOffset = (newPage - 1) * limit;
    setOffset(newOffset);
  };

  // Вычисляем текущую страницу на основе offset
  const currentPage = Math.floor(offset / limit) + 1;

  // Компонент уведомления
  const NotificationBanner = ({ message, onAction, actionText, onDismiss }) => (
    <div className={styles.notificationBanner}>
      <span>{message}</span>
      <div className={styles.notificationActions}>
        {onAction && (
          <Button variant="link" size="small" onClick={onAction}>
            {actionText}
          </Button>
        )}
        <Button variant="link" size="small" onClick={onDismiss}>
          ×
        </Button>
      </div>
    </div>
  );

  return (
    <div className={`${styles.page} ${notification ? styles.pageWithNotification : ''}`}>
      {/* Фиксированное уведомление сверху экрана */}
      {notification && (
        <NotificationBanner
          message={notification.message}
          actionText={notification.actionText}
          onAction={notification.onAction}
          onDismiss={() => setNotification(null)}
        />
      )}
      
      <div className={styles.content}>
        <Card className={styles.topicsCard}>
          <div className={styles.header}>
            <div className={styles.headerContent}>
              <h1 className={styles.title}>Темы форума</h1>
              <h2 className={styles.subtitle}>{forumName}</h2>
            </div>
            <div className={styles.headerActions}>
              <Button
                variant="primary"
                size="small"
                onClick={handleCreateTopic}
                className={styles.createTopicButton}
              >
                Создать тему
              </Button>
              <Button
                variant="outline"
                size="small"
                onClick={handleBackToForums}
                className={styles.backButton}
              >
                ← Назад
              </Button>
            </div>
          </div>

          {error && (
            <div className={styles.errorMessage}>
              {error}
            </div>
          )}

          {loading && !topics.length ? (
            <div className={styles.loading}>
              <span>Загрузка тем...</span>
            </div>
          ) : (
            <div className={styles.topicsContainer}>
              {topics.length === 0 ? (
                <div className={styles.emptyState}>
                  <p>В этом форуме пока нет тем</p>
                  <Button
                    variant="primary"
                    size="medium"
                    onClick={handleCreateTopic}
                  >
                    Создать первую тему
                  </Button>
                </div>
              ) : (
                <div className={styles.topicsGrid}>
                  {topics.map((topicItem) => (
                    <TopicCard
                      key={topicItem.topic.id}
                      topicItem={topicItem}
                      onEnterTopic={handleEnterTopic}
                    />
                  ))}
                </div>
              )}

              {/* Пагинация */}
              {totalCount > 0 && (
                <div className={styles.pagination}>
                  <div className={styles.paginationInfo}>
                    Всего тем: {totalCount}
                  </div>
                  <div className={styles.paginationControls}>
                    <Button
                      variant="outline"
                      size="small"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1 || isFetching}
                      className={styles.paginationButton}
                    >
                      ←
                    </Button>
                    
                    <span className={styles.paginationCurrent}>
                      {currentPage} / {totalPages}
                    </span>
                    
                    <Button
                      variant="outline"
                      size="small"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= totalPages || isFetching}
                      className={styles.paginationButton}
                    >
                      →
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
      
      {showAuthModal && (
        <AuthCheckModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          onAuthSuccess={handleAuthSuccess}
          onLoginClick={handleLoginClick}
        />
      )}
    </div>
  );
};

const ForumTopicsPage = withBaseMainPage(ForumTopicsPageComponent);

export { ForumTopicsPage };