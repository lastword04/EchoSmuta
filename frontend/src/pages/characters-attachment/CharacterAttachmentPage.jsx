import { useNavigate } from 'react-router-dom';
import { CharacterAttachmentForm } from '../../entities/character/ui/CharacterAttachmentForm/CharacterAttachmentForm';
import { 
  useGetMyCharactersQuery, 
  useGetCharacterCreationStatusQuery,
  useGetAttachmentSettingsQuery
} from '../../entities/character/api/characterApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './CharacterAttachmentPage.module.css';

const CharacterAttachmentComponentPage = () => {
  const navigate = useNavigate();

  const { data: characters = [], isError: isCharactersError, error: charactersError } = useGetMyCharactersQuery();
  const { data: creationStatus = { max_characters: 0 } } = useGetCharacterCreationStatusQuery();
  const { data: attachmentSettings } = useGetAttachmentSettingsQuery();

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
        <CharacterAttachmentForm
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

const CharacterAttachmentPage = withBaseMainPage(CharacterAttachmentComponentPage);

export { CharacterAttachmentPage };