import { Card } from '../../../../shared/ui/Card/Card';
import { config } from '../../../../shared/config/env/env';
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from './CommentCard.module.css';

const formatDate = (dateString) => {
  if (!dateString) return 'Неизвестно';

  const date = parseUtcDate(dateString);
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const CommentCard = ({ comment }) => {
  const {
    author_character_name,
    text,
    created_at,
    files = []
  } = comment;

  return (
    <Card className={styles.commentCard}>
      <div className={styles.commentHeader}>
        <div className={styles.authorInfo}>
          <h4 className={styles.authorName}>{author_character_name}</h4>
          <span className={styles.commentDate}>{formatDate(created_at)}</span>
        </div>
      </div>

      <div className={styles.commentContent}>
        <p className={styles.commentText}>{text}</p>

        {files.length > 0 && (
          <div className={styles.commentFiles}>
            {files.map((file) => {
              const fileSrc = `${config.FILE_API_BASE_URL}/${file.id}/content`;
              const isImage = file.content_type?.startsWith('image/');
              return (
                <div key={file.id} className={styles.fileItem}>
                  {isImage ? (
                    <a href={fileSrc} target="_blank" rel="noopener noreferrer">
                      <img
                        src={fileSrc}
                        alt={file.filename}
                        className={styles.imagePreview}
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = '/images/city-trade/no-image.png';
                        }}
                      />
                    </a>
                  ) : (
                    <a
                      href={fileSrc}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.fileLink}
                    >
                      📎 {file.filename} ({(file.size / 1024).toFixed(1)} KB)
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};
