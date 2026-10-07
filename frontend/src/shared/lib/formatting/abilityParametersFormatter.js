// =============================================================================
// Маппинг одиночных параметров способностей (не входящих в группы)
// =============================================================================

const ABILITY_PARAMETERS_MAP = {
  // Характеристики персонажа (числовые)
  power_number: (v) => v !== 0 ? `Сила +${v}` : null,
  agility_number: (v) => v !== 0 ? `Ловкость +${v}` : null,
  lucky_number: (v) => v !== 0 ? `Удача +${v}` : null,
  attributes_number: (v) => v !== 0 ? `+${v} ко всем атрибутам` : null,

  // Базовые характеристики (без суффикса)
  strength: (v) => v !== 0 ? `Сила +${v}` : null,
  agility: (v) => v !== 0 ? `Ловкость +${v}` : null,
  luck: (v) => v !== 0 ? `Удача +${v}` : null,
  health: (v) => v !== 0 ? `Здоровье +${v}` : null,
  mana: (v) => v !== 0 ? `Мана +${v}` : null,

  // Здоровье (числовое / процентное)
  health_number: (v) => v !== 0 ? `Здоровье +${v}` : null,
  max_health_percentage: (v) => v !== 0 ? `Макс. здоровье +${(v * 100).toFixed(0)}%` : null,

  // Мана (числовая)
  mana_number: (v) => v !== 0 ? `Мана +${v}` : null,

  // Магия порядка (плащи)
  magic_order_1_self: (v) => v !== 0 ? `Магия порядка I: +${(v * 100).toFixed(0)}%` : null,
  magic_order_2_self: (v) => v !== 0 ? `Магия порядка II: +${(v * 100).toFixed(0)}%` : null,
  magic_order_3_self: (v) => v !== 0 ? `Магия порядка III: +${(v * 100).toFixed(0)}%` : null,

  // Боевые способности (атаки против локаций)
  attack_against_swamp_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Болота` : null,
  attack_against_mine_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Шахты` : null,
  attack_against_lake_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Озера` : null,
  attack_against_sands_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Песков` : null,
  attack_against_quarry_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Прииска` : null,
  attack_against_forest_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Леса` : null,
  attack_against_labyrinth_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Лабиринта` : null,
  attack_against_library_percentage: (v) => v !== 0 ? `+${(v * 100).toFixed(0)}% к атаке против обитателей Библиотеки` : null,

  // Специальные способности
  dispel_all_effects: (v) => v ? 'Развеивает все эффекты' : null,
  invisible_way: (v) => v ? 'Невидимость в пути' : null,
  summon_additional_beast: (v) => v ? 'Призыв дополнительного зверя в бою' : null,
  accelerated_recovery: (v) => v ? 'Ускоренное восстановление персонажа' : null,
  increase_carry_weight: (v) => v !== 0 ? `+${v} к переносимому весу` : null,
};

// =============================================================================
// Пары параметров, которые объединяются в одну строку: "Сила +1 (+20%)"
// =============================================================================

const STAT_PAIRS = [
  { numKey: 'strength', pctKey: 'strength_percent', label: 'Сила' },
  { numKey: 'agility', pctKey: 'agility_percent', label: 'Ловкость' },
  { numKey: 'luck', pctKey: 'luck_percent', label: 'Удача' },
];

// =============================================================================
// Группы параметров, которые нужно объединить в одну строку через "/"
// =============================================================================

const ABILITY_GROUPS = [
  { label: 'Здоровье', keys: ['health_percentage', 'health_percentage_weared'] },
  { label: 'Усталость', keys: ['tiredness_percentage', 'tiredness_percentage_weared'] },
  { label: 'Мана', keys: ['mana_percentage', 'mana_percentage_weared'] },
];

// =============================================================================
// ✅ ФИКСИРОВАННЫЙ ПОРЯДОК вывода остальных ability_parameters
// =============================================================================

const ABILITY_PARAMETERS_ORDER = [
  // Характеристики
  'strength', 'agility', 'luck',
  'health', 'mana',
  'power_number', 'agility_number', 'lucky_number',
  'health_number', 'mana_number',
  'attributes_number',
  'max_health_percentage',

  // Магия порядка
  'magic_order_1_self', 'magic_order_2_self', 'magic_order_3_self',

  // Специальные способности
  'dispel_all_effects',
  'invisible_way',
  'summon_additional_beast',
  'accelerated_recovery',
  'increase_carry_weight',

  // Атаки против локаций
  'attack_against_swamp_percentage',
  'attack_against_mine_percentage',
  'attack_against_lake_percentage',
  'attack_against_sands_percentage',
  'attack_against_quarry_percentage',
  'attack_against_forest_percentage',
  'attack_against_labyrinth_percentage',
  'attack_against_library_percentage',
];

// =============================================================================
// Вспомогательная функция форматирования процентов со знаком
// =============================================================================

const formatPercentValue = (val) => {
  if (typeof val !== 'number') return String(val);
  const percent = (val * 100).toFixed(0);
  return val < 0 ? `${percent}%` : `+${percent}%`;
};

// =============================================================================
// Основная функция форматирования ability_parameters с группировкой
// =============================================================================

export const formatAbilityParameters = (abilityParams) => {
  if (!abilityParams || typeof abilityParams !== 'object') {
    return [];
  }

  const descriptions = [];
  const processedKeys = new Set();

  // 1. Обрабатываем пары (Сила +1 (+20%)) — с фильтрацией нулей
  for (const pair of STAT_PAIRS) {
    const numVal = abilityParams[pair.numKey];
    const pctVal = abilityParams[pair.pctKey];

    const hasNum = numVal !== undefined && numVal !== null && numVal !== 0;
    const hasPct = pctVal !== undefined && pctVal !== null && pctVal !== 0;

    if (hasNum && hasPct) {
      const pctStr = pctVal >= 0 ? `+${(pctVal * 100).toFixed(0)}%` : `${(pctVal * 100).toFixed(0)}%`;
      descriptions.push(`${pair.label} +${numVal} (${pctStr})`);
      processedKeys.add(pair.numKey);
      processedKeys.add(pair.pctKey);
    } else if (hasNum) {
      descriptions.push(`${pair.label} +${numVal}`);
      processedKeys.add(pair.numKey);
    } else if (hasPct) {
      const pctStr = pctVal >= 0 ? `+${(pctVal * 100).toFixed(0)}%` : `${(pctVal * 100).toFixed(0)}%`;
      descriptions.push(`${pair.label}: ${pctStr}`);
      processedKeys.add(pair.pctKey);
    }
  }

  // 2. Обрабатываем группы (Здоровье %, Усталость %, Мана %)
  for (const group of ABILITY_GROUPS) {
    const groupValues = group.keys
      .map((key) => abilityParams[key])
      .filter((val) => val !== undefined && val !== null && val !== 0);

    if (groupValues.length > 0) {
      const formattedValues = groupValues.map(formatPercentValue).join('/');
      descriptions.push(`${group.label} ${formattedValues}`);
      group.keys.forEach((key) => processedKeys.add(key));
    }
  }

  // 3. ✅ Оставшиеся ключи — в ФИКСИРОВАННОМ порядке
  for (const key of ABILITY_PARAMETERS_ORDER) {
    if (processedKeys.has(key)) continue;

    const value = abilityParams[key];
    if (value === 0 || value === null || value === undefined) continue;

    const formatter = ABILITY_PARAMETERS_MAP[key];
    if (formatter) {
      const formatted = formatter(value);
      if (formatted) {
        descriptions.push(formatted);
        processedKeys.add(key);
      }
    }
  }

  // 4. Fallback: неизвестные ключи (если бэк добавит новые)
  for (const key of Object.keys(abilityParams)) {
    if (processedKeys.has(key)) continue;

    const value = abilityParams[key];
    if (value === 0 || value === null || value === undefined) continue;

    descriptions.push(`${key}: ${value}`);
  }

  return descriptions;
};

export const formatAbilityParametersString = (abilityParams, separator = ', ') => {
  const descriptions = formatAbilityParameters(abilityParams);
  return descriptions.length > 0 ? descriptions.join(separator) : null;
};

// =============================================================================
// Маппинг для parameters (требования, защита, урон и т.д.)
// =============================================================================

const PARAMETERS_MAP = {
  required_strength: (v) => `Требуемая сила: ${v}`,
  required_agility: (v) => `Требуемая ловкость: ${v}`,
  required_luck: (v) => `Требуемая удача: ${v}`,
  max_wear: (v) => `Макс. износ: ${v}`,
  defense: (v) => `Защита: ${v}`,
  speed: (v) => `Скорость: ${v}`,
  volume: (v) => `Объём: ${v}`,
  max_used: (v) => `Макс. использований: ${v}`,
};

const PERCENT_PARAMETERS = {
  dodge_self: (v) => v !== 0 ? `Уворот себе: ${v >= 0 ? '+' : ''}${(v * 100).toFixed(0)}%` : null,
  crit_self: (v) => v !== 0 ? `Крит себе: ${v >= 0 ? '+' : ''}${(v * 100).toFixed(0)}%` : null,
  dodge_reduction: (v) => v !== 0 ? `Уворот противнику: ${(v * 100).toFixed(0)}%` : null,
  crit_reduction: (v) => v !== 0 ? `Крит противнику: ${(v * 100).toFixed(0)}%` : null,
  strength_percent: (v) => v !== 0 ? `Сила: ${v >= 0 ? '+' : ''}${(v * 100).toFixed(0)}%` : null,
};

const PARAMETERS_ORDER = [
  'damage_min', 'damage_max',  
  'dodge_self', 'crit_self',
  'dodge_reduction', 'crit_reduction',
  'strength_percent',
  'speed', 'volume', 'max_used', 'max_wear',
  'required_strength', 'required_agility', 'required_luck',
  'defense',
];

export const formatParameters = (params) => {
  if (!params || typeof params !== 'object') return [];
  const result = [];

  for (const key of PARAMETERS_ORDER) {
    if (params[key] === undefined || params[key] === null) continue;

    if (key === 'damage_min') {
      if (params.damage_max != null) {
        result.push(`Урон: ${params.damage_min}–${params.damage_max}`);
      }
    } else if (key === 'damage_max') {
      continue;
    } else if (PERCENT_PARAMETERS[key]) {
      const formatted = PERCENT_PARAMETERS[key](params[key]);
      if (formatted) result.push(formatted);
    } else if (PARAMETERS_MAP[key]) {
      result.push(PARAMETERS_MAP[key](params[key]));
    }
  }

  for (const [key, value] of Object.entries(params)) {
    if (PARAMETERS_ORDER.includes(key)) continue;
    if (value === 0 || value === null || value === undefined) continue;

    if (PERCENT_PARAMETERS[key]) {
      const formatted = PERCENT_PARAMETERS[key](value);
      if (formatted) result.push(formatted);
    } else if (PARAMETERS_MAP[key]) {
      result.push(PARAMETERS_MAP[key](value));
    }
  }

  return result;
};

export const formatParametersString = (params, separator = ', ') => {
  const descriptions = formatParameters(params);
  return descriptions.length > 0 ? descriptions.join(separator) : null;
};

// =============================================================================
// ✅ ПОЛНОСТЬЮ ПЕРЕПИСАНО: Форматирование описания рецепта
// =============================================================================

// ✅ ЕДИНЫЙ порядок всех параметров (из обоих sources)
const RECIPE_FULL_ORDER = [
  'damage_min', 'damage_max',           // Урон
  'health',                              // Здоровье (из ability_parameters)
  'strength', 'agility', 'luck',         // Характеристики (с процентами через STAT_PAIRS)
  'dodge_self', 'dodge_reduction',       // Уворот
  'crit_self', 'crit_reduction',         // Крит
  'defense',                             // Защита
];

export const formatRecipeDescription = (item) => {
  if (!item) return '—';

  const parts = [];
  const processedKeys = new Set();
  
  const params = item.parameters || {};
  const abilityParams = item.ability_parameters || {};

  // 1. Урон (только из parameters)
  if (params.damage_min != null && params.damage_max != null) {
    parts.push(`Урон: ${params.damage_min}–${params.damage_max}`);
    processedKeys.add('damage_min');
    processedKeys.add('damage_max');
  }

  // 2. Обрабатываем STAT_PAIRS (Сила +1 (+20%))
  for (const pair of STAT_PAIRS) {
    const numVal = abilityParams[pair.numKey];
    const pctVal = params[pair.pctKey] ?? abilityParams[pair.pctKey]; // Берём из parameters или ability_parameters

    const hasNum = numVal !== undefined && numVal !== null && numVal !== 0;
    const hasPct = pctVal !== undefined && pctVal !== null && pctVal !== 0;

    if (hasNum && hasPct) {
      const pctStr = pctVal >= 0 ? `+${(pctVal * 100).toFixed(0)}%` : `${(pctVal * 100).toFixed(0)}%`;
      parts.push(`${pair.label} +${numVal} (${pctStr})`);
      processedKeys.add(pair.numKey);
      processedKeys.add(pair.pctKey);
    } else if (hasNum) {
      parts.push(`${pair.label} +${numVal}`);
      processedKeys.add(pair.numKey);
    } else if (hasPct) {
      const pctStr = pctVal >= 0 ? `+${(pctVal * 100).toFixed(0)}%` : `${(pctVal * 100).toFixed(0)}%`;
      parts.push(`${pair.label}: ${pctStr}`);
      processedKeys.add(pair.pctKey);
    }
  }

  // 3. Остальные параметры в фиксированном порядке
  for (const key of RECIPE_FULL_ORDER) {
    if (processedKeys.has(key)) continue;

    // Проверяем сначала в parameters
    let value = params[key];
    let source = 'parameters';
    
    // Если нет в parameters — проверяем в ability_parameters
    if (value === undefined || value === null) {
      value = abilityParams[key];
      source = 'ability_parameters';
    }

    if (value === undefined || value === null || value === 0) continue;

    // Форматируем в зависимости от источника
    if (source === 'parameters') {
      if (PERCENT_PARAMETERS[key]) {
        const formatted = PERCENT_PARAMETERS[key](value);
        if (formatted) parts.push(formatted);
      } else if (PARAMETERS_MAP[key]) {
        parts.push(PARAMETERS_MAP[key](value));
      }
    } else {
      if (ABILITY_PARAMETERS_MAP[key]) {
        const formatted = ABILITY_PARAMETERS_MAP[key](value);
        if (formatted) parts.push(formatted);
      }
    }
    
    processedKeys.add(key);
  }

  // 4. Fallback: остальные ability_parameters (специальные способности и т.д.)
  const abilityStr = formatAbilityParametersString(abilityParams);
  if (abilityStr) {
    // Проверяем, не добавили ли мы уже эти параметры
    const additionalParts = abilityStr.split(', ').filter(part => {
      return !parts.some(p => p.includes(part.substring(0, 20)));
    });
    if (additionalParts.length > 0) {
      parts.push(...additionalParts);
    }
  }

  return parts.length > 0 ? parts.join(', ') : '—';
};