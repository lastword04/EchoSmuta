import { Card } from '../../../../shared/ui/Card/Card';
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from './ForumCard.module.css';

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

export const ForumCard = ({ forum, onEnter }) => {
  const {
    name,
    last_comment_character_name,
    last_comment_datetime
  } = forum.forum;

  // Обработчик клика на имя форума
  const handleForumClick = () => {
    onEnter(forum.forum.id, forum.forum.name);
  };

  return (
    <Card className={styles.forumCard}>
      <div className={styles.forumHeader}>
        {/* Сделаем имя форума кликабельным */}
        <h3 
          className={`${styles.forumName} ${styles.clickable}`}
          onClick={handleForumClick}
          title={`Войти в форум "${name}"`}
        >
          {name}
        </h3>
        {/* Убираем кнопку "Войти" */}
      </div>
      
      <div className={styles.forumStats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Тем:</span>
          <span className={styles.statValue}>{forum.topics_count}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Сообщений:</span>
          <span className={styles.statValue}>{forum.comments_count}</span>
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