export const adaptItemForCard = (item) => {
  if (item.item) return item;

  // Детальная инфа может быть вложена (sale items, рецепты)
  const details = item.item_details?.item || {};

  // Определение расы для эликсиров по названию
  const getRaceFromElixirName = (itemName) => {
    if (!itemName) return null;
    
    const orcElixirs = [
      'Эликсир Нечистая сила', 'Эликсир Укус Пчелы', 'Эликсир Медвежья песня',
      'Эликсир Трезвость', 'Эликсир Полная Луна', 'Эликсир Сила Действия',
      'Эликсир Скорость Тигра', 'Эликсир Шепот Фортуны'
    ];
    
    const elfElixirs = [
      'Эликсир Плач Неразумных', 'Эликсир Живая Вода', 'Эликсир Розовый Свет',
      'Эликсир Легкий Путь', 'Эликсир Второе Дыхание', 'Эликсир Сила Духа',
      'Эликсир Скорость Ястреба', 'Эликсир Танец Фортуны'
    ];
    
    const humanElixirs = [
      'Эликсир Свирепый Воин', 'Эликсир Преследование', 'Эликсир Момент Истины',
      'Эликсир Белый День', 'Эликсир Энергия', 'Эликсир Сила Разума',
      'Эликсир Скорость Звука', 'Эликсир Улыбка Фортуны'
    ];
    
    if (orcElixirs.includes(itemName)) return 'orc';
    if (elfElixirs.includes(itemName)) return 'elf';
    if (humanElixirs.includes(itemName)) return 'human';
    return null;
  };

  // Поддерживаем оба формата: item_name/item_slug (лавка) и name/slug (рецепты)
  const itemName = item.item_name || item.name || details.name || 'Предмет';
  const itemType = item.item_type || details.item_type || 'misc';
  
  let race = item.race || details.race || null;
  if (!race && itemType === 'elixir') {
    race = getRaceFromElixirName(itemName);
  }

  return {
    item: {
      name: itemName,
      item_type: itemType,
      slug: item.item_slug || item.slug || details.slug || '',
      price: item.item_price ?? item.price ?? item.recipe_price ?? details.price ?? 0,
      weight: item.weight ?? details.weight ?? 0,
      parameters: item.parameters || details.parameters || {},
      ability_parameters: item.ability_parameters || details.ability_parameters || {},
      minimal_level: item.minimal_level ?? details.minimal_level ?? 0,
      race: race,
      description: item.description || details.description || '',
    },
    amount: item.amount ?? 1,
    wear: item.wear ?? 0,
    expired_date: item.expired_date || null,
    used_count: item.used_count ?? 0,
  };
};