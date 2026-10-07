import SquarePattern from '../../shared/ui/SquarePattern/SquarePattern';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import { useAutoFontSize } from '../../shared/hooks/ui/useAutoFontSize';
import styles from './CharacterPanel.module.css';

export const MobileCharacterPanel = ({ character, characterImage, imageError, handleImageError, squareConfig, isShowUpSkills, handleUpSkillsButtonClick }) => {
  const nameMobileRef = useAutoFontSize(window.innerWidth - 10, 16, 10);

 
  // Эффективные статы: берём готовые с бэка, а если их нет (первый рендер) — считаем локально по базе + экипировке
  const equipmentBonuses = character?.equipment_bonuses || {};

  const effectivePower = character?.effective_power
    ?? ((character?.power || 0) + (equipmentBonuses.strength_bonus || 0));
  const effectiveAgility = character?.effective_agility
    ?? ((character?.agility || 0) + (equipmentBonuses.agility_bonus || 0));
  const effectiveLucky = character?.effective_lucky
    ?? ((character?.lucky || 0) + (equipmentBonuses.luck_bonus || 0));
  const effectiveMaxHealth = character?.effective_max_health
    ?? ((character?.max_health || 0) + (equipmentBonuses.max_health_bonus || 0));
  const effectiveMaxMana = character?.effective_max_mana
    ?? ((character?.max_mana || 0) + (equipmentBonuses.max_mana_bonus || 0));
  const effectiveMaxTiredness = character?.effective_max_tiredness
    ?? (1.0 + (equipmentBonuses.max_tiredness_bonus || 0));


  return (
    <div className={`${styles.characterPanel} ${styles.mobileCharacterPanel}`}>
      <div className={`${styles.characterContent} ${styles.mobileCharacterContent}`}>
        <div className={`${styles.characterInfo} ${styles.mobileCharacterInfo}`}>
          <h2 ref={nameMobileRef} className={styles.mobileCharacterName} onClick={() => window.open(`/characters/${character.id}`, '_blank')}>{character.name}</h2>

          <div className={styles.mobileTopRow}>
            <div className={styles.mobileLeftColumn}>
              <div className={`${styles.characterImageContainer} ${styles.mobileCharacterImageContainer}`}>
                {imageError || !characterImage ? (
                  <div className={`${styles.characterImageBackground} ${styles.mobileCharacterImageBackground}`}>
                    <SquarePattern className={styles.squares} squares={squareConfig} />
                    <div className={`${styles.imageWrapper} ${styles.mobileImageWrapper}`}>
                      <div className={`${styles.imagePlaceholder} ${styles.mobileImagePlaceholder}`}>
                        <span>?</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`${styles.characterImageBackground} ${styles.mobileCharacterImageBackground}`}>
                    <SquarePattern className={styles.squares} squares={squareConfig} />
                    <div className={`${styles.imageWrapper} ${styles.mobileImageWrapper}`}>
                      <img 
                        src={characterImage}
                        alt={character.name}
                        className={`${styles.characterImage} ${styles.mobileCharacterImage}`}
                        onError={handleImageError}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className={styles.mobileCharacterProgress}>
                <ProgressBar 
                  current={character.health} 
                  max={effectiveMaxHealth} 
                  label="Здоровье" 
                  color="green"
                />
                <ProgressBar 
                  current={Math.round(character.tiredness * 100)} 
                  max={Math.round(effectiveMaxTiredness * 100)} 
                  label="Усталость" 
                  color="red"
                />
                <ProgressBar 
                  current={character.mana} 
                  max={effectiveMaxMana} 
                  label="Мана" 
                  color="blue"
                />
              </div>
            </div>

            <div className={`${styles.characterStats} ${styles.mobileCharacterStats}`}>
              <h4 className={styles.mobileStatsTitle}>Характеристики</h4>

              <div className={`${styles.statsGrid} ${styles.mobileStatsGrid}`}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Сила:</span>
                  <span className={styles.statValue}>{effectivePower}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Ловкость:</span>
                  <span className={styles.statValue}>{effectiveAgility}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Удача:</span>
                  <span className={styles.statValue}>{effectiveLucky}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Выносливость:</span>
                  <span className={styles.statValue}>{character?.endurance || 0}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Интеллект:</span>
                  <span className={styles.statValue}>{character?.intelligence || 0}</span>
                </div>
              </div>

              <div className={`${styles.additionalStats} ${styles.mobileAdditionalStats}`}>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Опыт:</span>
                  <span className={styles.statValue}>{character.experience}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Уровень:</span>
                  <span className={styles.statValue}>{character.level}</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Побед:</span>
                  <span className={styles.statValue}>0</span>
                </div>
                <div className={styles.statItem}>
                  <span className={styles.statLabel}>Поражений:</span>
                  <span className={styles.statValue}>0</span>
                </div>
              </div>

              <div className={`${styles.balance} ${styles.mobileBalance}`}>
                <div className={styles.statItem}>
                  <div className={styles.balanceItem}>
                    <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                    <span>{Number(character?.ducats ?? 0).toFixed(2)} дт.</span>
                  </div>
                </div>
                {character.gold > 0 && (
                  <div className={styles.statItem}>
                    <div className={styles.balanceItem}>
                      <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} />
                      <span>{Number(character?.gold ?? 0).toFixed(2)} злт.</span>                      
                    </div>
                  </div>
                )}
              </div>

              {isShowUpSkills && (
                <div className={styles.skillsSection}>
                  <span className={styles.skillsText} onClick={handleUpSkillsButtonClick}>Улучшения</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};