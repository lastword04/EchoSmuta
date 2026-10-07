export const raceLabels = {
  human: 'Человек',
  orc: 'Орк',
  elf: 'Эльф'
};


export const getRaceShield = (race, isMale) => {
  const gender = isMale ? 'male' : 'female';
  return `/images/shields/${race}_${gender}_shield.gif`;
};

export const getRaceDisplayName = (race) => {
    return raceLabels[race] || race;
  };

export const getGenderDisplayName = (isMale) => {
    return isMale ? 'Мужчина' : 'Женщина';
  };