import { useState } from "react";
import styles from "./ImprovementsModal.module.css";

export const ImprovementsModal = ({ character, onClose, freePoints, freeMasteryPoints, onSave }) => {
  const [baseStats, setBaseStats] = useState({
    strength: { current: character.power || 0, bonus: 0, final: character.power || 0 },
    agility: { current: character.agility || 0, bonus: 0, final: character.agility || 0 },
    luck: { current: character.lucky || 0, bonus: 0, final: character.lucky || 0 },
    endurance: { current: character.endurance || 0, bonus: 0, final: character.endurance || 0 },
    intelligence: { current: character.intelligence || 0, bonus: 0, final: character.intelligence || 0 },
  });

  const [weaponMastery, setWeaponMastery] = useState({
    swords: { current: character.mastership_sword || 0, bonus: 0 },
    axes: { current: character.mastership_axe || 0, bonus: 0 },
    hammers: { current: character.mastership_hammer || 0, bonus: 0 },
  });

  const spentPoints = Object.values(baseStats).reduce((sum, s) => sum + s.bonus, 0);
  const remainingPoints = freePoints - spentPoints;
  const spentMastery = Object.values(weaponMastery).reduce((sum, w) => sum + w.bonus, 0);
  const remainingMasteryPoints = freeMasteryPoints - spentMastery;

  const [saveMessage, setSaveMessage] = useState("");

  const statNames = {
    strength: "Сила",
    agility: "Ловкость",
    luck: "Удача",
    endurance: "Выносливость",
    intelligence: "Интеллект",
  };

  const weaponNames = {
    swords: "Мечи",
    axes: "Топоры",
    hammers: "Молоты",
  };

  const handleStatIncrease = (stat) => {
    if (remainingPoints > 0) {
      setBaseStats(prev => ({
        ...prev,
        [stat]: {
          ...prev[stat],
          bonus: prev[stat].bonus + 1,
          final: prev[stat].current + prev[stat].bonus + 1,
        }
      }));      
    }
  };

  const handleStatDecrease = (stat) => {
    if (baseStats[stat].bonus > 0) {
      setBaseStats(prev => ({
        ...prev,
        [stat]: {
          ...prev[stat],
          bonus: prev[stat].bonus - 1,
          final: prev[stat].current + prev[stat].bonus - 1,
        }
      }));     
    }
  };

  const handleMasteryIncrease = (weapon) => {
    if (remainingMasteryPoints > 0) {
      setWeaponMastery(prev => ({
        ...prev,
        [weapon]: {
          ...prev[weapon],
          bonus: prev[weapon].bonus + 1,
        }
      }));      
    }
  };

  const handleMasteryDecrease = (weapon) => {
    if (weaponMastery[weapon].bonus > 0) {
      setWeaponMastery(prev => ({
        ...prev,
        [weapon]: {
          ...prev[weapon],
          bonus: prev[weapon].bonus - 1,
        }
      }));      
    }
  };

  const handleSave = async () => {
    let pointsSpent = false;

  Object.values(baseStats).forEach(stat => {
    if (stat.bonus > 0) {
      pointsSpent = true;
    }
  });

  Object.values(weaponMastery).forEach(mastery => {
    if (mastery.bonus > 0) {
      pointsSpent = true;
    }
  });

  // Если очки не были использованы совсем, выдаём ошибку
  if (!pointsSpent) {
    setSaveMessage("Необходимо распределить хотя бы одно очко");
    return;
  }
    

    // Формируем данные об изменениях
    const updatedData = {
      character_id: character.id,
      count_applied_power: baseStats.strength.bonus,
      count_applied_agility: baseStats.agility.bonus,
      count_applied_lucky: baseStats.luck.bonus,
      count_applied_endurance: baseStats.endurance.bonus,
      count_applied_intelligence: baseStats.intelligence.bonus,
      count_applied_mastership_sword: weaponMastery.swords.bonus,
      count_applied_mastership_axe: weaponMastery.axes.bonus,
      count_applied_mastership_hammer: weaponMastery.hammers.bonus,
    };

    if (onSave) {
      try {
        await onSave(updatedData);
        onClose();
      } catch {
        setSaveMessage("Ошибка сохранения");
      }
    }
  };  

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>Улучшения основных навыков</h2>
          <button className={styles.closeButton} onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Основные характеристики */}
        <div className={styles.section}>
          <div className={styles.pointsInfo}>
            Свободные очки атрибутов: <span className={styles.pointsCount}>{remainingPoints > 0 ? remainingPoints : '0'}</span>
          </div>

          <table className={styles.statsTable}>
            <thead>
              <tr>
                <th>Атрибуты</th>
                <th>Сейчас</th>
                <th></th>
                <th></th>
                <th>Будет</th>
                <th>Итого</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(baseStats).map(([key, value]) => (
                <tr key={key}>
                  <td className={styles.statName}>{statNames[key]}</td>
                  <td>{value.current}</td>
                  <td>
                    <span className={styles.bonus}>
                    +{value.bonus}
                    </span>
                  </td>
                  <td className={styles.controls}>
                    <button
                      className={styles.controlButton}
                      onClick={() => handleStatDecrease(key)}
                      disabled={value.bonus === 0}
                    >
                      −
                    </button>
                    <button
                      className={styles.controlButton}
                      onClick={() => handleStatIncrease(key)}
                      disabled={remainingPoints <= 0}  
                    >
                      +
                    </button>
                  </td>
                  <td>{value.current + value.bonus}</td>
                  <td className={styles.finalValue}>{value.final}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Мастерство владения оружием */}
        <div className={styles.section}>
          
          <div className={styles.pointsInfo}>
            Свободные очки мастерства: <span className={styles.pointsCount}>{remainingMasteryPoints > 0 ? remainingMasteryPoints : '0'}</span>
          </div>
          <table className={styles.masteryTable}>
            <thead>
              <tr>
                <th colSpan="2">Оружие</th>
              </tr>
            </thead>

          
            <tbody>
              {Object.entries(weaponMastery).map(([key, value]) => (
                <tr key={key}>
                  <td className={styles.weaponName}>{weaponNames[key]}</td>
                  <td className={styles.controls}>
                    <button
                      className={styles.controlButton}
                      onClick={() => handleMasteryDecrease(key)}
                      disabled={value.bonus === 0}
                    >
                      −
                    </button>
                    <span className={styles.masteryValue}>{value.current + value.bonus}</span>
                    <button
                      className={styles.controlButton}
                      onClick={() => handleMasteryIncrease(key)}
                      disabled={remainingMasteryPoints <= 0}
                    >
                      +
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Футер с кнопками */}
        <div className={styles.footer}>
          <div className={styles.leftSection}>
            {saveMessage && (
              <span className={`${styles.saveMessage} ${
                saveMessage.includes('Необходимо') || saveMessage.includes('Ошибка')
                  ? styles.error
                  : styles.success
              }`}>
                {saveMessage}
              </span>
            )}
          </div>
          
          <button 
            className={styles.saveButton} 
            onClick={handleSave}
          >
            Сохранить
          </button>
          
        </div>
      </div>
    </div>
  );
};