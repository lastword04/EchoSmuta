export const DEFAULT_ITEM_ICON = '/images/items/default.png';

const TRADE_PREFIXES = ['i.el.', 'i.an.', 'i.o.', 'i.f.', 'i.fur.'];

export const itemIcon = (slug) => {
  const folder = TRADE_PREFIXES.some((p) => slug.startsWith(p)) ? 'trade' : 'equip';
  return `/images/items/${folder}/${slug}.png`;
};