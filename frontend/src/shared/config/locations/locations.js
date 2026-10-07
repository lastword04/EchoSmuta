export const AVALON_NUMBER = 1;
export const NIGHBORHOOD_AVALON_NUMBER = 2;

export const locations = {
  city: [
    {
      title: 'Дворцовая Площадь',
      items: [
        { name: 'Академия', slug: `${AVALON_NUMBER}.1.academy` },
        { name: 'Арена Людей', slug: `${AVALON_NUMBER}.2.arena-humans` },
        { name: 'Арена Орков', slug: `${AVALON_NUMBER}.3.arena-orcs` },
        { name: 'Арена Раздора', slug: `${AVALON_NUMBER}.4.arena-chaos` },
        { name: 'Арена Эльфов', slug: `${AVALON_NUMBER}.5.arena-elves` },
        { name: 'Дворец', slug: `${AVALON_NUMBER}.6.palace` },
        { name: 'Дворец бракосочетаний', slug: `${AVALON_NUMBER}.7.wedding-palace` },
        { name: 'Храм', slug: `${AVALON_NUMBER}.8.temple` }
      ]
    },

    {
      title: 'Мастеровая Площадь',
      items: [
        { name: 'Аптека', slug: `${AVALON_NUMBER}.9.pharmacy` },
        { name: 'Больница', slug: `${AVALON_NUMBER}.10.hospital` },
        { name: 'Вход в Лабиринт', slug: `${AVALON_NUMBER}.11.labyrinth-entrance` },
        { name: 'Гостиница', slug: `${AVALON_NUMBER}.12.inn` },
        { name: 'Кузница', slug: `${AVALON_NUMBER}.13.forge` },
        { name: 'Ремонтная Мастерская', slug: `${AVALON_NUMBER}.14.repair-shop` },
        { name: 'Харчевня', slug: `${AVALON_NUMBER}.15.tavern` },
        { name: 'Ювелиры', slug: `${AVALON_NUMBER}.16.jewelers` }
      ]
    },

    {
      title: 'Привокзальная Площадь',
      items: [
        { name: 'Вокзал', slug: `${AVALON_NUMBER}.17.station` },
        { name: 'Тюрьма', slug: `${AVALON_NUMBER}.18.prison` },
        { name: 'Частные дома', slug: `${AVALON_NUMBER}.19.residential-area` }
      ]
    },

    {
      title: 'Торговая Площадь',
      items: [
        { name: 'Магазин', slug: `${AVALON_NUMBER}.20.shop` },
        { name: 'Мебельная Лавка', slug: `${AVALON_NUMBER}.21.furniture-shop` },
        { name: 'Охотничья Лавка', slug: `${AVALON_NUMBER}.22.hunting-shop` },
        { name: 'Питомник', slug: `${AVALON_NUMBER}.24.bird-market` },
        { name: 'Подарочный Магазин', slug: `${AVALON_NUMBER}.23.gift-shop` },
        { name: 'Рыбная Лавка', slug: `${AVALON_NUMBER}.25.fish-shop` },
        { name: 'Скупочный Магазин', slug: `${AVALON_NUMBER}.26.pawn-shop` },
        { name: 'Торговая Палата', slug: `${AVALON_NUMBER}.27.trade-hall` }
      ]
    }
  ],

  resources: [
    // --- Блок 1 ---
    { empty: true },
    { name: 'Авалон', position: 'left', slug: `${AVALON_NUMBER}.28.city` },
    { name: 'Пещера Стонов', position: 'left', slug: `${AVALON_NUMBER}.29.stone-cave` },
    { name: 'Портал', position: 'left', slug: `${AVALON_NUMBER}.30.portal` },

    // --- Блок 2 ---
    { empty: true },
    { name: 'Болото', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.1.swamp`, resourceName: 'Растения', action: "Собирать", profession: "травника"},
    { name: 'Лес', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.5.forest`, resourceName: 'Деревья', action: "Рубить", profession: "лесоруба"},
    { name: 'Озеро', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.4.lake`, resourceName: 'Рыба', action: "Забросить", profession: "рыбака"},
    { name: 'Пески', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.6.sands`, resourceName: 'Находки', action: "Исследовать", profession: "исследователя"},
    { name: 'Прииск', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.3.mine`, resourceName: 'Самоцветы', action: "Добывать", profession: "старателя"},
    { name: 'Шахта', position: 'right', slug: `${NIGHBORHOOD_AVALON_NUMBER}.2.shaft`, resourceName: 'Руда', action: "Копать", profession: "рудокопа"},

    // --- Блок 3 ---
    { empty: true },
    { name: 'Замок с Привидениями', position: 'left', slug: `${AVALON_NUMBER}.31.ghost-castle` },
    { name: 'Замок Стали', position: 'left', slug: `${AVALON_NUMBER}.32.steel-castle` },
    { name: 'Замок Белого Камня', position: 'left', slug: `${AVALON_NUMBER}.33.white-stone-castle` },
    { name: 'Замок Ветра', position: 'left', slug: `${AVALON_NUMBER}.34.wind-castle` },

    // --- Блок 4 ---
    { empty: true },
    { name: 'Местоположение', position: 'left', slug: 'position' }
  ]
};

export const locationsUrlMap = {
  [`${NIGHBORHOOD_AVALON_NUMBER}.1.swamp`]: "resources",
  [`${NIGHBORHOOD_AVALON_NUMBER}.5.forest`]: "resources",
  [`${NIGHBORHOOD_AVALON_NUMBER}.4.lake`]: "resources",
  [`${NIGHBORHOOD_AVALON_NUMBER}.6.sands`]: "resources",
  [`${NIGHBORHOOD_AVALON_NUMBER}.3.mine`]: "resources",
  [`${NIGHBORHOOD_AVALON_NUMBER}.2.shaft`]: "resources",
  [`${AVALON_NUMBER}.17.station`]: "station",
  [`${AVALON_NUMBER}.10.hospital`]: "hospital",
  [`${AVALON_NUMBER}.27.trade-hall`]: "city-trade",
  [`${AVALON_NUMBER}.26.pawn-shop`]: "pawn-shop",
    
}

export const isResourceLocation = (slug) => {
  for (const loc of locations.resources) {
    if(loc.slug === slug) return true;
  }
  return false;
}

export const getUrlForLocationSlug = (slug) => {
  return locationsUrlMap[slug];
}

// Создаем объект для быстрого доступа к названиям локаций
const locationNames = {};

// Заполняем объект названиями локаций
locations.city.forEach(cat => {
  cat.items.forEach(loc => {
    locationNames[loc.slug] = loc.name;
  });
});
// Добавляем названия локаций из resources
locations.resources.forEach(loc => {
  locationNames[loc.slug] = loc.name;
});

// Добавляем названия workshop локаций
locationNames['1.35.laboratory'] = 'Лаборатория';
locationNames['1.36.kitchen'] = 'Кухня';
locationNames['1.37.carpentry-workshop'] = 'Столярная мастерская';
locationNames['1.38.hunter-workshop'] = 'Мастерская охотника';
locationNames['1.39.incubator'] = 'Инкубатор';

export const getLocationName = (slug) => {
  // Виртуальный slug гостиницы — показываем как обычное имя локации.
  // (Для дома лейбл даёт useChatRoomLabel, getLocationName его не касается.)
  if (slug === 'inn:inside') return 'Гостиница';
  return locationNames[slug] || slug;
};

export const getLocationNameAndIsResourceLocation = (slug) => {
  for (const cat of locations.city) {
    for (const loc of cat.items) {
      if (loc.slug === slug) return { locationName: loc.name, isResourceLocation: false };
    }
  }

  for (const loc of locations.resources) {
    if (loc.slug === slug) return { locationName: loc.name, isResourceLocation: true };
  }

  return { locationName: slug, isResourceLocation: false };
};

export const getResourceBySlug = (slug) => {
  for (const cat of locations.resources) {
    if(cat.resourceName && cat.slug === slug){
      return cat;
    }
  }
  return slug;
}

// Торговые локации с магазинами
export const TRADE_LOCATIONS = [
  `${AVALON_NUMBER}.21.furniture-shop`,
  `${AVALON_NUMBER}.22.hunting-shop`,
  `${AVALON_NUMBER}.24.bird-market`,
  `${AVALON_NUMBER}.25.fish-shop`,
  `${AVALON_NUMBER}.9.pharmacy`,
  `${AVALON_NUMBER}.27.trade-hall`,
  `${AVALON_NUMBER}.13.forge`,
  `${AVALON_NUMBER}.16.jewelers`,
];

// Локации мастерских (workshop)
export const WORKSHOP_LOCATIONS = [
  `${AVALON_NUMBER}.35.laboratory`,
  `${AVALON_NUMBER}.36.kitchen`,
  `${AVALON_NUMBER}.37.carpentry-workshop`,
  `${AVALON_NUMBER}.38.hunter-workshop`,
  `${AVALON_NUMBER}.39.incubator`,
];

// Проверка, является ли локация торговой
export const isTradeLocation = (locationSlug) => {
  return TRADE_LOCATIONS.includes(locationSlug) || WORKSHOP_LOCATIONS.includes(locationSlug);
};
