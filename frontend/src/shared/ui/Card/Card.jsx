import { useTheme } from '../../hooks/ui/useTheme';
import styles from './Card.module.css';

export const Card = ({ mode: propMode, children, className = '' }) => {
  const { themeClass } = useTheme();
  const mode = propMode || themeClass;
  // Устанавливаем класс в зависимости от режима
  let dynamicClass = mode === 'night' ? styles['card-night'] : styles['card-day'];

  return (
    <div className={`${styles.card} ${dynamicClass} ${className}`}>
      {children}
    </div>
  );
};

/* import styles from './Card.module.css';

export const Card = ({ children, className = '', ...props }) => {
  return (
    <div className={`${styles.card} ${className}`} {...props}>
      {children}
    </div>
  );
}; !!!! */