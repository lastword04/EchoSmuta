import { useTheme } from '../../hooks/ui/useTheme';
import styles from './Sky.module.css';

export const Sky = ({ mode: propMode, className = '' }) => {
  const { themeClass } = useTheme();
  const mode = propMode || themeClass;
  
  return (
    <div className={`${styles.sky} ${styles[mode]} ${className}`}>
      {mode === 'night' ? (
        <>
          {/* Луна — слева */}
          <div className={styles.moon}></div>
          
          {/* Звёзды */}
          {[...Array(50)].map((_, i) => (
            <div 
              key={i} 
              className={styles.star}
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                width: `${Math.random() * 3 + 1}px`,
                height: `${Math.random() * 3 + 1}px`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${Math.random() * 2 + 2}s`
              }}
            />
          ))}
          
          {/* Падающая звезда */}
          <div className={styles.shootingStar}></div>
        </>
      ) : (
        <>
          {/* Тёплые частицы в воздухе */}
          {[...Array(15)].map((_, i) => (
            <div 
              key={`particle-${i}`} 
              className={styles.particle}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${Math.random() * 4 + 6}s`
              }}
            />
          ))}
          
          {/* === Искры (медленные) === */}
          {[...Array(12)].map((_, i) => (
            <div 
              key={`spark-${i}`} 
              className={styles.spark}
              style={{
                left: `${Math.random() * 100}%`,
                bottom: `-${Math.random() * 20}%`,
                animationDelay: `${Math.random() * 8}s`,
                animationDuration: `${Math.random() * 4 + 8}s`  /* Было 3+4, стало 4+8 */
              }}
            />
          ))}
        </>
      )}
    </div>
  );
};