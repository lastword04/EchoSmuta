import { MenuItemsList } from './MenuItemsList';
import { usePanelSelection } from '../CharacterPanel/hooks/usePanelSelection';
import styles from './MobileMenu.module.css';

export const MobileMenu = ({ character, onMenuItemClick, onExit, isShowUpSkills,
  handleUpSkillsButtonClick }) => {
  const { handleCheckboxChange } = usePanelSelection();

  const handleMenuItemClick = (menuItem) => {
    if (onMenuItemClick) {
      onMenuItemClick(menuItem);
    }
  };

  // Эффективные статы (та же логика, что в панелях)
  const equipmentBonuses = character?.equipment_bonuses || {};

  const effectivePower = character?.effective_power
    ?? ((character?.power || 0) + (equipmentBonuses.strength_bonus || 0));
  const effectiveAgility = character?.effective_agility
    ?? ((character?.agility || 0) + (equipmentBonuses.agility_bonus || 0));
  const effectiveLucky = character?.effective_lucky
    ?? ((character?.lucky || 0) + (equipmentBonuses.luck_bonus || 0));


  return (
    <div className={styles.mobileMenu}>
      <div className={styles.mobileList}>
        <div className={styles.menuLeft}>
          <h4>Управление</h4>
          <MenuItemsList 
            onMenuItemClick={handleMenuItemClick}
            onCheckboxChange={handleCheckboxChange}
          />
        </div>
      
        <div className={styles.menuRight}>
          <h4>Характеристики</h4>
          <div className={styles.characterStats}>
            <div className={styles.onlyStats}>
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
      <div className={styles.footer}>    
        <button 
            className={styles.mobileExitButton}
            onClick={onExit}
          >
            Выйти из игры
        </button>
      </div>    
    </div>
  );
};