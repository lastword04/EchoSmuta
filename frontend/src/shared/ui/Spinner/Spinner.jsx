import styles from './Spinner.module.css';

export const Spinner = ({ size = 'medium', className = '' }) => {
  return (
    <div className={`${styles.spinner} ${styles[size]} ${className}`}>
      <div className={styles.spinnerInner}></div>
    </div>
  );
};