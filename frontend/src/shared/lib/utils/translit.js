const translitMap = {
  a: 'а', b: 'б', v: 'в', g: 'г', d: 'д', e: 'е', yo: 'ё', zh: 'ж', z: 'з',
  i: 'и', j: 'й', k: 'к', l: 'л', m: 'м', n: 'н', o: 'о', p: 'п', r: 'р',
  s: 'с', t: 'т', u: 'у', f: 'ф', h: 'х', ts: 'ц', ch: 'ч', sh: 'ш', shch: 'щ',
  yu: 'ю', ya: 'я', x: 'кс', c: 'ц',
  A: 'А', B: 'Б', V: 'В', G: 'Г', D: 'Д', E: 'Е', Yo: 'Ё', Zh: 'Ж', Z: 'З',
  I: 'И', J: 'Й', K: 'К', L: 'Л', M: 'М', N: 'Н', O: 'О', P: 'П', R: 'Р',
  S: 'С', T: 'Т', U: 'У', F: 'Ф', H: 'Х', Ts: 'Ц', Ch: 'Ч', Sh: 'Ш', Shch: 'Щ',
  Yu: 'Ю', Ya: 'Я', X: 'Кс', C: 'Ц'
};

export const transliterate = (text) => {
  let result = text;
  const sortedKeys = Object.keys(translitMap).sort((a, b) => b.length - a.length);
  for (const key of sortedKeys) {
    result = result.replace(new RegExp(key, 'g'), translitMap[key]);
  }
  return result;
};