import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { Input } from '../../shared/ui/Input/Input';
import { Textarea } from '../../shared/ui/Textarea/Textarea';
import { Spinner } from '../../shared/ui/Spinner/Spinner';
import { 
  useLazyCheckForumAuthQuery, 
  useCreateTopicWithCommentMutation 
} from '../../entities/forum/api/forumApi';
import { 
  useUploadFileMutation, 
  useUploadFilesBatchMutation, 
  useDeleteFileMutation 
} from '../../entities/file/api/fileApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './CreateTopicPage.module.css';

  const CreateTopicPageComponent = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { forumId } = useParams();
  const fileInputRef = useRef(null);
  const [checkForumAuth] = useLazyCheckForumAuthQuery();
  const [createTopicWithComment] = useCreateTopicWithCommentMutation();

  const [formData, setFormData] = useState({
    title: '',
    comment: '',
    forumName: location.state?.forumName || 'Форум'
  });

  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  const [uploadingFiles, setUploadingFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadFile] = useUploadFileMutation();
  const [uploadFilesBatch] = useUploadFilesBatchMutation();
  const [deleteFile] = useDeleteFileMutation();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const isAuthenticated = await checkForumAuth(undefined, false).unwrap().catch(() => false);
        if (!isAuthenticated) {
          navigate('/forum/login', {
            state: {
              returnUrl: `/forum/${forumId}/create-topic`,
              forumId,
              forumName: formData.forumName
            }
          });
        } else {
          setAuthChecked(true);
        }
      } catch (error) {
        console.error('Auth check error:', error);
        navigate('/forum/login', {
          state: {
            returnUrl: `/forum/${forumId}/create-topic`,
            forumId,
            forumName: formData.forumName
          }
        });
      }
    };

    if (forumId) {
      checkAuth();
    }
  }, [navigate, forumId, formData.forumName, checkForumAuth]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

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
      setErrors(prev => ({ ...prev, general: 'Ошибка загрузки файлов. Попробуйте еще раз.' }));
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

  const handleRemoveFile = async (file, index) => {
    try {
      await deleteFile(file.id).unwrap();
      setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    } catch (err) {
      console.error('Ошибка при удалении файла:', err);
      setErrors(prev => ({ ...prev, general: 'Ошибка при удалении файла' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.title.trim()) {
      newErrors.title = 'Введите название темы';
    } else if (formData.title.length < 3) {
      newErrors.title = 'Название темы должно содержать минимум 3 символа';
    } else if (formData.title.length > 100) {
      newErrors.title = 'Название темы не должно превышать 100 символов';
    }

    if (!formData.comment.trim()) {
      newErrors.comment = 'Введите текст комментария';
    } else if (formData.comment.trim().length < 3) {
      newErrors.comment = 'Комментарий должен содержать минимум 3 символа';
    } else if (formData.comment.length > 1000) {
      newErrors.comment = 'Комментарий не должен превышать 1000 символов';
    }

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
    setErrors({});

    try {
      const requestData = {
        topic: { name: formData.title.trim() },
        comment: {
          text: formData.comment.trim()
        }
      };

      if (uploadedFiles.length > 0) {
        requestData.comment.files_ids = uploadedFiles.map(f => f.id);
      }

      const responseData = await createTopicWithComment({ forumId, requestData }).unwrap();

      navigate(`/forum/${forumId}/topics`, {
        state: {
          forumName: formData.forumName,
          successMessage: 'Тема успешно создана!',
          newTopicData: responseData
        }
      });
    } catch (error) {
      console.error('Create topic error:', error);
      
      if (error?.status === 422) {
        setErrors({ general: 'Пожалуйста, проверьте правильность заполнения формы' });
      } else if (error?.status === 401 || error?.status === 403) {
        navigate('/forum/login', {
          state: {
            returnUrl: `/forum/${forumId}/create-topic`,
            forumId,
            forumName: formData.forumName
          }
        });
      } else {
        setErrors({ general: 'Ошибка создания темы. Попробуйте позже.' });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const UploadingFileItem = ({ file }) => (
    <div className={styles.fileItemUploading}>
      <span className={styles.fileItemName}>
        ⏳ {file.name} ({(file.size / 1024).toFixed(1)} KB)
      </span>
      <Spinner size="small" className={styles.fileSpinner} />
    </div>
  );

  const UploadedFileItem = ({ file, index, onRemove }) => (
    <div className={styles.fileItemUploaded}>
      <span className={styles.fileItemName}>
        ✅ {file.originalName || file.filename || file.name}
      </span>
      <button
        type="button"
        onClick={() => onRemove(file, index)}
        className={styles.removeFileButton}
        disabled={isLoading}
      >
        ×
      </button>
    </div>
  );

  if (!forumId) {
    return (
      <div className={styles.page}>
        <div className={styles.content}>
          <Card className={styles.createTopicCard}>
            <div className={styles.generalError}>
              Некорректная ссылка. Отсутствует ID форума.
            </div>
          </Card>
        </div>
      </div>
    );
  }

  if (!authChecked) {
    return (
      <div className={styles.page}>
        <div className={styles.content}>
          <Card className={styles.createTopicCard}>
            <div className={styles.loading}>
              <Spinner size="small" />
              <span>Проверка авторизации...</span>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <Card className={styles.createTopicCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Создание темы</h1>
            <h2 className={styles.subtitle}>{formData.forumName}</h2>
          </div>

          {errors.general && <div className={styles.generalError}>{errors.general}</div>}

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Название темы"
              type="text"
              name="title"
              placeholder="Введите название новой темы"
              value={formData.title}
              onChange={handleInputChange}
              error={errors.title}
              autoFocus
              disabled={isLoading}
            />

            <Textarea
              label="Первый комментарий"
              name="comment"
              placeholder="Введите текст первого комментария"
              value={formData.comment}
              onChange={handleInputChange}
              error={errors.comment}
              disabled={isLoading}
              rows={6}
              maxLength={1000}
              helperText={`${formData.comment.length}/1000 символов`}
            />

            {/* Прикрепление файлов */}
            <div className={styles.fileSection}>
              <label className={styles.fileLabel}>Прикрепить файлы</label>
              
              <div className={styles.fileUploadArea}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  multiple
                  accept="image/*,.pdf,.doc,.docx"
                  disabled={isLoading}
                  className={styles.fileInput}
                />
                
                <Button
                  variant="secondary"
                  size="medium"
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className={styles.fileUploadButton}
                  disabled={isLoading || uploadingFiles.length > 0}
                >
                  <span className={styles.uploadIcon}>
                    {uploadingFiles.length > 0 ? '⏳' : '📎'}
                  </span>
                  {uploadingFiles.length > 0 ? 'Загрузка...' : 'Выбрать файлы'}
                </Button>
                
                <span className={styles.fileHint}>
                  Поддерживаются изображения, PDF, DOC, DOCX
                </span>
              </div>

              {(uploadingFiles.length > 0 || uploadedFiles.length > 0) && (
                <div className={styles.filesPreview}>
                  <div className={styles.filesPreviewHeader}>
                    Прикрепленные файлы ({uploadingFiles.length + uploadedFiles.length})
                  </div>
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
                        onRemove={handleRemoveFile}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className={styles.actions}>
              <Button
                type="submit"
                variant="primary"
                size="large"
                disabled={isLoading}
                className={styles.submitButton}
              >
                {isLoading ? (
                  <>
                    <Spinner size="small" className={styles.buttonSpinner} />
                    Создание...
                  </>
                ) : 'Создать тему'}
              </Button>
            </div>
          </form>

          <div className={styles.footer}>
            <Button
              type="button"
              variant="link"
              onClick={() => navigate(`/forum/${forumId}/topics`, { state: { forumName: formData.forumName } })}
              className={styles.backButton}
              disabled={isLoading}
            >
              ← Вернуться к темам
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

const CreateTopicPage = withBaseMainPage(CreateTopicPageComponent);

export { CreateTopicPage };
