// DetachmentCharacterItem.jsx
import { useAutoFontSize } from '../../../../shared/hooks/ui/useAutoFontSize';
import { getRaceShield, getRaceDisplayName, getGenderDisplayName } from '../../config/race';
import styles from './CharacterDetachmentForm.module.css';

export const DetachmentCharacterItem = ({
  character,
  isSelected,
  isOnline,
  onSelect,
  calculateDetachCost,
}) => {
  const nameRef = useAutoFontSize(window.innerWidth - 300, 16, 5);
  const detachCost = calculateDetachCost(character);
  const race = character.race || character.race_type || '';
  const isMale = character.is_male !== undefined ? character.is_male : character.gender === 'male';
  const shieldIcon = getRaceShield(race, isMale);

  return (
    <div
      className={`${styles.characterItem} ${isSelected ? styles.selected : ''} ${
        isOnline ? styles.characterOnline : ''
      }`}
      onClick={() => !isOnline && onSelect(character)}
    >
      <div className={styles.characterInfo}>
        <div className={styles.characterDetails}>
          <div className={styles.characterNameContainer}>
            <span className={styles.characterName} ref={nameRef}>
              {character.name}
            </span>
            <span className={styles.characterLevel}>[{character.level}]</span>
            {isOnline && <span className={styles.onlineIndicator}>● Онлайн</span>}
          </div>
        </div>
        <div className={styles.characterShield}>
          {shieldIcon && (
            <img
              src={shieldIcon}
              alt={`${getRaceDisplayName(race)} ${getGenderDisplayName(isMale)}`}
              className={styles.shieldIcon}
              onError={(e) => (e.target.style.display = 'none')}
            />
          )}
        </div>
      </div>
      <div className={styles.characterCost}>
        <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> {detachCost} дт.
      </div>
    </div>
  );
};
