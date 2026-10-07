import { useState, useEffect, useRef } from 'react';
import { useGetMealsQuery, useBuyMealMutation } from '../../entities/economy/api/tavernApi';
import { parseUtcDate } from '../../shared/lib/utils/utcDate';
import { useErrorToast } from '../../shared/hooks/ui/useErrorToast';
import ErrorToast from '../../shared/ui/ErrorToast/ErrorToast';
import { getErrorMessage } from '../../shared/lib/error/getErrorMessage';
import styles from './TavernPage.module.css';
import btn from '../../shared/styles/buttons.module.css';

function TavernPage({ character }) {  
  const { data: menuData, refetch } = useGetMealsQuery();
  const [buyMeal] = useBuyMealMutation();   
  const { currentError, showError } = useErrorToast();

  const [rotationTimeLeft, setRotationTimeLeft] = useState('');
  const [buyingMealId, setBuyingMealId] = useState(null);
  const [cooldownActive, setCooldownActive] = useState(false);
  const [cooldownLeft, setCooldownLeft] = useState('');

  const meals = menuData?.meals || [];
  const nextRotationAt = menuData?.next_rotation_at;

  const rotationRefetchedRef = useRef(false);

  // Таймеры ротации и кулдауна
  useEffect(() => {
    const updateTimer = () => {
      const now = Date.now();

      // Таймер ротации
      if (nextRotationAt) {
        const rotationDate = parseUtcDate(nextRotationAt);
        const diff = rotationDate - now;
        if (diff > 0) {
          const hours = Math.floor(diff / (1000 * 60 * 60));
          const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
          setRotationTimeLeft(`${String(hours).padStart(2, '0')}ч ${String(minutes).padStart(2, '0')}мин`);
        } else {
          setRotationTimeLeft('00ч 00мин');
          if (!rotationRefetchedRef.current) {
            rotationRefetchedRef.current = true;
            refetch();
          }
        }
      }

      // Таймер кулдауна
      if (character?.food_cooldown_until) {
        const cd = parseUtcDate(character.food_cooldown_until);
        const diff = cd - now;
        if (diff > 0) {
          const mins = Math.floor(diff / (1000 * 60));
          const secs = Math.floor((diff % (1000 * 60)) / 1000);
          
          if (mins > 0) {
            setCooldownLeft(`${mins} мин`);
          } else {
            setCooldownLeft(`${secs} сек`);
          }
        } else {
          setCooldownLeft('');
          setCooldownActive(false);
        }
      } else {
        setCooldownLeft('');
        setCooldownActive(false);
      }
    };
    
    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [nextRotationAt, character?.food_cooldown_until, refetch]);

  // Сброс флага таймера
  useEffect(() => {
    rotationRefetchedRef.current = false;
  }, [nextRotationAt]);

  const handleBuy = async (meal) => {
    setBuyingMealId(meal.id);
    try {
      await buyMeal(meal.id).unwrap();
      // Системка придёт в чат через WebSocket
      setCooldownActive(false);
    } catch (e) {
      const errorData = e?.data || e?.response?.data;
      const message = errorData?.detail || errorData?.message || 'Ошибка при покупке';

      // Ошибку кулдауна превращаем в живое сообщение
      if (message.includes('недавно ели')) {
        setCooldownActive(true);
      } else {
        // Остальные ошибки — в toast
        showError(getErrorMessage(e, 'Ошибка при покупке'));
        setCooldownActive(false);
      }
    } finally {
      setBuyingMealId(null);
    }
  };

  return (
    <div className={styles.wrapper}>
      <ErrorToast message={currentError} />
      <div className={styles.contentBox}>
        <div className={styles.tables}>
          {/* Заголовок */}
          <div className={styles.tavernTitle}>
            Трактир "Три корочки хлеба"
          </div>

          {/* Таймер ротации */}
          <div className={styles.timers}>
            <div className={styles.timerItem}>
              <span className={styles.timerLabel}>Следующая смена блюд через:</span>
              <span className={styles.timerValue}>{rotationTimeLeft || '—'}</span>
            </div>
          </div>

          {/* Живое сообщение кулдауна */}
          {cooldownActive && (
            <div className={styles.messageContainer}>
              <div className={styles.errorMessage}>
                Вы недавно ели. Подождите ещё {cooldownLeft}.
              </div>
            </div>
          )}

          {/* Таблица */}
          <div className={styles.borderBox}>
            <table className={styles.mealsTable}>
              <colgroup>
                <col className={styles.colImage} />
                <col className={styles.colName} />
                <col className={styles.colEffects} />
                <col className={styles.colPrice} />
                <col className={styles.colStock} />
                <col className={styles.colAction} />
              </colgroup>
              <thead>
                <tr>
                  <th></th>
                  <th>Блюдо</th>
                  <th>Эффекты</th>
                  <th>Цена</th>
                  <th>Порций</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {meals.map((meal) => {
                  return (
                    <tr key={meal.id} className={styles.tableRow}>
                      <td className={styles.imageCell}>
                        <img
                          src={`/images/tavern/meals/${meal.slug}.png`}
                          alt={meal.name}
                          className={styles.mealImage}
                        />
                      </td>
                      <td className={styles.mealNameCell}>{meal.name}</td>
                      <td className={styles.effectsCell}>
                        {meal.health_restore > 0 && (
                          <span className={styles.effect}>
                            Здоровье: +{meal.health_restore}
                          </span>
                        )}
                        {meal.tiredness_restore_percent > 0 && (
                          <span className={styles.effect}>
                            Усталость: -{Math.round(meal.tiredness_restore_percent * 100)}%
                          </span>
                        )}
                      </td>
                      <td className={styles.priceCell}>
                        <span className={styles.priceValue}>
                          <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                          {Number(meal.ducats_price).toFixed(2)} дт.
                        </span>
                      </td>
                      <td className={styles.stockCell}>
                        {meal.stock}
                      </td>
                      <td className={styles.actionCell}>
                        <button
                          className={btn.textLinkDanger}
                          onClick={() => handleBuy(meal)}
                          disabled={buyingMealId === meal.id}
                        >
                          Купить
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TavernPage;