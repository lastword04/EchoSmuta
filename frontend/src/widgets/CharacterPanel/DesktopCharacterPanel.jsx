import SquarePattern from '../../shared/ui/SquarePattern/SquarePattern';
import { MenuItem } from '../../shared/ui/MenuItem/MenuItem';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import { menuItems } from '../../shared/config/ui/menuItems';
import { useAutoFontSize } from '../../shared/hooks/ui/useAutoFontSize';
import { usePanelSelection } from './hooks/usePanelSelection';
import styles from './CharacterPanel.module.css';

export const DesktopCharacterPanel = ({ 
  character, 
  characterImage,     
  imageError, 
  handleImageError,
  squareConfig,
  showMenu,  
  menuRef,
  handleControlButtonMouseEnter,
  handleControlButtonMouseLeave,
  handleControlButtonClick,
  handleMenuMouseEnter,
  handleMenuMouseLeave,
  handleMenuItemClickInternal,   
  isShowUpSkills,
  handleUpSkillsButtonClick
}) => {
  const nameRef = useAutoFontSize(280, 16, 10);

  const { handleCheckboxChange, isItemChecked } = usePanelSelection();
  

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
    <div className={styles.characterPanel}>
      <div className={styles.headerContainer}>
        <h2 ref={nameRef} className={styles.characterName} onClick={() => window.open(`/characters/${character?.id}`, '_blank')}>{character?.name}</h2>
        <div className={styles.controlContainer} ref={menuRef}>
          <button 
            className={styles.controlButton}
            onMouseEnter={handleControlButtonMouseEnter}
            onMouseLeave={handleControlButtonMouseLeave}
            onClick={handleControlButtonClick}
          >
            <span>Управление</span>
          </button>
          
          {showMenu && (
            <div 
              className={styles.dropdownMenu}
              onMouseEnter={handleMenuMouseEnter}
              onMouseLeave={handleMenuMouseLeave}
            >
              {
                menuItems.map((menuItem) => (
                  <MenuItem
                    key={menuItem.id}
                    item={menuItem}
                    onClick={handleMenuItemClickInternal}
                    onMouseEnter={handleMenuMouseEnter}
                    onMouseLeave={handleMenuMouseLeave}
                    isChecked={isItemChecked(menuItem.id)}
                    onCheckboxChange={handleCheckboxChange}                    
                  />
                ))
              }
            </div>
          )}
        </div>
      </div>

      <div className={styles.characterContent}>
        <div className={styles.characterInfo}>
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
                    alt={character?.name}
                    className={styles.characterImage}
                    onError={handleImageError}
                  />
                </div>
              </div>
            )}
          </div>

          <div className={styles.characterProgress}>
            <ProgressBar 
              current={character?.health} 
              max={effectiveMaxHealth} 
              label="Здоровье" 
              color="green"
            />
            <ProgressBar 
              current={Math.round(character?.tiredness * 100)} 
              max={Math.round(effectiveMaxTiredness * 100)} 
              label="Усталость" 
              color="red"
            />
            <ProgressBar 
              current={character?.mana} 
              max={effectiveMaxMana} 
              label="Мана" 
              color="blue"
            />
          </div>
        </div>

        <div className={styles.characterStats}>
          <h3>Характеристики</h3>
          
          <div className={styles.statsGrid}>
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

          <div className={styles.additionalStats}>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Опыт:</span>
              <span className={styles.statValue}>{character?.experience}</span>
            </div>
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Уровень:</span>
              <span className={styles.statValue}>{character?.level}</span>
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
          
          <div className={styles.balance}>
            <div className={styles.statItem}>
              <div className={styles.balanceItem}>
                <img src="/images/currency/dt.png" alt="дт." className={styles.currencyIcon} />
                <span>{Number(character?.ducats ?? 0).toFixed(2)} дт.</span>
              </div>
            </div>
            {character?.gold > 0 && (
              <div className={styles.statItem}>
                <div className={styles.balanceItem}>
                  <img src="/images/currency/gld.png" alt="злт." className={styles.currencyIcon} />
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
  );
};