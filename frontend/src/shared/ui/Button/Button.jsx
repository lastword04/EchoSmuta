import { useTheme } from '../../hooks/ui/useTheme';
import styles from './Button.module.css';

export const Button = ({ 
  children, 
  mode: propMode,
  variant = 'primary', 
  size = 'medium', 
  onClick,
  className = '',
  ...props 
}) => {
  const { themeClass } = useTheme();
  const mode = propMode || themeClass;
  let dynamicClass = mode !== undefined && mode === 'night'
                   ? styles['button-night']
                   : styles['button-day'];
  return (
    <button
      className={`${styles.button} ${dynamicClass} ${styles[variant]} ${styles[size]} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};