import progressStyles from './TopBarProgress.module.css';

export const MobileProgressBar = ({ current, max, label, color = 'blue' }) => {
  const percentage = max > 0 ? (current / max) * 100 : 0;
  
  const getColorClass = () => {
    switch(color) {
      case 'green': return progressStyles.progressBarGreen;
      case 'red': return progressStyles.progressBarRed;
      case 'blue': return progressStyles.progressBarBlue;
      default: return progressStyles.progressBarBlue;
    }
  };

  // Для усталости показываем проценты, для остальных - текущее(максимальное)
  const renderValue = () => {
    if (label === 'Усталость') {
      return `${Math.round(percentage)}%`;
    }
    return `${current}(${max})`;
  };

  return (
    <div className={progressStyles.progressItem}>
      <div className={progressStyles.progressHeader}></div>
      <div className={progressStyles.progressBarWrapper}>
        <div 
          className={`${progressStyles.progressBar} ${getColorClass()}`}
          style={{ width: `${percentage}%` }}
        >
        </div>
        <span className={progressStyles.progressBarLabel}>
          {label}
        </span>
        <span className={progressStyles.progressBarValue}>
          {renderValue()}
        </span>
      </div>
    </div>
  );
};