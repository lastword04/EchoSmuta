import { ProgressBar } from '../../../../shared/ui/ProgressBar/ProgressBar';
import { raceLabels, getRaceShield } from '../../config/race';
import { getLocationName } from '../../../../shared/config/locations/locations';
import SquarePattern from '../../../../shared/ui/SquarePattern/SquarePattern';
import { useCharacterImage } from '../../hooks/useCharacterImage';
import styles from './CharacterInfo.module.css';

export const CharacterInfo = ({ character }) => {
  const { info, additional_info, categories_stats } = character;
  const locationName = getLocationName(info.location_slug);

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

  const { 
    image: characterImage, 
    error: imageError,
    handleImageError,
  } = useCharacterImage(character?.info?.photo_id, 'portrait');

  return (
    <div className={styles.characterContainer}>
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
                  alt={info.name}
                  className={styles.characterImage}
                  onError={handleImageError}
                />
              </div>
            </div>
          )}
        </div>
        <div className={styles.characterProgress}>
          <ProgressBar
            current={info.health}
            max={info.max_health}
            label="Здоровье"
            color="green"
          />
          <ProgressBar
            current={Math.round(info.tiredness * 100)}
            max={100}
            label="Усталость"
            color="red"
          />
          <ProgressBar
            current={info.mana}
            max={info.max_mana}
            label="Мана"
            color="blue"
          />
        </div>
      </div>

      <div className={styles.characterInfoSection}>
        <div className={styles.characterHeader}>
          <h1 className={styles.characterName}>{info.name}</h1>
          <div className={styles.characterStatus}>
            <span className={`${styles.statusIndicator} ${info.is_online ? styles.online : styles.offline}`}>
              {info.is_online ? 'Онлайн' : 'Оффлайн'}
            </span>
            <span className={styles.characterType}>
              {info.is_main ? 'Основной' : 'Мульт'}
            </span>
          </div>
        </div>

        <div className={styles.characterRace}>
          <div className={styles.raceContent}>
            <span>Раса: {raceLabels[info.race] || info.race}</span>
            <img
              src={getRaceShield(info.race, info.is_male)}
              alt={`${info.race} ${info.is_male ? 'male' : 'female'} shield`}
              className={styles.raceShield}
            />
          </div>
        </div>

        <div className={styles.characterStats}>
          <h2>Характеристики</h2>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Сила:</span>
            <span className={styles.statValue}>{info.power}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Ловкость:</span>
            <span className={styles.statValue}>{info.agility}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Удача:</span>
            <span className={styles.statValue}>{info.lucky}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Опыт:</span>
            <span className={styles.statValue}>{info.experience}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Уровень:</span>
            <span className={styles.statValue}>{info.level}</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Побед:</span>
            <span className={styles.statValue}>0</span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Поражений:</span>
            <span className={styles.statValue}>0</span>
          </div>
        </div>

        <div className={styles.locationInfo}>
          Персонаж находится в окрестностях города Авалон ({locationName})
        </div>

        <div className={styles.personalInfo}>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Имя:</span>
            <span className={styles.infoValue}>{additional_info?.name || ''}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Страна:</span>
            <span className={styles.infoValue}>{additional_info?.country || ''}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Город:</span>
            <span className={styles.infoValue}>{additional_info?.city || ''}</span>
          </div>
          <div className={styles.infoRow}>
            <span className={styles.infoLabel}>Раса:</span>
            <span className={styles.infoValue}>{raceLabels[info.race] || info.race}</span>
          </div>
        </div>

        <div className={styles.friendsEnemies}>
          <div className={styles.countRow}>
            <span>{categories_stats.friends_count} Персонажей считают меня другом</span>
          </div>
          <div className={styles.countRow}>
            <span>{categories_stats.enemies_count} Персонажей считают меня врагом</span>
          </div>
        </div>

        <div className={styles.aboutSection}>
          <h3>О себе</h3>
          <div className={styles.aboutContent}>
            {additional_info?.info || ''}
          </div>
        </div>
      </div>
    </div>
  );
};