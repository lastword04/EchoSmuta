import { useAutoFontSize } from '../../../../shared/hooks/ui/useAutoFontSize';
import { getRaceShield, getRaceDisplayName, getGenderDisplayName  } from '../../config/race';
import styles from './CharacterTransferForm.module.css';


export const CharacterTransferItem = ({ character, isSelected, onSelect }) => {
  // адаптивный размер шрифта имени персонажа
  const nameRef = useAutoFontSize(window.innerWidth - 250, 18, 5, 0);

  const shieldIcon = getRaceShield(character.race, character.is_male);

  return (
    <div
      className={`${styles.characterItem} ${isSelected ? styles.selected : ''}`}
      onClick={onSelect}
    >
      <div className={styles.characterHeader}>
        <span ref={nameRef} className={styles.characterName}>
          {character.name}
        </span>
        <span className={styles.characterLevel}>[{character.level}]</span>
        {shieldIcon && (
          <img
            src={shieldIcon}
            alt={`${getRaceDisplayName(character.race)} ${getGenderDisplayName(character.is_male)}`}
            className={styles.shieldIcon}
            onError={(e) => (e.target.style.display = 'none')}
          />
        )}
      </div>
    </div>
  );
};
