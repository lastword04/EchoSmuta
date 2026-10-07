import { useAutoFontSize } from '../../../../shared/hooks/ui/useAutoFontSize';
import { useCharacterImage } from '../../hooks/useCharacterImage';
import { useMediaQuery } from '../../../../shared/hooks/ui/useMediaQuery';
import { getRaceShield, getRaceDisplayName, getGenderDisplayName } from '../../config/race';
import SquarePattern from '../../../../shared/ui/SquarePattern/SquarePattern';
import styles from './AttachmentCharacterItem.module.css';

export const AttachmentCharacterItem = ({
  character,
  isSelected,
  onSelect,
  calculateAttachCost,
}) => {
  const isMobile = useMediaQuery('(max-width: 950px)');
  const isSMobile = useMediaQuery('(max-width: 360px)');
  
  // Адаптив для длинных ников
  const nameRef = useAutoFontSize(isMobile ? window.innerWidth - 300 : window.innerWidth - 300, isMobile ? 16 : 16, isMobile ? 4 : 5, isMobile ? 0 : undefined);

  // Загрузка изображения персонажа
  const { 
    image: characterImage,     
    error: imageError,
    handleImageError,
  } = useCharacterImage(character?.photo_id);

  const attachCost = calculateAttachCost(character);
  const race = character.race || character.race_type || '';
  const isMale = character.is_male !== undefined ? character.is_male : character.gender === 'male';
  const shieldIcon = getRaceShield(race, isMale);

  const squareMobileSize = isSMobile ? 20 : 27;

  const squareConfig = [
    { content: null },
    { content: null },
    { className: 'invisibleSquare', content: null },
    { className: 'invisibleSquare', content: null },
    { content: null },
    { content: null },
    { content: null },
    { content: null },
  ];

  // Мобильная версия
  if (isMobile) {
    return (
      <div
        className={`${styles.characterItem} ${styles.mobileCharacterItem} ${isSelected ? styles.selected : ''}`}
        onClick={() => onSelect(character)}
      >
        {/* Верхняя часть: имя, уровень, щит, стоимость */}
        <div className={styles.mobileHeader}>
          <div className={styles.mobileMainInfo}>
            <span className={styles.mobileName} ref={nameRef}>
              {character.name}
            </span>
            <span className={styles.mobileLevel}>[{character.level}]</span>
            <div className={styles.mobileShield}>
              {shieldIcon && (
                <img
                  src={shieldIcon}
                  alt={`${getRaceDisplayName(race)} ${getGenderDisplayName(isMale)}`}
                  className={styles.mobileShieldIcon}
                  onError={(e) => (e.target.style.display = 'none')}
                />
              )}
            </div>
          </div>
          <div className={styles.mobileCost}>
            <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} />
            {attachCost}
          </div>
        </div>

        {/* Основной контент: фото и характеристики */}
        <div className={styles.mobileContent}>
          {/* Левая часть: фото */}
          <div className={styles.mobileImageSection}>
            <div className={styles.characterImageContainer}>
              {imageError || !characterImage ? (
                <div className={styles.characterImageBackground}>
                  <SquarePattern className={styles.squares} squares={squareConfig} squareSize={squareMobileSize} />
                  <div className={styles.imageWrapper}>
                    <div className={styles.imagePlaceholder}>
                      <span>?</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={styles.characterImageBackground}>
                  <SquarePattern className={styles.squares} squares={squareConfig} squareSize={squareMobileSize} />
                  <div className={styles.imageWrapper}>
                    <img 
                      src={characterImage}
                      alt={character.name}
                      className={styles.characterImage}
                      onError={handleImageError}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Правая часть: характеристики */}
          <div className={styles.mobileStatsSection}>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Сила:</span>
              <span className={styles.statValue}>{character.power || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Ловкость:</span>
              <span className={styles.statValue}>{character.agility || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Удача:</span>
              <span className={styles.statValue}>{character.lucky || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Выносливость:</span>
              <span className={styles.statValue}>{character.endurance || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Интеллект:</span>
              <span className={styles.statValue}>{character.intelligence || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Опыт:</span>
              <span className={styles.statValue}>{character.experience || 0}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statValue}>
                <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                {character.ducats || 0} дт.
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Десктопная версия
  return (
    <div
      className={`${styles.characterItem} ${isSelected ? styles.selected : ''}`}
      onClick={() => onSelect(character)}
    >
      {/* Верхняя часть: имя, уровень, щит, стоимость */}
      <div className={styles.characterHeader}>
        <div className={styles.characterMainInfo}>
          <span className={styles.characterName} ref={nameRef}>
            {character.name}
          </span>
          <span className={styles.characterLevel}>[{character.level}]</span>
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
          <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} />
          {attachCost} злт.
        </div>
      </div>

      {/* Основной контент: фото и характеристики */}
      <div className={styles.characterContent}>
        {/* Левая часть: фото */}
        <div className={styles.characterImageSection}>
          <div className={styles.characterImageContainer}>
            {imageError || !characterImage ? (
              <div className={styles.characterImageBackground}>
                <SquarePattern className={styles.squares} squares={squareConfig} />
                <div className={styles.imageWrapper}>
                  <div className={styles.imagePlaceholder}>
                    <span>?</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className={styles.characterImageBackground}>
                <SquarePattern className={styles.squares} squares={squareConfig} />
                <div className={styles.imageWrapper}>
                  <img 
                    src={characterImage}
                    alt={character.name}
                    className={styles.characterImage}
                    onError={handleImageError}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Правая часть: характеристики */}
        <div className={styles.characterStatsSection}>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Сила:</span>
            <span className={styles.statValue}>{character.strength || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Ловкость:</span>
            <span className={styles.statValue}>{character.dexterity || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Удача:</span>
            <span className={styles.statValue}>{character.luck || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Выносливость:</span>
            <span className={styles.statValue}>{character.endurance || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Интеллект:</span>
            <span className={styles.statValue}>{character.intelligence || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Опыт:</span>
            <span className={styles.statValue}>{character.experience || 0}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statValue}>
              <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
              {character.ducats || 0} дт.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};