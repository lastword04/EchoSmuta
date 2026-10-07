import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { Input } from '../../../../shared/ui/Input/Input';
import { useCreateCommentMutation } from '../../api/commentApi';
import { useLazyCheckForumAuthQuery } from '../../api/forumApi';
import { setPendingCommentText, clearPendingCommentText } from '../../store/pendingCommentSlice';
import styles from './CommentForm.module.css';

export const CommentForm = ({ 
  forumId, 
  topicId, 
  onCommentCreated, 
  initialText = '',
  attachedFileIds = [],
  onShowAuthModal
}) => {
  const dispatch = useDispatch();
  const [createComment] = useCreateCommentMutation();
  const [checkForumAuth] = useLazyCheckForumAuthQuery();
  const pendingCommentText = useSelector((state) => state.session.pendingComment.commentText);

  const [commentText, setCommentText] = useState(initialText);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (pendingCommentText && !commentText) {
      setCommentText(pendingCommentText);
    }
  }, [pendingCommentText, commentText]);

  const handleSubmit = async (e) => {
    e.preventDefault();


    
    if (!commentText.trim()) {
      setError('Введите текст комментария');
      return;
    }
    
    if (commentText.length > 1000) {
      setError('Комментарий не должен превышать 1000 символов');
      return;
    }
    
    setIsSubmitting(true);
    setError('');
    
    try {
      // Проверяем авторизацию перед созданием комментария
      const isAuthenticated = await checkForumAuth(undefined, false).unwrap().catch(() => false);
      
      if (!isAuthenticated) {
        // Сохраняем текст комментария перед переходом на авторизацию
        if (commentText.trim()) {
          dispatch(setPendingCommentText(commentText.trim()));
        }
        
        // Если не авторизован, выбрасываем событие для показа модального окна
        if (onShowAuthModal) {
          onShowAuthModal({
            message: 'Для добавления комментария необходимо войти в систему за основного персонажа',
            onAuthSuccess: async () => {
              await submitComment();
            }
          });
        }
        return;
      }
      
      // Если авторизован, отправляем комментарий
      await submitComment();
      
    } catch (error) {
      console.error('Auth check error:', error);
      
      // Сохраняем текст комментария перед переходом на авторизацию
      if (commentText.trim()) {
        dispatch(setPendingCommentText(commentText.trim()));
      }
      
      // В случае ошибки проверки авторизации тоже показываем модальное окно
      if (onShowAuthModal) {
        onShowAuthModal({
          message: 'Для добавления комментария необходимо войти в систему за основного персонажа',
          onAuthSuccess: async () => {
            await submitComment();
          }
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Отдельная функция для отправки комментария
  const submitComment = async () => {
    try {
      const commentData = {
        text: commentText.trim()
      };
      
      // Добавляем ID файлов, если есть
      if (attachedFileIds.length > 0) {
        commentData.files_ids = attachedFileIds;
      }
      
      const newComment = await createComment({ forumId, topicId, commentData }).unwrap();
      
      // Очищаем форму
      setCommentText('');
      
      // Очищаем сохраненный текст из стора
      dispatch(clearPendingCommentText());
      
      // Вызываем callback для обновления списка комментариев
      if (onCommentCreated) {
        onCommentCreated(newComment);
      }
      
    } catch (error) {
      console.error('Create comment error:', error);
      
      if (error?.status) {
        const { status } = error;
        
        if (status === 422) {
          // Ошибки валидации
          setError('Некорректный текст комментария');
        } else if (status === 401 || status === 403) {
          // Сохраняем текст комментария
          dispatch(setPendingCommentText(commentText.trim()));
          
          // Показываем модальное окно через пропс
          if (onShowAuthModal) {
            setTimeout(() => {
              onShowAuthModal({
                message: 'Ошибка авторизации. Попробуйте войти снова.',
                onAuthSuccess: async () => {
                  await submitComment();
                }
              });
            }, 2000);
          }
        } else {
          setError('Ошибка создания комментария. Попробуйте позже.');
        }
      } else {
        setError('Ошибка подключения к серверу. Проверьте соединение и попробуйте снова.');
      }
    }
  };

  const handleTextChange = (e) => {
    const { value } = e.target;
    setCommentText(value);
    
    if (error) {
      setError('');
    }
  };



  return (
    <Card className={styles.commentFormCard}>
      <div className={styles.formHeader}>
        <h3 className={styles.formTitle}>Добавить комментарий</h3>
      </div>
      
      {/* Показываем количество прикрепленных файлов */}
      {attachedFileIds.length > 0 && (
        <div className={styles.attachedFilesInfo}>
          Прикреплено файлов: {attachedFileIds.length}
        </div>
      )}
      {error && (
        <div className={styles.errorMessage}>
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className={styles.form}>
        <Input
          label="Текст комментария"
          type="textarea"
          name="commentText"
          placeholder="Введите ваш комментарий..."
          value={commentText}
          onChange={handleTextChange}
          error={error}
          disabled={isSubmitting}
          rows={4}
          maxLength={1000}
          
        />
        
        <div className={styles.formActions}>
          <Button
            type="submit"
            variant="primary"
            size="medium"
            disabled={isSubmitting}
            className={styles.submitButton}
          >
            {isSubmitting ? 'Отправка...' : 'Отправить'}
          </Button>
          
          <div className={styles.charCounter}>
            {commentText.length}/1000
          </div>
        </div>
      </form>
    </Card>
  );
};