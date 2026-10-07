// src/widgets/CharacterPanel/buffs.js
import { parseUtcDate } from '../../shared/lib/utils/utcDate';


export const BUFF_LABELS = {
  strength_boost: 'Сила',
  agility_boost: 'Ловкость',
  luck_boost: 'Удача',
  hp_restore: 'Здоровье',
  stamina_restore: 'Выносливость',
  stamina_restore_percent: 'Снижение усталости',
};


export const isBuffAlive = (buff, now = Date.now()) => {
  if (!buff?.is_active) return false;
  if (!buff.expires_at) return true;
  return parseUtcDate(buff.expires_at).getTime() > now;
};

