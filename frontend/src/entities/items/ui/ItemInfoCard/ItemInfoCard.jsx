import React, { useState } from 'react';
import { formatRecipeDescription } from '../../../../shared/lib/formatting/abilityParametersFormatter';
import { itemIcon, DEFAULT_ITEM_ICON } from '../../../../shared/config/ui/itemIcons';   
import { parseUtcDate } from '../../../../shared/lib/utils/utcDate';
import styles from './ItemInfoCard.module.css';
import btn from '../../../../shared/styles/buttons.module.css';

const TYPE_LABELS = {
  weapon: 'Оружие', shield: 'Щит', kit: 'Комплект', helmet: 'Шлем', armor: 'Броня',
  gauntlets: 'Перчатки', gloves: 'Перчатки', leggings: 'Поножи', boots: 'Сапоги',
  cloak: 'Плащ', amulet: 'Амулет', pendant: 'Кулон', ring: 'Кольцо',
  elixir: 'Эликсир', fish: 'Рыба', oil: 'Масло', furniture: 'Мебель', animal: 'Животное',
};

const RACE_LABELS = {
  orc: 'Орк',
  elf: 'Эльф',
  human: 'Человек',
};

const EQUIPMENT_TYPES = [
  'weapon', 'shield', 'kit', 'helmet', 'armor', 'gauntlets', 'gloves',
  'leggings', 'boots', 'cloak', 'amulet', 'pendant', 'ring'
];

const computeTotals = (char) => {
  if (!char) return null;
  const eb = char.equipment_bonuses || {};
  return {
    level: char.level ?? 0,
    race: char.race,
    power: char.effective_power ?? ((char.power ?? 0) + (eb.strength_bonus ?? 0)),
    agility: char.effective_agility ?? ((char.agility ?? 0) + (eb.agility_bonus ?? 0)),
    lucky: char.effective_lucky ?? ((char.lucky ?? 0) + (eb.luck_bonus ?? 0)),
  };
};

const formatExpiry = (expiredDate) => {
  if (!expiredDate) return null;
  const diff = parseUtcDate(expiredDate) - Date.now();
  if (diff <= 0) return 'истёк';
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${days}дн. ${String(hours).padStart(2, '0')}ч. ${String(mins).padStart(2, '0')}мин.`;
};

// Построение строк параметров с правильным порядком:
// Статы с числом (Сила +1, Здоровье +6) → Статы с процентом (Сила: +5%) → Модификаторы (Уворот, Крит)
const buildParamRows = (itemData) => {
  const rows = formatRecipeDescription(itemData)
    .split(', ')
    .filter(r => r && r !== '—');

  // Статы ТОЛЬКО с процентом («Сила: +5%», «Ловкость: +3%», «Удача: +2%»)  
  const pctOnlyRegex = /^(Сила|Ловкость|Удача): [+-]?\d+%$/;
  const early = rows.filter(r => pctOnlyRegex.test(r));
  const rest = rows.filter(r => !pctOnlyRegex.test(r));
  if (early.length === 0) return rows;

  // Все статы с числом (Сила +1, Ловкость +2, Здоровье +6, Мана +5 и т.д.)
  const statWithNumRegex = /^(Сила|Ловкость|Удача|Здоровье|Мана) (\+\d+|\d+)/;
  let lastStatIdx = -1;
  rest.forEach((row, i) => {
    if (statWithNumRegex.test(row)) lastStatIdx = i;
  });

  if (lastStatIdx >= 0) {
    // Вставляем после последнего стата с числом — ПЕРЕД модификаторами
    rest.splice(lastStatIdx + 1, 0, ...early);
  } else {
    // Статов с числом нет — ставим в начало
    rest.unshift(...early);
  }
  return rest;
};

export const ItemInfoCard = ({ item, onClose, actionLabel, onAction, actionDisabled, character }) => {
  const [imgError, setImgError] = useState(false);
  const type = String(item.item.item_type).toLowerCase();
  const isEquipment = EQUIPMENT_TYPES.includes(type);
  const isKit = type === 'kit';
  const p = item.item?.parameters || {};

  const paramRows = buildParamRows(item.item);

  // Износ: красный при > 75% от максимума
  const wear = item.wear ?? 0;
  const maxWear = p.max_wear ?? null;
  const isWearCritical = maxWear ? wear > maxWear * 0.75 : wear > 0;

  // Требования (явные > 0 — чтобы не рендерились «нули»)
  const reqLevel = item.item?.minimal_level ?? 0;
  const reqStrength = p.required_strength ?? 0;
  const reqAgility = p.required_agility ?? 0;
  const reqLuck = p.required_luck ?? 0;
  const reqRace = item.item?.race ? String(item.item.race).toLowerCase() : null;
  const hasRequirements = reqLevel > 0 || reqStrength > 0 || reqAgility > 0 || reqLuck > 0 || !!reqRace;

  const totals = computeTotals(character);
  const unmet = {
    level: !!totals && reqLevel > 0 && totals.level < reqLevel,
    strength: !!totals && reqStrength > 0 && totals.power < reqStrength,
    agility: !!totals && reqAgility > 0 && totals.agility < reqAgility,
    luck: !!totals && reqLuck > 0 && totals.lucky < reqLuck,
    race: !!totals && !!reqRace && !!totals.race && String(totals.race).toLowerCase() !== reqRace,
  };

  return (
    <div className={styles.resourceInfoCard}>
      <div className={styles.resourceInfoHeader}>
        <div className={styles.resourceInfoTitle}>{item.item.name}</div>
        <button className={styles.resourceInfoClose} onClick={onClose}>✕</button>
      </div>

      {/* Верхняя строка на всю ширину */}
      <div className={styles.itemInfoTopRow}>
        <span>Цена: <span className={styles.itemPriceValue}>{item.item.price} дт.</span></span>
        <span>Вес: {item.item.weight}</span>
        {isEquipment && !isKit ? (
          <span className={isWearCritical ? styles.itemWearValue : undefined}>
            Износ: {wear}/{maxWear ?? '?'}
          </span>
        ) : (
          <span>Кол-во: {item.amount}</span>
        )}
      </div>

      {/* Картинка + параметры */}
      <div className={styles.itemInfoBody}>
        {!isKit && (
          <div className={styles.itemInfoImageBox}>
            <img
              className={styles.itemInfoImage}
              src={imgError ? DEFAULT_ITEM_ICON : itemIcon(item.item.slug)}
              alt={item.item.name}
              onError={() => setImgError(true)}
              fetchPriority="high"
            />
          </div>
        )}
        <div className={styles.itemInfoDetails}>
          {paramRows.length > 0 && (
            <>
              <div className={styles.itemInfoSection}>{isEquipment ? 'Параметры' : 'Свойства'}</div>
              {paramRows.map((row, i) => <div key={i}>{row}</div>)}
            </>
          )}
          {item.expired_date && (
            <div className={styles.itemInfoExpiry}>Срок годности: {formatExpiry(item.expired_date)}</div>
          )}
          {type === 'oil' && p.max_used != null && (
            <div className={styles.itemInfoExpiry}>
              Применений: {item.used_count ?? 0} / {p.max_used}
            </div>
          )}
        </div>
      </div>

      {/* Требования — отдельный блок внизу */}
      {hasRequirements && (
        <div className={styles.itemInfoRequirementsBlock}>
          <div className={`${styles.itemInfoSection} ${styles.itemInfoSectionCenter}`}>Требования</div>
          <div className={styles.itemInfoRequirements}>
            {reqLevel > 0 && <span>Уровень: <b className={unmet.level ? styles.reqUnmet : undefined}>{reqLevel}</b></span>}
            {reqStrength > 0 && <span>Сила: <b className={unmet.strength ? styles.reqUnmet : undefined}>{reqStrength}</b></span>}
            {reqAgility > 0 && <span>Ловкость: <b className={unmet.agility ? styles.reqUnmet : undefined}>{reqAgility}</b></span>}
            {reqLuck > 0 && <span>Удача: <b className={unmet.luck ? styles.reqUnmet : undefined}>{reqLuck}</b></span>}
            {reqRace && <span>Раса: <b className={unmet.race ? styles.reqUnmet : undefined}>{RACE_LABELS[reqRace] || reqRace}</b></span>}
          </div>
        </div>
      )}

      {actionLabel && (
        <div className={styles.itemInfoActions}>
          <button
            className={btn.textLinkAction}
            onClick={onAction}
            disabled={actionDisabled}
          >
            {actionLabel}
          </button>
        </div>
      )}
    </div>
  );
};