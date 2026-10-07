import { useEffect, useState, useMemo } from "react";
import { 
  useGetAppliedSkillsQuery, 
  useCalculateSkillsCostMutation,
  useUpdateCharacterSkillsMutation 
} from '../../entities/character/api/characterApi';
import styles from "./HospitalPage.module.css";
import btn from '../../shared/styles/buttons.module.css';

function HospitalPage({ character }) {  

  // Дизеййбл кнопок пока оплата обрабатывается
  const [isProcessingStat, setIsProcessingStat] = useState(false);
  const [isProcessingMastery, setIsProcessingMastery] = useState(false);
  
  // Сообщения
  const [errorMessageStat, setErrorMessageStat] = useState("");
  const [errorMessageMastery, setErrorMessageMastery] = useState("");
  const [statsSuccessMessage, setStatsSuccessMessage] = useState("");
  const [masterySuccessMessage, setMasterySuccessMessage] = useState("");
  const { data: appliedSkillsData } = useGetAppliedSkillsQuery();
  const [updateSkills] = useUpdateCharacterSkillsMutation();
  const [calculateCost] = useCalculateSkillsCostMutation();

  // Стоимость
  const [statsCost, setStatsCost] = useState(0);
  const [masteryCost, setMasteryCost] = useState(0); 
  

  // Начальные состояния
  const initialStats = {
    power: 0,
    agility: 0,
    lucky: 0,
    endurance: 0,
    intelligence: 0,
  };

  const initialMastery = {
    sword: 0,
    axe: 0,
    hammer: 0,    
  };

  const [statChanges, setStatChanges] = useState(initialStats);
  const [masteryChanges, setMasteryChanges] = useState(initialMastery);

  const statNames = {
    power: "Сила",
    agility: "Ловкость",
    lucky: "Удача",
    endurance: "Выносливость",
    intelligence: "Интеллект",
  };

  const masteryNames = {
    sword: "Мечи",
    axe: "Топоры",
    hammer: "Молоты",
  };

  

  // Данные теперь берутся напрямую из RTK Query
  const history = useMemo(() => appliedSkillsData?.history || {}, [appliedSkillsData]);
  const statsInfo = useMemo(() => appliedSkillsData?.info?.find((i) => i.skill_type === "standard"), [appliedSkillsData]);
  const masteryInfo = useMemo(() => appliedSkillsData?.info?.find((i) => i.skill_type === "mastership"), [appliedSkillsData]);
  
  const displayServerStats = statsInfo?.count_distributions || 0;
  const displayServerMastery = masteryInfo?.count_distributions || 0;


  // --- Логика АТРИБУТОВ (строгая) ---

  // Сколько очков освободили минусами (наш пул)
  const freedStatPoints = Object.values(statChanges).reduce(
    (sum, val) => sum + (val < 0 ? Math.abs(val) : 0), 
    0
  );

  // Сколько очков вложили плюсами (трата пула)
  const spentStatPoints = Object.values(statChanges).reduce(
    (sum, val) => sum + (val > 0 ? val : 0), 
    0
  );

  // Остаток "Доступно для перераспределения"
  const availableStats = freedStatPoints - spentStatPoints;

  // Условия для кнопок:
  // Плюс можно нажать ТОЛЬКО если есть свободные очки в пуле
  const canIncreaseStat = availableStats > 0;


  // --- Логика МАСТЕРСТВА (строгая) ---

  const freedMasteryPoints = Object.values(masteryChanges).reduce(
    (sum, val) => sum + (val < 0 ? Math.abs(val) : 0), 
    0
  );

  const spentMasteryPoints = Object.values(masteryChanges).reduce(
    (sum, val) => sum + (val > 0 ? val : 0), 
    0
  );

  const availableMastery = freedMasteryPoints - spentMasteryPoints;
  const canIncreaseMastery = availableMastery > 0;


  // --- Расчет стоимости ---
  
  // Если мы сняли 1 и добавили 1 - это 1 шаг перераспределения (spentPoints).
  useEffect(() => {
    if (spentStatPoints === 0) {
      setStatsCost(0);
      return;
    }
    const fetchCost = async () => {
      try {
        const response = await calculateCost({ step: spentStatPoints, skill_type: "standard" }).unwrap();
        setStatsCost(response.total_cost);
      } catch (e) { 
        console.error("Ошибка расчета стоимости статов:", e); 
      }
    };
    fetchCost();
  }, [spentStatPoints, calculateCost]);

  useEffect(() => {
    if (spentMasteryPoints === 0) {
      setMasteryCost(0);
      return;
    }
    const fetchCost = async () => {
      try {
        const response = await calculateCost({ step: spentMasteryPoints, skill_type: "mastership" }).unwrap();
        setMasteryCost(response.total_cost);
      } catch (e) { 
        console.error("Ошибка расчета стоимости мастерства:", e); 
      }
    };
    fetchCost();
  }, [spentMasteryPoints, calculateCost]);


  // Таймеры очистки сообщений
  useEffect(() => {
    if (statsSuccessMessage) {
      const t = setTimeout(() => setStatsSuccessMessage(""), 5000);
      return () => clearTimeout(t);
    }
  }, [statsSuccessMessage]);
  useEffect(() => {
    if (masterySuccessMessage) {
      const t = setTimeout(() => setMasterySuccessMessage(""), 5000);
      return () => clearTimeout(t);
    }
  }, [masterySuccessMessage]);


  // --- Обработчики ---

  const handleStatIncrease = (stat) => {
    if (!canIncreaseStat) return; // Блокировка, если availableStats <= 0
    setStatChanges(prev => ({ ...prev, [stat]: prev[stat] + 1 }));
  };

  const handleStatDecrease = (stat) => {
    if (!history) return;
    const maxDecrease = history[`count_applied_${stat}`] || 0;
    const currentDecrease = -statChanges[stat];

    if (currentDecrease >= maxDecrease) return;
    setStatChanges(prev => ({ ...prev, [stat]: prev[stat] - 1 }));
  };

  const handleMasteryIncrease = (mastery) => {
    if (!canIncreaseMastery) return;
    setMasteryChanges(prev => ({ ...prev, [mastery]: prev[mastery] + 1 }));
  };

  const handleMasteryDecrease = (mastery) => {
    if (!history) return;
    const maxDecrease = history[`count_applied_mastership_${mastery}`] || 0;
    const currentDecrease = -masteryChanges[mastery];

    if (currentDecrease >= maxDecrease) return;
    setMasteryChanges(prev => ({ ...prev, [mastery]: prev[mastery] - 1 }));
  };

  // --- Сброс и Очистка ---

  const handleResetStats = () => setStatChanges(initialStats);
  const handleResetMastery = () => setMasteryChanges(initialMastery);

  const resetAfterPaymentStats = () => {
    setStatChanges(initialStats);
    setStatsCost(0);
    setErrorMessageStat("");
  };
  const resetAfterPaymentMastery = () => {
    setMasteryChanges(initialMastery);
    setMasteryCost(0);
    setErrorMessageMastery("");
  };

  // --- Оплата ---

  const handlePaymentStats = async () => {
    if (isProcessingStat) return;
    // Проверка: Должны быть изменения (freed > 0) И всё должно быть распределено (available === 0)
    if (availableStats !== 0) {
      setErrorMessageStat("Необходимо распределить все очки атрибутов");
      return;
    }

    setIsProcessingStat(true);
    try {
      const changeDataStats = {
        character_id: character.id,
        count_applied_power: (history.count_applied_power || 0) + statChanges.power,
        count_applied_agility: (history.count_applied_agility || 0) + statChanges.agility,
        count_applied_lucky: (history.count_applied_lucky || 0) + statChanges.lucky,
        count_applied_endurance: (history.count_applied_endurance || 0) + statChanges.endurance,
        count_applied_intelligence: (history.count_applied_intelligence || 0) + statChanges.intelligence,
      };

      await updateSkills(changeDataStats).unwrap();
      
      setStatsSuccessMessage("Изменения успешно применены!");      
      resetAfterPaymentStats();
      
    } catch (e) {
      const errorData = e?.data || e?.response?.data;
      if (errorData?.error_code === "INSUFFICIENT_FUNDS") {
        setErrorMessageStat(`Недостаточно средств. Требуется: ${Number(errorData.extras?.required_amount ?? 0).toFixed(2)} дт.`);
      } else {
        setErrorMessageStat("Ошибка при обновлении");
      }
      } finally {
    // После любого исхода операции устанавливаем состояние обратно в false
    setIsProcessingStat(false);
    }
  };

  const handlePaymentMastery = async () => {
    if (isProcessingMastery) return;
    if (availableMastery !== 0) {
      setErrorMessageMastery("Необходимо распределить все очки мастерства");
      return;
    }

    setIsProcessingMastery(true);
    try {
      const changeDataMastery = {
        character_id: character.id,
        count_applied_mastership_sword: (history.count_applied_mastership_sword || 0) + masteryChanges.sword,
        count_applied_mastership_axe: (history.count_applied_mastership_axe || 0) + masteryChanges.axe,
        count_applied_mastership_hammer: (history.count_applied_mastership_hammer || 0) + masteryChanges.hammer,
      };

      await updateSkills(changeDataMastery).unwrap();

      setMasterySuccessMessage("Изменения успешно применены!");      
      resetAfterPaymentMastery();

    } catch (e) {
      const errorData = e?.data || e?.response?.data;
      if (errorData?.error_code === "INSUFFICIENT_FUNDS") {
        setErrorMessageMastery(`Недостаточно средств. Требуется: ${Number(errorData.extras?.required_amount ?? 0).toFixed(2)} дт.`);
      } else {
        setErrorMessageMastery("Ошибка при обновлении");
      }
      } finally {
    // После любого исхода операции устанавливаем состояние обратно в false
    setIsProcessingMastery(false);
    }
  };

  if (!character) return null;

  /*const bgUrl = character ? `/images/locations/backgrounds/${character.location_slug}.png` : "";*/
  const getCurrentStatValue = (stat) => character ? character[stat] || 0 : 0;
  const getFutureStatValue = (stat) => getCurrentStatValue(stat) + statChanges[stat];
  const getCurrentMasteryValue = (mastery) => character ? character[`mastership_${mastery}`] || 0 : 0;
  const getFutureMasteryValue = (mastery) => getCurrentMasteryValue(mastery) + masteryChanges[mastery];

  // Кнопка оплаты активна только если мы что-то меняли (freed > 0) И всё раскидали (available === 0)
  const canPayStatsButton = freedStatPoints > 0 && availableStats === 0;
  const canPayMasteryButton = freedMasteryPoints > 0 && availableMastery === 0;

  return (
    <div className={styles.wrapper}>
      <div className={styles.contentBox}>
        <div className={styles.leftRightLayout}>
          <div className={styles.tables}>
            
            {/* АТРИБУТЫ */}
            <div className={styles.borderBox}>
              <table className={styles.statsTable}>  
                <colgroup>
                  <col style={{ width: "30%" }} />
                  <col style={{ width: "15%" }} />
                  <col style={{ width: "5%" }} />
                  <col style={{ width: "20%" }} />
                  <col style={{ width: "10%" }} /> 
                  <col style={{ width: "20%" }} /> 
                </colgroup>          
                <thead>
                  <tr>
                    <th colSpan="6">Атрибуты</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan="6">
                      Количество распределений на уровне: {displayServerStats}
                    </td>
                  </tr>
                  <tr>
                    <td colSpan="6">
                      Доступно для перераспределения: {availableStats}
                    </td>
                  </tr>
                                
                  <tr>
                    <th>Атрибуты</th>
                    <th>Сейчас</th>
                    <th></th>
                    <th></th>
                    <th>Будет</th>
                    <th>Итого</th>
                  </tr>
                  {Object.keys(statNames).map((stat) => {
                    const current = getCurrentStatValue(stat);
                    const change = statChanges[stat];
                    const future = getFutureStatValue(stat);
                    const maxDecrease = history[`count_applied_${stat}`] || 0;

                    return (
                      <tr key={stat}>
                        <td>{statNames[stat]}</td>
                        <td>{current}</td>
                        <td>
                          <span style={{ color: change > 0 ? "#048b04" : change < 0 ? "#a00303" : "#000000" }}>
                            {change > 0 ? `+${change}` : change < 0 ? change : "+0"}
                          </span>
                        </td>
                        <td className={styles.controls}>
                          <button
                            className={styles.controlButton}
                            onClick={() => handleStatDecrease(stat)}
                            disabled={-change >= maxDecrease || isProcessingStat}
                          >
                            −
                          </button>
                          <button
                            className={styles.controlButton}
                            onClick={() => handleStatIncrease(stat)}
                            // Кнопка + неактивна, если нет очков в пуле перераспределения
                            disabled={availableStats <= 0 || isProcessingStat}
                          >
                            +
                          </button>
                        </td>
                        <td>{future}</td>
                        <td>{future}</td>
                      </tr>
                    );
                  })}
                  <tr>
                    <td colSpan="6" className={styles.infoBox}>
                      <div className={styles.balanceItem}>
                        <span>Цена:</span>
                        <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                        <span>{statsCost.toFixed(2)} дт.</span>
                      </div>

                      <div className={styles.messageContainer}>
                        {statsSuccessMessage && <div style={{ color: "#166534" }}>{statsSuccessMessage}</div>}
                        {errorMessageStat && <div style={{ color: "#ef4444" }}>{errorMessageStat}</div>}
                      </div>

                      <div className={styles.buttons}>
                        <button 
                          className={btn.gameButton}
                          style={{ width: '160px' }}
                          onClick={handleResetStats}
                          disabled={isProcessingStat}
                        >
                          Начать с начала
                        </button>
                        <button
                          className={btn.gameButton}
                          style={{ width: '160px' }}
                          onClick={handlePaymentStats}
                          disabled={!canPayStatsButton}
                        >
                          Оплатить операцию
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
                  
            {/* МАСТЕРСТВО */}
            <div className={styles.borderBox}>
              <table className={styles.weaponTable}>
                <colgroup>
                  <col style={{ width: "50%" }} />
                  <col style={{ width: "50%" }} />
                </colgroup>
                <thead>
                  <tr>
                    <th colSpan="2">Мастерство</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan="2">
                      Количество распределений на уровне: {displayServerMastery}
                    </td>
                  </tr>
                  <tr>
                    <td colSpan="2">
                      Доступно для перераспределения: {availableMastery}
                    </td>
                  </tr>
                  <tr>
                    <th colSpan="2">Оружие</th>
                  </tr>                         
                  {Object.keys(masteryNames).map((mastery) => {
                    const change = masteryChanges[mastery];
                    const future = getFutureMasteryValue(mastery);
                    const maxDecrease = history[`count_applied_mastership_${mastery}`] || 0;

                    return (
                      <tr key={mastery}>
                        <td>{masteryNames[mastery]}</td>
                        <td className={styles.controls}>
                          <button
                            className={styles.controlButton}
                            onClick={() => handleMasteryDecrease(mastery)}
                            disabled={-change >= maxDecrease || isProcessingMastery}
                          >
                            −
                          </button>
                          <span style={{ margin: "0 8px" }}>{future}</span>
                          <button
                            className={styles.controlButton}
                            onClick={() => handleMasteryIncrease(mastery)}
                            disabled={availableMastery <= 0 || isProcessingMastery}
                          >
                            +
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                  <tr>
                    <td colSpan="2" className={styles.infoBox}>
                      <div className={styles.balanceItem}>
                        <span>Цена:</span>
                        <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                        <span>{masteryCost.toFixed(2)} дт.</span>
                      </div>

                      <div className={styles.messageContainer}>
                        {masterySuccessMessage && <div style={{ color: "#166534" }}>{masterySuccessMessage}</div>}
                        {errorMessageMastery && <div style={{ color: "#ef4444" }}>{errorMessageMastery}</div>}
                      </div>

                      <div className={styles.buttons}>
                        <button 
                          className={btn.gameButton}
                          style={{ width: '160px' }}
                          onClick={handleResetMastery}
                          disabled={isProcessingMastery}
                        >
                          Начать с начала
                        </button>
                        <button
                          className={btn.gameButton}
                          style={{ width: '160px' }}
                          onClick={handlePaymentMastery}
                          disabled={!canPayMasteryButton}
                        >
                          Оплатить операцию
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>                  
            </div>
          </div>  
        </div>
      </div>
    </div>
  );
}

export default HospitalPage;