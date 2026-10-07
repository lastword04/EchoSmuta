import { useState, useRef } from 'react';
import { useSelector } from 'react-redux';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { Spinner } from '../../shared/ui/Spinner/Spinner';
import { CommentCard } from '../../entities/forum/ui/CommentCard/CommentCard';
import { CommentForm } from '../../entities/forum/ui/CommentForm/CommentForm';
import { useGetTopicCommentsQuery } from '../../entities/forum/api/commentApi';
import { AuthCheckModal } from '../../entities/forum/components/AuthCheckModal/AuthCheckModal';
import { 
  useUploadFileMutation, 
  useUploadFilesBatchMutation, 
  useDeleteFileMutation 
} from '../../entities/file/api/fileApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './TopicCommentsPage.module.css';

  const TopicCommentsPageComponent = () => {
  const { forumId, topicId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const pendingCommentText = useSelector((state) => state.session.pendingComment.commentText);
  
  const [error, setError] = useState(null); // локальные ошибки (файлы и т.п.)
  const [topicName] = useState(location.state?.topicName || 'Тема');
  const [forumName] = useState(location.state?.forumName || 'Форум');
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);

  const {
    data: commentsData = { objects: [], count: 0 },
    isLoading: loading,
    isError,
    isFetching,
  } = useGetTopicCommentsQuery({ forumId, topicId, limit, offset });

  const comments = commentsData.objects || [];
  const totalCount = commentsData.count || 0;
  const totalPages = Math.ceil(totalCount / limit);
  const queryError = isError ? 'Ошибка загрузки комментариев. Попробуйте позже.' : null;
  const displayError = error || queryError;

  
  // Состояния для файлов
  const [uploadingFiles, setUploadingFiles] = useState([]); // Загружаемые файлы
  const [uploadedFiles, setUploadedFiles] = useState([]);   // Успешно загруженные файлы
  const fileInputRef = useRef(null);
  const [uploadFile] = useUploadFileMutation();
  const [uploadFilesBatch] = useUploadFilesBatchMutation();
  const [deleteFile] = useDeleteFileMutation();
  
  // Состояние для модального окна авторизации
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalConfig, setAuthModalConfig] = useState(null);
   
  // Состояние для уведомлений
  const [notification, setNotification] = useState(null);

  
  const handleShowAuthModal = (config) => {
    setAuthModalConfig(config);
    setShowAuthModal(true);
  };

  const handleAuthSuccess = async () => {
    setShowAuthModal(false);
    if (authModalConfig?.onAuthSuccess) {
      try {
        await authModalConfig?.onAuthSuccess();
      } catch (error) {
        console.error('Error after auth success:', error);
      }
    }
  };

  const handleCloseAuthModal = () => {
    setShowAuthModal(false);
    setAuthModalConfig(null);
  };

  const handleCommentCreated = () => {
    // Список обновится сам: createComment инвалидирует тег Comments
    const newCount = totalCount + 1;
    const newTotalPages = Math.ceil(newCount / limit);
    const currentPage = Math.floor(offset / limit) + 1;
    const targetPage = newTotalPages;

    if (currentPage !== targetPage) {
      setNotification({
        message: 'Ваш комментарий добавлен!',
        actionText: 'Перейти к комментарию',
        onAction: () => {
          handlePageChange(targetPage);
          setNotification(null);
        }
      });
      setTimeout(() => setNotification(null), 5000);
    }

    // Очищаем загруженные файлы
    setUploadedFiles([]);
  };

  const handleBackToTopics = () => {
    navigate(`/forum/${forumId}/topics`, {
      state: { forumName, topicName }
    });
  };

  const handlePageChange = (newPage) => {
    const newOffset = (newPage - 1) * limit;
    setOffset(newOffset);
  };

  const currentPage = Math.floor(offset / limit) + 1;

  // Работа с файлами
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    if (files.length > 0) {
      uploadSelectedFiles(files);
    }
    event.target.value = '';
  };

  const uploadSelectedFiles = async (filesToUpload) => {
    setUploadingFiles(prev => [...prev, ...filesToUpload]);

    try {
      let results;

      if (filesToUpload.length === 1) {
        const file = filesToUpload[0];
        const result = await uploadFile({ file, subdir: 'forum' }).unwrap();
        results = [result];
      } else {
        results = await uploadFilesBatch({ files: filesToUpload, subdir: 'forum' }).unwrap();
      }

      const mergedResults = results.map((result, index) => ({
        ...result,
        originalName: filesToUpload[index].name,
        originalSize: filesToUpload[index].size
      }));

      setUploadedFiles(prev => [...prev, ...mergedResults]);

    } catch (error) {
      console.error('Error uploading files:', error);

      // проверяем код ошибки
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        handleShowAuthModal({ // ← ВЫЗЫВАЕМ ПРОПС
          message: 'Чтобы прикреплять файлы, нужно войти в систему',
          onAuthSuccess: async () => {
            await uploadSelectedFiles(filesToUpload);
          }
        });
      } else {
        setError('Ошибка загрузки файлов. Попробуйте еще раз.');
      }
    } finally {
      setUploadingFiles(prev =>
        prev.filter(uploadingFile =>
          !filesToUpload.some(file =>
            file.name === uploadingFile.name && file.size === uploadingFile.size
          )
        )
      );
    }
  };


  const handleRemoveUploadedFile = async (file, index) => {
    try {
      await deleteFile(file.id).unwrap();
      setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    } catch (error) {
      console.error('Error deleting file:', error);
      setError('Не удалось удалить файл. Попробуйте позже.');
    }
  };

  // UI компонентов
  const UploadingFileItem = ({ file }) => (
    <div className={styles.fileItem}>
      <span className={styles.fileName}>
        ⏳ {file.name} ({(file.size / 1024).toFixed(1)} KB)
      </span>
      <Spinner size="small" />
    </div>
  );

  const UploadedFileItem = ({ file, index, onRemove }) => (
    <div className={styles.fileItem}>
      <span className={styles.fileName}>
        ✅ {file.originalName} ({(file.originalSize / 1024).toFixed(1)} KB)
      </span>
      <Button
        variant="link"
        size="small"
        onClick={() => onRemove(file, index)}
        className={styles.removeFileButton}
      >
        ×
      </Button>
    </div>
  );

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
      {notification && (
        <NotificationBanner
          message={notification.message}
          actionText={notification.actionText}
          onAction={notification.onAction}
          onDismiss={() => setNotification(null)}
        />
      )}
      
      <div className={styles.content}>
        <Card className={styles.commentsCard}>
          <div className={styles.header}>
            <div className={styles.headerContent}>
              <h1 className={styles.title}>Комментарии</h1>
              <h2 className={styles.subtitle}>{topicName}</h2>
              <h3 className={styles.forumSubtitle}>{forumName}</h3>
            </div>
            <div className={styles.headerActions}>
              <Button
                variant="outline"
                size="small"
                onClick={handleBackToTopics}
                className={styles.backButton}
              >
                ← Назад к темам
              </Button>
            </div>
          </div>

          {displayError && <div className={styles.errorMessage}>{displayError}</div>}

          {loading && !comments.length ? (
            <div className={styles.loading}>
              <span>Загрузка комментариев...</span>
            </div>
          ) : (
            <div className={styles.commentsContainer}>
              <div className={styles.commentsList}>
                {comments.length === 0 ? (
                  <div className={styles.emptyState}>
                    <p>В этой теме пока нет комментариев</p>
                  </div>
                ) : (
                 comments.map((commentItem) => (
                    <div key={commentItem.id} className={styles.commentWithFiles}>
                      <CommentCard comment={commentItem} />
                    </div>
                  ))
                )}
              </div>

              <div className={styles.commentFormSection}>
                <div className={styles.fileAttachmentCompact}>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    multiple
                    accept="image/*,.pdf,.doc,.docx"
                    className={styles.fileInput}
                  />
                  
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => fileInputRef.current?.click()}
                    className={styles.pinButton}
                    title="Прикрепить файлы"
                    disabled={uploadingFiles.length > 0}
                  >
                    {uploadingFiles.length > 0 ? '⏳' : '📎'}
                  </Button>

                  {(uploadingFiles.length > 0 || uploadedFiles.length > 0) && (
                    <span className={styles.fileCounter}>
                      {uploadingFiles.length + uploadedFiles.length}
                    </span>
                  )}
                </div>

                {(uploadingFiles.length > 0 || uploadedFiles.length > 0) && (
                  <div className={styles.filesPreview}>
                    <div className={styles.filesPreviewHeader}>Прикрепленные файлы:</div>
                    <div className={styles.attachedFilesList}>
                      {uploadingFiles.map((file) => (
                        <UploadingFileItem
                          key={`uploading-${file.name}-${file.size}-${file.lastModified}`}
                          file={file}
                        />
                      ))}
                      
                      {uploadedFiles.map((file, index) => (
                        <UploadedFileItem
                          key={`uploaded-${file.id}`}
                          file={file}
                          index={index}
                          onRemove={handleRemoveUploadedFile}
                        />
                      ))}
                    </div>
                  </div>
                )}

                <CommentForm
                  forumId={forumId}
                  topicId={topicId}
                  onCommentCreated={handleCommentCreated}
                  initialText={pendingCommentText}
                  onShowAuthModal={handleShowAuthModal}
                  attachedFileIds={uploadedFiles.map(file => file.id)}
                />
              </div>

              {totalCount > 0 && (
                <div className={styles.pagination}>
                  <div className={styles.paginationInfo}>
                    Всего комментариев: {totalCount}
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
          onClose={handleCloseAuthModal}
          onAuthSuccess={handleAuthSuccess}
          message={authModalConfig?.message}
        />
      )}
    </div>
  );
};

const TopicCommentsPage = withBaseMainPage(TopicCommentsPageComponent);

export { TopicCommentsPage };
