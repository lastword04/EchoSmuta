// entities/forum/ui/CommentFiles/CommentFiles.jsx
import { config } from '../../../../shared/config/env/env';
import styles from './CommentFiles.module.css';

export const CommentFiles = ({ files }) => {
  if (!files || files.length === 0) return null;

  return (
    <div className={styles.filesContainer}>
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
  );
};
