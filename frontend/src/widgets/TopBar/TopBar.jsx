import { useTopBar } from './hooks/useTopBar';
import { Button } from '../../shared/ui/Button/Button';
import { MobileProgressBar } from '../../shared/ui/MobileProgressBar/MobileProgressBar';
import { MobileMenu } from './MobileMenu';
import { ServerClock } from './components/ServerClock';
import { TopBarSecondBar } from './components/TopBarSecondBar';
import styles from './TopBar.module.css';
import progressStyles from '../../shared/ui/MobileProgressBar/TopBarProgress.module.css';

export const TopBar = ({
  title,
  city,
  character,
  onMenuItemClick,
  onRefresh,
  isRefreshing,
  hasUnreadMail,
  onMailClick,
  handleUpSkillsButtonClick,
  isShowUpSkills,
  onTradeButtonClick
}) => {
  const {
    fontSize,
    showMobileMenu,
    isExiting,
    isMailLoading,
    isMobile,
    localRefreshing,
    cityNameRef,
    selectedMenuItems,
    locationButtons,
    activeView,
    showSecondBar,
    handleExit,
    handleRefresh,
    handleMailClick,
    handlePanelIconClick,
    handleMenuButtonClick,
  } = useTopBar(character, city, onRefresh, isRefreshing, hasUnreadMail, onMailClick);

  // ======================== MOBILE RENDER ========================
  if (isMobile) {
    return (
      <header className={styles.headerContainer}>
        <div className={styles.highestFence}></div>
        <div className={`${styles.topBar} ${styles.mobileTopBar}`}>
          <div className={`${styles.topBarContent} ${styles.mobileTopBarContent}`}>
            <div className={`${styles.leftSection} ${styles.mobileLeftSection}`}>
              <div className={styles.mobileIconsContainer}>
                <button 
                  className={styles.mobileMailContainer} 
                  onClick={handleMailClick} 
                  disabled={isMailLoading}
                >
                  <img 
                    src="/images/widgets/top-bar/mail.gif" 
                    alt="Mail" 
                    className={`${styles.mailIcon} ${styles.mobileMailIcon} ${hasUnreadMail ? styles.mailIconBlink : ''}`} 
                  />
                </button>
                
                {selectedMenuItems.length > 0 && (
                  <div className={`${styles.panelIcons} ${styles.mobilePanelIcons}`}>
                    {selectedMenuItems.map((item, idx) => (
                      <button 
                        key={`${item.id}-${idx}`} 
                        className={`${styles.panelIconContainer} ${styles.mobilePanelIconContainer}`} 
                        onClick={() => handlePanelIconClick(item, onMenuItemClick)} 
                        title={item.label}
                      >
                        <img 
                          src={item.icon} 
                          alt={item.label} 
                          className={`${styles.panelIcon} ${styles.mobilePanelIcon}`} 
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <button 
                className={styles.mobileMenuButton} 
                onClick={handleMenuButtonClick}
              >
                Меню
              </button>
            </div>
            
            <div className={`${styles.centerSection} ${styles.mobileCenterSection}`}>
              <span className={`${styles.title} ${styles.mobileTitle}`}>{title}</span>
            </div>
            
            <div className={`${styles.rightSection} ${styles.mobileRightSection}`}>
              <ServerClock />
              <button 
                className={`${styles.mobileMenuButton} ${styles.mobileMenuButtonBottomRight}`} 
                onClick={handleMenuButtonClick}
              >
                Меню
              </button>
            </div>
          </div>
        </div>
        
        {character && (
          <div className={progressStyles.progressContainer}>
            <MobileProgressBar current={character.health} max={character.effective_max_health ?? ((character.max_health || 0) + (character.equipment_bonuses?.max_health_bonus || 0))} label="Здоровье" color="green" />
            <MobileProgressBar current={Math.round(character.tiredness * 100)} max={Math.round((character.effective_max_tiredness ?? ((character.max_tiredness || 1) + (character.equipment_bonuses?.max_tiredness_bonus || 0))) * 100)} label="Усталость" color="red" />
            <MobileProgressBar current={character.mana} max={character.effective_max_mana ?? ((character.max_mana || 0) + (character.equipment_bonuses?.max_mana_bonus || 0))} label="Мана" color="blue" />
          </div>
        )}
        
        {showMobileMenu && character && (
          <MobileMenu 
            character={character} 
            onMenuItemClick={(item) => handlePanelIconClick(item, onMenuItemClick)} 
            onExit={handleExit} 
            handleUpSkillsButtonClick={handleUpSkillsButtonClick} 
            isShowUpSkills={isShowUpSkills} 
          />
        )}
        
        <TopBarSecondBar
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          locationButtons={locationButtons}
          activeView={activeView}
          showSecondBar={showSecondBar}
          onTradeButtonClick={onTradeButtonClick}
          isMobile={isMobile}
          localRefreshing={localRefreshing}
        />
      </header>
    );
  }

  // ======================== DESKTOP RENDER ========================
  return (
    <header className={styles.headerContainer}>
      <div className={styles.highestFence}></div>
      <div className={styles.topBar}>
        <div className={styles.topBarContent}>
          <div className={styles.leftSection}>
            {selectedMenuItems.length > 0 && (
              <div className={styles.panelIcons}>
                {selectedMenuItems.map((item, idx) => (
                  <button 
                    key={`${item.id}-${idx}`} 
                    className={styles.panelIconContainer} 
                    onClick={() => handlePanelIconClick(item, onMenuItemClick)} 
                    title={item.label}
                  >
                    <img src={item.icon} alt={item.label} className={styles.panelIcon} />
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <div className={styles.centerSection}>
            <span className={styles.title}>{title}</span>
          </div>
          
          <div className={styles.rightSection}>
            <div className={styles.mailTimeContainer}>
              <img
                src="/images/widgets/top-bar/mail.gif"
                alt="Mail"
                className={`${styles.mailIcon} ${hasUnreadMail ? styles.mailIconBlink : ''}`}
                onClick={handleMailClick}
                style={{ 
                  pointerEvents: isMailLoading ? 'none' : 'auto', 
                  opacity: isMailLoading ? 0.6 : 1, 
                  cursor: isMailLoading ? 'not-allowed' : 'pointer' 
                }}
              />
              <ServerClock />
            </div>
            
            <div className={styles.cityFrame}>
              <span 
                className={styles.cityName} 
                style={{ fontSize }} 
                ref={cityNameRef}
              >
                {city}
              </span>
              
              <Button 
                variant="outline" 
                size="small" 
                onClick={handleExit} 
                className={styles.backButton} 
                disabled={isExiting}
              >
                <img src="/images/widgets/top-bar/exit.png" alt="Выход" className={styles.exitIcon} />
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <TopBarSecondBar
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        locationButtons={locationButtons}
        activeView={activeView}
        showSecondBar={showSecondBar}
        onTradeButtonClick={onTradeButtonClick}
        isMobile={isMobile}
        localRefreshing={localRefreshing} 
      />
    </header>
  );
};