import { useState, useEffect } from 'react';
import { ActiveBuffs } from '../../ActiveBuffs';
import { isBuffAlive } from '../../buffs';
import styles from '../MagicModal.module.css';

export const EffectsTab = ({ character }) => {
  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const now = Date.now();
  const buffs = (character?.buffs || []).filter(b => isBuffAlive(b, now));

  return (
    <div className={styles.list}>
      {buffs.length === 0 ? (
        <div className={styles.placeholder}>Нет активных эффектов</div>
      ) : (
        <ActiveBuffs buffs={buffs} />
      )}
    </div>
  );
};