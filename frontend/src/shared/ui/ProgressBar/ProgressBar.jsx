import React from 'react';
import styles from './ProgressBar.module.css';

export const ProgressBar = ({ current, max, label, color = 'blue' }) => {
  const percentage = max > 0 ? (current / max) * 100 : 0;

  return (
    <div className={styles.progressBarContainer}>
      <div className={styles.progressLabel}>
        <span>{label}</span>
        <span>{current}/{max}</span>
      </div>
      <div className={styles.progressBar}>
        <div
          className={`${styles.progressFill} ${styles[`progress-${color}`]}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};
