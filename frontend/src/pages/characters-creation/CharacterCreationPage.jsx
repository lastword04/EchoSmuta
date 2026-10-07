import { useNavigate } from 'react-router-dom';
import { CharacterCreationForm } from '../../entities/character/ui/CharacterCreationForm/CharacterCreationForm';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';

import styles from './CharacterCreationPage.module.css';

const CharacterCreationComponentPage = () => {
  const navigate = useNavigate();

  const handleSuccess = () => {
    navigate('/characters?tab=characters');
  };

  const handleCancel = () => {
    navigate('/characters?tab=characters');
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.content}>
        <CharacterCreationForm
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </div>
    </div>
  );
};

const CharacterCreationPage = withBaseMainPage(CharacterCreationComponentPage);

export { CharacterCreationPage };