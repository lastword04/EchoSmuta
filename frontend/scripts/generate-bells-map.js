import fs from 'fs';

// Читаем bells-info.json
const bellsInfoRaw = fs.readFileSync('public/bells-info.json', 'utf8');
const bellsInfo = JSON.parse(bellsInfoRaw);

const bellMap = {};

// Заполняем маппинг из bells-info.json
Object.entries(bellsInfo).forEach(([folder, numbers]) => {
  numbers.forEach(number => {
    bellMap[number.toString()] = folder;
  });
});

// Сохраняем в файл
fs.writeFileSync('public/bells-map.json', JSON.stringify(bellMap, null, 2));

console.log('bells-map.json успешно создан из bells-info.json!');