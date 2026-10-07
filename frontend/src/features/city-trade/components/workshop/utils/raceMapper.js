/**
 * Маппинг рас с английского на русский
 * Используется в таблицах крафта и рецептов
 */
const RACE_MAP = {
  'human': 'Человек',
  'elf': 'Эльф',
  'orc': 'Орк',
  'dwarf': 'Гном'
};

/**
 * Возвращает русское название расы
 * @param {string} race - slug расы на английском
 * @returns {string} - русское название или исходный slug
 */
export const getRaceName = (race) => RACE_MAP[race] || race;