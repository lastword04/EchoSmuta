import { useState } from 'react';
import { Card } from '../../../../shared/ui/Card/Card';
import { useTrackTopicActivityMutation } from '../../api/commentApi';
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from './TopicCard.module.css';

const formatDate = (dateString) => {
  if (!dateString) return 'Нет сообщений';
  
  const date = parseUtcDate(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const TopicCard = ({ topicItem, onEnterTopic }) => {
  const { topic, comments_count } = topicItem;
  const {
    name,
    author_character_name,
    views,
    last_comment_character_name,
    last_comment_datetime
  } = topic;

  const [trackingActivity, setTrackingActivity] = useState(false);
  const [trackTopicActivity] = useTrackTopicActivityMutation();

  // Обработчик клика на имя темы
  const handleTopicClick = async () => {
    setTrackingActivity(true);
    
    try {
      // Отслеживаем активность в теме
      await trackTopicActivity({ forumId: topic.forum_id, topicId: topic.id }).unwrap();
      
      // Вызываем callback для перехода к теме
      onEnterTopic(topic.id, name);
      
    } catch (error) {
      console.error('Failed to track topic activity:', error);
      // Всё равно переходим к теме, даже если tracking не удался
      onEnterTopic(topic.id, name);
    } finally {
      setTrackingActivity(false);
    }
  };

  return (
    <Card className={styles.topicCard}>
      <div className={styles.topicHeader}>
        {/* Сделаем имя темы кликабельным */}
        <h3 
          className={`${styles.topicName} ${styles.clickable}`}
          onClick={handleTopicClick}
          title={`Открыть тему "${name}"`}
        >
          {trackingActivity ? 'Открытие...' : name}
        </h3>
        {/* Убираем кнопку "Открыть" */}
      </div>
      
      <div className={styles.topicInfo}>
        <div className={styles.topicAuthor}>
          <span className={styles.infoLabel}>Автор:</span>
          <span className={styles.infoValue}>{author_character_name}</span>
        </div>
        
        <div className={styles.topicStats}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Ответов:</span>
            <span className={styles.statValue}>{comments_count}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Просмотров:</span>
            <span className={styles.statValue}>{views}</span>
          </div>
        </div>
      </div>
      
      <div className={styles.lastComment}>
        {last_comment_character_name ? (
          <div className={styles.lastCommentInfo}>
            <div className={styles.lastCommentAuthor}>
              Последнее сообщение: <strong>{last_comment_character_name}</strong>
            </div>
            <div className={styles.lastCommentDate}>
              {formatDate(last_comment_datetime)}
            </div>
          </div>
        ) : (
          <div className={styles.noComments}>
            Нет сообщений
          </div>
        )}
      </div>
      
      <div className={styles.moderatorInfo}>
        <span className={styles.moderatorLabel}>Модератор: </span>
        <span className={styles.moderatorName}>Не назначен</span>
      </div>
    </Card>
  );
};