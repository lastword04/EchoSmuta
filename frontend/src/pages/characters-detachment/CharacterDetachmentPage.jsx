import { useNavigate } from 'react-router-dom';
import { CharacterDetachmentForm } from '../../entities/character/ui/CharacterDetachmentForm/CharacterDetachmentForm';
import { useGetMyCharactersQuery, useGetCharacterCreationStatusQuery, useGetAttachmentSettingsQuery } from '../../entities/character/api/characterApi'; // Проверь путь к characterApi
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './CharacterDetachmentPage.module.css';

const CharacterDetachmentComponentPage = () => {
  const navigate = useNavigate(); 

  // Мгновенный рендер: используем дефолтные значения, чтобы не блокировать UI  
  const { data: characters = [], isError: isCharactersError, error: charactersError } = useGetMyCharactersQuery();
  const { data: creationStatus = { max_characters: 0 } } = useGetCharacterCreationStatusQuery();
  const { data: attachmentSettings } = useGetAttachmentSettingsQuery();

  // Если базовый query не перехватывает 401/403 глобально, обрабатываем здесь
  if (isCharactersError && (charactersError?.status === 401 || charactersError?.status === 403)) {
    navigate('/login', {
      state: { authRequired: 'Для доступа к этой странице требуется авторизация' }
    });
    return null;
  }

  const handleSuccess = () => {
    navigate('/characters?tab=characters');
  };

  const handleCancel = () => {
    navigate('/characters?tab=characters');
  };

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <CharacterDetachmentForm
          onSuccess={handleSuccess}
          onCancel={handleCancel}
          characters={characters}
          maxCharacters={creationStatus.max_characters}
          attachmentSettings={attachmentSettings}
        />
      </div>
    </div>
  );
};

const CharacterDetachmentPage = withBaseMainPage(CharacterDetachmentComponentPage);

export { CharacterDetachmentPage };