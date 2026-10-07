import { ServerClock } from './ServerClock';
import styles from '../TopBar.module.css';

/**
 * Вторая панель TopBar: кнопка Refresh + trade buttons.
 * Общий компонент для mobile и desktop версий.
 */
export const TopBarSecondBar = ({
  onRefresh, 
  locationButtons,
  activeView,
  showSecondBar,
  onTradeButtonClick,
  isMobile,
  localRefreshing,
}) => {
  return (
    <div className={styles.secondBar}>
      <button
        className={`${styles.refreshButton} ${localRefreshing ? styles.refreshButtonLoading : ''} ${isMobile ? styles.mobileRefreshButton : ''}`}
        onClick={onRefresh}
        disabled={localRefreshing}
      >
        Обновить
      </button>

      {showSecondBar && (
        <div className={styles.tradeButtons}>
          {locationButtons.map(button => (
            <button
              key={`btn-${button.id}`}
              className={`${styles.tradeButton} ${activeView === button.id ? styles.activeTradeButton : ''}`}
              onClick={() => onTradeButtonClick && onTradeButtonClick(button.id)}
            >
              {button.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};