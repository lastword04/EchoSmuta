import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { inventoryApi } from '../../../items/api/inventoryApi';
import { characterApi } from '../../api/characterApi';
import { characterStatsApi } from '../../api/characterStatsApi';
import { economyApi } from '../../../economy/api/economyApi';
import { usePlayMutation, useQuitMutation } from '../../../auth/api/authGameApi';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { useMediaQuery } from '../../../../shared/hooks/ui/useMediaQuery';
import { useAutoFontSize } from '../../../../shared/hooks/ui/useAutoFontSize';
import { useCharacterImage } from '../../hooks/useCharacterImage';
import { MobileProgressBar } from '../../../../shared/ui/MobileProgressBar/MobileProgressBar';
import SquarePattern from '../../../../shared/ui/SquarePattern/SquarePattern';
import { raceLabels, getRaceShield } from '../../config/race';
import { setActiveCharacterName } from '../../../../shared/store/activeCharacterNameSlice';
import { setActiveCharacterId, clearActiveCharacterId } from '../../../../shared/store/activeCharacterIdSlice';
import visitService from '../../../../shared/services/visitService';
import { clearLastMining } from '../../../../entities/resources/store/miningSlice';
import styles from './CharacterCard.module.css';

// Компонент для мобильного имени с динамическим размером шрифта
const MobileCharacterName = ({ name, isMain }) => {
  const mobileNameRef = useAutoFontSize(window.innerWidth - 300, 16, 10, 0);
  
  return (
    <span 
      ref={mobileNameRef}
      className={styles.mobileName}
      style={{
        fontWeight: isMain ? 'bold' : 'normal'
        /*'var(--red-accent, #ff4d4d)' : 'var(--light-gold)'*/
      }}
    >
      {name}
    </span>
  );
};

export const CharacterCard = ({ character, onCharacterUpdated }) => {
  const [characterState, setCharacterState] = useState(character);
  const [isExiting, setIsExiting] = useState(false);

  const dispatch = useDispatch();
  const [play] = usePlayMutation();
  const [quit] = useQuitMutation();

  const navigate = useNavigate();
  const isMobile = useMediaQuery('(max-width: 650px)');
  const isSMobile = useMediaQuery('(max-width: 360px)');
  const squareMobileSize = isSMobile ? 20 : 27;

  const { 
    image: characterImage,     
    error: imageError,
    handleImageError,
  } = useCharacterImage(characterState?.photo_id);
  // Ref для автоматического изменения размера шрифта (только для десктопа)
  const desktopNameRef = useAutoFontSize(0, 18, 10, 20);

  // Обновляем состояние персонажа при изменении пропсов
  useEffect(() => {
    setCharacterState(character);
  }, [character]); 
  

  const handlePlay = async () => {
    try {
      const fingerprint = await visitService.getFingerprint();
      const data = {
        fingerprint: fingerprint
      };
      
      const inGameCharacter = await play({ characterId: characterState.id, data }).unwrap();

      dispatch(inventoryApi.util.resetApiState());
      dispatch(characterApi.util.resetApiState());
      dispatch(characterStatsApi.util.resetApiState());
      dispatch(economyApi.util.resetApiState());
      dispatch(setActiveCharacterName(inGameCharacter.name));
      dispatch(setActiveCharacterId(inGameCharacter.id));
      navigate("/location");
    } catch (error) {
      console.error('Error playing character:', error);
      alert('Ошибка входа в игру');
    }
  };

  const handleExit = async () => {
    try {
      setIsExiting(true);
      if (characterState && characterState.id) {
        const fingerprint = await visitService.getFingerprint();
        const data = {
          fingerprint: fingerprint
        };
        await quit({ characterId: characterState.id, data }).unwrap();
        
        const updatedCharacter = {
          ...characterState,
          is_online: false
        };
        setCharacterState(updatedCharacter);
        // Персонаж больше не в игре — логика игр/хуков рассчитывает на null.
        // Имя НЕ очищаем: оно нужно только для приветствия в кабинете.
        dispatch(clearActiveCharacterId());
        // Точечная инвалидация вместо полного сброса кэша:
        // кабинет НЕ мигает, список персонажей дообновится фоном
        dispatch(characterApi.util.invalidateTags(['MyCharacters', 'Character']));
        dispatch(inventoryApi.util.resetApiState());
        dispatch(characterStatsApi.util.resetApiState());
        dispatch(economyApi.util.resetApiState());
        dispatch(clearLastMining());   
        
        if (onCharacterUpdated) {
          onCharacterUpdated(updatedCharacter);
        }
      }
    } catch (error) {
      console.error('Ошибка при выходе:', error);
      alert('Ошибка выхода из игры');
    } finally {
      setIsExiting(false);
    }
  };

  const ProgressBar = ({ current, max, label, color = 'blue' }) => {
    const percentage = max > 0 ? (current / max) * 100 : 0;
    
    return (
      <div className={styles.progressBarContainer}>
        <div className={styles.progressLabel}>
          <span>{label}</span>
          <span>{current}/{max}</span>
        </div>
        <div className={styles.progressBar}>
          <div 
            className={`${styles.progressFill} ${styles[`progress-${color}`]}`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };

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

  // Мобильная версия карточки
  if (isMobile) {
    return (
      <Card className={`${styles.characterCard} ${styles.mobileCharacterCard}`}>
        <div className={styles.mobileHeader}>
          <div className={styles.mobileStatusInfo}>
            <div 
              className={`${styles.mobileStatusIndicator} ${characterState.is_online ? styles.online : styles.offline}`}
              style={{ width: '12px', height: '12px', minWidth: '12px', padding: 0 }}
            ></div>
            <div className={styles.mobileNameInfo}>
              <div className={styles.mobileNameWrapper}>
                <MobileCharacterName 
                  name={characterState.name} 
                  isMain={characterState.is_main} 
                />
              </div>
              <span className={styles.mobileLevel}>[{characterState.level}]</span>
              <img 
                src={getRaceShield(characterState.race, characterState.is_male)}
                alt={`${characterState.race} shield`}
                className={styles.mobileRaceShield}
              />
            </div>
          </div>
          <div className={styles.mobileActions}>
            <button 
              className={styles.mobileActionButton}
              onClick={handlePlay}
              title="Войти в игру"
            >
              <img src="/images/character/game/play-game.png" alt="Войти" />
            </button>
            {characterState.is_online && (
              <button 
                className={styles.mobileActionButton}
                onClick={handleExit}
                disabled={isExiting}
                title="Выйти из игры"
                style={{ opacity: isExiting ? 0.6 : 1 }}
              >
                <img src="/images/character/game/exit-game.png" alt="Выйти" />
              </button>
            )}
          </div>
        </div>

        <div className={styles.mobileContent}>
          <div className={styles.mobileImageSection}>
            <div className={styles.characterImageContainer}>
              {imageError || !characterImage ? (
                <div className={styles.characterImageBackground}>
                  <SquarePattern className={styles.squares} squares={squareConfig} squareSize={squareMobileSize}/>
                  <div className={styles.imageWrapper}>
                    <div className={styles.imagePlaceholder}>
                      <span>?</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={styles.characterImageBackground}>
                  <SquarePattern className={styles.squares} squares={squareConfig} squareSize={squareMobileSize}/>
                  <div className={styles.imageWrapper}>
                    <img 
                      src={characterImage}
                      alt={characterState.name}
                      className={styles.characterImage}
                      onError={handleImageError}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className={styles.mobileStatsSection}>
            <div className={styles.mobileStatsContainer}>
              <div className={styles.mobileStatItem}>
                <span className={styles.statLabel}>Опыт:</span>
                <span className={styles.statValue}>{characterState.experience}</span>
              </div>
              <div className={styles.mobileStatItem}>
                <span className={styles.statLabel}>До апа:</span>
                <span className={styles.statValue}>0</span>
              </div>
              <div className={styles.mobileStatItem}>
                <span className={styles.statValue}>
                  <img src="/images/currency/dt.png" alt="" className={styles.currencyIcon} />
                  {characterState.ducats} дт.
                </span>
              </div>
              <div className={styles.mobileStatItem}>
                <span className={styles.statValue}>
                  <img src="/images/currency/gld.png" alt="" className={styles.currencyIcon} />
                  {characterState.gold} злт.
                </span>
              </div>
            </div>
            
            <div className={styles.mobileProgressBars}>
              <MobileProgressBar 
                current={characterState.health} 
                max={characterState.effective_max_health ?? ((characterState.max_health || 0) + (characterState.equipment_bonuses?.max_health_bonus || 0))}
                label="Здоровье" 
                color="green"
              />
              <MobileProgressBar 
                current={Math.round(characterState.tiredness * 100)} 
                max={Math.round((characterState.effective_max_tiredness ?? ((characterState.max_tiredness || 0) + (characterState.equipment_bonuses?.max_tiredness_bonus || 0))) * 100)}
                label="Усталость" 
                color="red"
              />
              <MobileProgressBar 
                current={characterState.mana}
                max={characterState.effective_max_mana ?? ((characterState.max_mana || 0) + (characterState.equipment_bonuses?.max_mana_bonus || 0))}
                label="Мана" 
                color="blue"
              />
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Десктопная версия
  return (
    <Card className={styles.characterCard}>
      <div className={styles.characterHeader}>
        <h3 ref={desktopNameRef} className={styles.characterName} title={characterState.name}>
          {characterState.name}
        </h3>
        
        <div className={styles.characterStatus}>
          <span className={`${styles.statusIndicator} ${characterState.is_online ? styles.online : styles.offline}`}>
            {characterState.is_online ? 'Онлайн' : 'Оффлайн'}
          </span>
          <span className={styles.characterType}>
            {characterState.is_main ? 'Основной' : 'Мульт'}
          </span>
        </div>
      </div>

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
                alt={characterState.name}
                className={styles.characterImage}
                onError={handleImageError}
              />
            </div>
          </div>
        )}
      </div>

      <div className={styles.characterRace}>
        <div className={styles.raceContent}>
          <span>Раса: {raceLabels[characterState.race] || characterState.race}</span>
          <img 
            src={getRaceShield(characterState.race, characterState.is_male)}
            alt={`${characterState.race} ${characterState.is_male ? 'male' : 'female'} shield`}
            className={styles.raceShield}
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'inline';
            }}
          />
          <span 
            className={styles.fallbackGender}
            style={{ display: 'none' }}
          >
            {characterState.is_male ? ' ♂' : ' ♀'}
          </span>
        </div>
      </div>

      <div className={styles.characterStats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Уровень:</span>
          <span className={styles.statValue}>{characterState.level}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Опыт:</span>
          <span className={styles.statValue}>{characterState.experience}</span>
        </div>
        
        <ProgressBar 
          current={characterState.health} 
          max={characterState.effective_max_health ?? ((characterState.max_health || 0) + (characterState.equipment_bonuses?.max_health_bonus || 0))}
          label="Здоровье" 
          color="green"
        />

        <ProgressBar 
          current={Math.round(characterState.tiredness * 100)} 
          max={Math.round((characterState.effective_max_tiredness ?? ((characterState.max_tiredness || 0) + (characterState.equipment_bonuses?.max_tiredness_bonus || 0))) * 100)}
          label="Усталость" 
          color="red"
        />

        <ProgressBar 
          current={characterState.mana} 
          max={characterState.effective_max_mana ?? ((characterState.max_mana || 0) + (characterState.equipment_bonuses?.max_mana_bonus || 0))}
          label="Мана" 
          color="blue"
        />
        
        <div className={styles.stat}>
          <span className={styles.statLabel}>Дукаты:</span>
          <span className={styles.statValue}>{characterState.ducats}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Золото:</span>
          <span className={styles.statValue}>{characterState.gold}</span>
        </div>
      </div>

      <div className={styles.characterActions}>
        <Button
          variant="primary"
          size="medium"
          onClick={handlePlay}
          className={styles.playButton}
        >
          В игру
        </Button>
        
        {characterState.is_online && (
          <Button
            variant="secondary"
            size="medium"
            onClick={handleExit}
            disabled={isExiting}
            className={styles.exitButton}
            style={{ opacity: isExiting ? 0.6 : 1 }}
          >
            Выйти из игры
          </Button>
        )}
      </div>
    </Card>
  );
};