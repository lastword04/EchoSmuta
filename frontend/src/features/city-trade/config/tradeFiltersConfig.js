// ============================================================
// tradeFiltersConfig.js
// ============================================================
export const TRADE_FILTERS_CONFIG = {
  '1.21.furniture-shop': {
    numberLabel: '№ лавки',
    groups: [
      {
        id: 'furniture',
        label: 'Мебель',
        placeholder: 'Мебель',
        options: [
          { label: 'Лавка малая', value: 'Лавка малая' },
          { label: 'Стул', value: 'Стул' },
          { label: 'Кресло', value: 'Кресло' },
          { label: 'Стол обеденный', value: 'Стол обеденный' },
          { label: 'Кровать одноместная', value: 'Кровать одноместная' },
          { label: 'Светильник', value: 'Светильник' },
          { label: 'Зеркало', value: 'Зеркало' },
          { label: 'Ковер', value: 'Ковер' },
        ],
      },
    ],
  },
  '1.9.pharmacy': {
    numberLabel: '№ аптеки',
    groups: [
      {
        id: 'raceless',
        label: 'Внерасовые',
        placeholder: 'Эликсиры',
        options: [
          { label: 'Эликсир Развеивания', value: 'Эликсир Развеивания' },
          { label: 'Эликсир Вечной Жизни', value: 'Эликсир Вечной Жизни' },
          { label: 'Грааль Жизни +240', value: 'Эликсир Грааль Жизни' },
          { label: 'Кубок Жизни +180', value: 'Эликсир Кубок Жизни' },
          { label: 'Чаша Жизни +120', value: 'Эликсир Чаша Жизни' },
          { label: 'Небесный Поток +90', value: 'Эликсир Небесный Поток' },
          { label: 'Лагуна Мудрости +60', value: 'Эликсир Лагуна Мудрости' },
          { label: 'Глоток Жизни +60', value: 'Эликсир Глоток Жизни' },
          { label: 'Волшебная Слеза +30', value: 'Эликсир Волшебная Слеза' },
          { label: 'Капля Жизни +30', value: 'Эликсир Капля Жизни' },
        ],
      },
      {
        id: 'race',
        tabs: [
          { id: 'orc', label: 'Орк' },
          { id: 'elf', label: 'Эльф' },
          { id: 'human', label: 'Человек' },
        ],
        defaultTab: 'orc',
        placeholder: 'Эликсиры',
        options: [
          // === ORC ===
          { label: 'Сила +5', value: 'Эликсир Нечистая сила', tab: 'orc' },
          { label: 'Ловкость +3', value: 'Эликсир Укус Пчелы', tab: 'orc' },
          { label: 'Удача +3', value: 'Эликсир Медвежья песня', tab: 'orc' },
          { label: 'Усталость -20%', value: 'Эликсир Трезвость', tab: 'orc' },
          { label: 'Усталость -40%', value: 'Эликсир Полная Луна', tab: 'orc' },
          { label: 'Сила +1', value: 'Эликсир Сила Действия', tab: 'orc' },
          { label: 'Ловкость +1', value: 'Эликсир Скорость Тигра', tab: 'orc' },
          { label: 'Удача +1', value: 'Эликсир Шепот Фортуны', tab: 'orc' },
          // === ELF ===
          { label: 'Сила +3', value: 'Эликсир Плач Неразумных', tab: 'elf' },
          { label: 'Ловкость +5', value: 'Эликсир Живая Вода', tab: 'elf' },
          { label: 'Удача +3', value: 'Эликсир Розовый Свет', tab: 'elf' },
          { label: 'Усталость -20%', value: 'Эликсир Легкий Путь', tab: 'elf' },
          { label: 'Усталость -40%', value: 'Эликсир Второе Дыхание', tab: 'elf' },
          { label: 'Сила +1', value: 'Эликсир Сила Духа', tab: 'elf' },
          { label: 'Ловкость +1', value: 'Эликсир Скорость Ястреба', tab: 'elf' },
          { label: 'Удача +1', value: 'Эликсир Танец Фортуны', tab: 'elf' },
          // === HUMAN ===
          { label: 'Сила +3', value: 'Эликсир Свирепый Воин', tab: 'human' },
          { label: 'Ловкость +3', value: 'Эликсир Преследование', tab: 'human' },
          { label: 'Удача +5', value: 'Эликсир Момент Истины', tab: 'human' },
          { label: 'Усталость -20%', value: 'Эликсир Белый День', tab: 'human' },
          { label: 'Усталость -40%', value: 'Эликсир Энергия', tab: 'human' },
          { label: 'Сила +1', value: 'Эликсир Сила Разума', tab: 'human' },
          { label: 'Ловкость +1', value: 'Эликсир Скорость Звука', tab: 'human' },
          { label: 'Удача +1', value: 'Эликсир Улыбка Фортуны', tab: 'human' },
        ],
      },
    ],
  },
  '1.25.fish-shop': {
    numberLabel: '№ лавки',
    groups: [
      {
        id: 'dried',
        label: 'Вяленая рыба',
        placeholder: 'Рыба',
        options: [
          { label: 'Вяленый Ерш -10%', value: 'Вяленый Ерш' },
          { label: 'Вяленая Плотва -30%', value: 'Вяленая Плотва' },
          { label: 'Вяленый Карась -50%', value: 'Вяленый Карась' },
        ],
      },
      {
        id: 'fried',
        label: 'Жареная и копченая рыба',
        placeholder: 'Рыба',
        options: [
          { label: 'Жареный Карп +175', value: 'Жареный Карп' },
          { label: 'Жареная Щука +250', value: 'Жареная Щука' },
          { label: 'Жареный Сом +350', value: 'Жареный Сом' },
          { label: 'Копченый Осетр +500/-50%', value: 'Копченый Осетр' },
        ],
      },
    ],
  },
  '1.22.hunting-shop': {
    numberLabel: '№ лавки',
    groups: [
      {
        id: 'resource',
        label: 'Ресурсные локации',
        placeholder: 'Масла',
        options: [
          { label: 'Масло против Зверожабов', value: 'Масло против Зверожабов' },
          { label: 'Масло против Гро', value: 'Масло против Гро' },
          { label: 'Масло против Златоглавов', value: 'Масло против Златоглавов' },
          { label: 'Масло против Шишиг', value: 'Масло против Шишиг' },
          { label: 'Масло против Клювозубов', value: 'Масло против Клювозубов' },
          { label: 'Масло против Скорпионов', value: 'Масло против Скорпионов' },
        ],
      },
      {
        id: 'quests',
        label: 'Квесты',
        placeholder: 'Масла',
        options: [
          { label: 'Масло Сказаний', value: 'Масло Сказаний' },
          { label: 'Масло Сокровений', value: 'Масло Сокровений' },
        ],
      },
    ],
  },
  '1.24.bird-market': {
    numberLabel: '№ питомника',
    groups: [
      {
        id: 'dragons',
        label: 'Драконы',
        placeholder: 'Драконы',
        options: [
          { label: 'Великанский дракон', value: 'Великанский дракон' },
          { label: 'Горный дракон', value: 'Горный дракон' },
          { label: 'Призрачный дракон', value: 'Призрачный дракон' },
          { label: 'Речной дракон', value: 'Речной дракон' },
          { label: 'Боевой дракон', value: 'Боевой дракон' },
          { label: 'Огненный дракон', value: 'Огненный дракон' },
        ],
      },
    ],
  },
  '1.27.trade-hall': {
    numberLabel: '№ палатки',
    advancedFilters: true,
    levels: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    groups: [
      {
        id: 'weapon',
        label: 'Оружие',
        placeholder: 'Оружие',
        options: [
          { label: 'Мечи', value: 'swords' },
          { label: 'Топоры', value: 'axes' },
          { label: 'Молоты', value: 'hammers' },          
        ],
      },
      {
        id: 'armor',
        label: 'Броня',
        placeholder: 'Броня',
        options: [
          { label: 'Щиты', value: 'shields' },
          { label: 'Комплекты', value: 'kit' },
          { label: 'Шлемы', value: 'helmet' },
          { label: 'Доспехи', value: 'armor' },
          { label: 'Нарукавники', value: 'gauntlets' },
          { label: 'Перчатки', value: 'gloves' },
          { label: 'Поножи', value: 'leggings' },
          { label: 'Сандалии', value: 'boots' },
          { label: 'Плащи', value: 'cloak' },          
        ],
      },
      {
        id: 'jewelry',
        label: 'Украшения',
        placeholder: 'Украшения',
        options: [
          { label: 'Амулеты', value: 'amulet' },
          { label: 'Кулоны', value: 'pendant' },
          { label: 'Кольца', value: 'ring' },
        ],
      },
    ],
  },
};

export const getTradeFilters = (locationSlug) =>
  TRADE_FILTERS_CONFIG[locationSlug] || { numberLabel: '№ лавки', groups: [] };