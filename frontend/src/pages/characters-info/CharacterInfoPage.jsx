import { useParams } from 'react-router-dom';
import { useGetCharacterQuery } from '../../entities/character/api/characterApi';
import { CharacterInfo } from '../../entities/character/ui/CharacterInfo/CharacterInfo';
import styles from './CharacterInfoPage.module.css';

export const CharacterInfoPage = () => {
  const { characterId } = useParams();
  const { data: character, isError } = useGetCharacterQuery(characterId, {
    skip: !characterId,
  });

  if (isError) {
    return (
      <div className={styles.page}>
        <div className={styles.errorContainer}>
          <span className={styles.errorText}>Не удалось загрузить данные персонажа</span>
        </div>
      </div>
    );
  }

  // Атомарный рендер: пока нет данных — ничего не рисуем.
  // Никакого спиннера — как только придут данные, CharacterInfo отрисуется сразу.
  if (!character) {
    return null;
  }

  return (
    <div className={styles.page}>
      <CharacterInfo character={character} />
    </div>
  );
};