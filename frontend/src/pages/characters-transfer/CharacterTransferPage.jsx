import { useNavigate } from 'react-router-dom';
import { CharacterTransferForm } from '../../entities/character/ui/CharacterTransferForm/CharacterTransferForm';
import { 
  useGetMyCharactersQuery,
  useGetTransferRulesQuery 
} from '../../entities/character/api/characterApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './CharacterTransferPage.module.css';

const CharacterTransferComponentPage = () => {
  const navigate = useNavigate();

  const { data: characters = [], isError: isCharactersError, error: charactersError } = useGetMyCharactersQuery();
  const { data: transferRules } = useGetTransferRulesQuery();

  if (isCharactersError && (charactersError?.status === 401 || charactersError?.status === 403)) {
    navigate('/login', {
      state: { authRequired: 'Для доступа к этой странице требуется авторизация' }
    });
    return null;
  }

  const handleSuccess = () => {
    // Ничего не делаем — RTK Query сам обновит кэш MyCharacters через invalidatesTags
  };

  const handleCancel = () => {
    navigate('/characters?tab=characters');
  };

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <CharacterTransferForm
          onSuccess={handleSuccess}
          onCancel={handleCancel}
          characters={characters}
          transferRules={transferRules}
        />
      </div>
    </div>
  );
};

const CharacterTransferPage = withBaseMainPage(CharacterTransferComponentPage);

export { CharacterTransferPage };