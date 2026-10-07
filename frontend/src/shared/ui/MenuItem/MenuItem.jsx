import styles from './MenuItem.module.css';

export const MenuItem = ({ 
  item, 
  onClick, 
  onMouseEnter, 
  onMouseLeave,  
  isChecked = false,
  onCheckboxChange,  
}) => {
  const handleClick = () => {
    onClick(item);
  };

  const handleCheckboxClick = (e) => {
    e.stopPropagation();     
    onCheckboxChange(item.id, !isChecked);    
  };

  return (
    <div
      className={styles.menuItem}
      onClick={handleClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div 
        className={`${styles.checkbox} ${isChecked ? styles.checked : ''}`}
        onClick={handleCheckboxClick}
      >
        {isChecked && (
          <svg 
            className={styles.checkmark} 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M20 6L9 17L4 12" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            />
          </svg>
        )}
      </div>
      <span className={styles.menuLabel}>{item.label}</span>
    </div>
  );
};