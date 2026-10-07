export const CATEGORY_LABELS = {
  swamp: 'Болото',
  mine: 'Шахта',
  gems: 'Прииск',
  lake: 'Озеро',
  forest: 'Лес',
  sands: 'Пески',
  skins: 'Шкуры',
};

export const CATEGORY_ORDER = ['swamp', 'mine', 'gems', 'lake', 'forest', 'sands', 'skins'];

export const sortCategories = (categories) => {
  return categories.sort((a, b) => {
    const idxA = CATEGORY_ORDER.indexOf(a);
    const idxB = CATEGORY_ORDER.indexOf(b);
    if (idxA === -1 && idxB === -1) return 0;
    if (idxA === -1) return 1;
    if (idxB === -1) return -1;
    return idxA - idxB;
  });
};