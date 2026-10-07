import { BUFF_LABELS, isBuffAlive } from './buffs';
import { parseUtcDate } from '../../shared/lib/utils/utcDate';
import styles from './CharacterPanel.module.css';


const formatDuration = (expiresAt) => {
  if (!expiresAt) return '∞';
  const diff = parseUtcDate(expiresAt).getTime() - Date.now();
  if (diff <= 0) return 'истёк';

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (seconds < 60) return `${seconds}с`;
  if (minutes < 60) {
    const remSeconds = seconds % 60;
    return remSeconds > 0 ? `${minutes}м ${remSeconds}с` : `${minutes}м`;
  }
  if (hours < 24) {
    const remMinutes = minutes % 60;
    return remMinutes > 0 ? `${hours}ч ${remMinutes}м` : `${hours}ч`;
  }
  const remHours = hours % 24;
  return remHours > 0 ? `${days}д ${remHours}ч` : `${days}д`;
};


export const ActiveBuffs = ({ buffs }) => { 

  if (!buffs || buffs.length === 0) return null;

  const now = Date.now();
  const alive = buffs.filter(b => isBuffAlive(b, now));
  if (alive.length === 0) return null;
 
  return (
    <div className={styles.buffsTable}>
      <div className={styles.buffsHeader}>
        <span>Название</span>
        <span>Время</span>
        <span>Описание</span>
      </div>
      {alive.map(buff => {
        const label = BUFF_LABELS[buff.buff_type] || buff.buff_type;
        const sign = buff.value >= 0 ? '+' : '';
        return (
          <div key={buff.id} className={styles.buffRow}>
            <span>{buff.source_name || label}</span>                           
            <span>{formatDuration(buff.expires_at)}</span>     
            <span>{label} {sign}{buff.value}</span>                  
          </div>
        );
      })}
    </div>
  );
};

  
