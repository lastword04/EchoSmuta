import { useState, useEffect, useMemo } from 'react';
import { useDispatch } from 'react-redux';
import { characterApi } from '../../entities/character/api/characterApi';
import { moveOnlineUser } from '../../app/providers/lib/onlineCacheSync';
import { storeRef } from '../../shared/store/storeRef';
import { chatApi } from '../../entities/chat/api/chatApi';
import { 
  useGetRestStatusQuery,
  useRentRoomMutation,
  useExitRoomMutation,
  useEnterRoomMutation,
  useSyncExpiryMutation,
} from '../../entities/character/api/restApi';
import { commitCharacterFields, commitChatRoom } from '../../entities/character/store/characterSlice';
import { parseUtcDate } from '../../shared/lib/utils/utcDate';
import { useErrorToast } from '../../shared/hooks/ui/useErrorToast';
import ErrorToast from '../../shared/ui/ErrorToast/ErrorToast';
import { getErrorMessage } from '../../shared/lib/error/getErrorMessage';
import styles from './InnPage.module.css';
import btn from '../../shared/styles/buttons.module.css';

function InnPage({ character }) {
  const { data: statusData, refetch } = useGetRestStatusQuery();
  const [rentRoom] = useRentRoomMutation();
  const [exitRoom] = useExitRoomMutation();
  const [enterRoom] = useEnterRoomMutation();
  const [syncExpiry] = useSyncExpiryMutation();
  const dispatch = useDispatch();
  const { currentError, showError } = useErrorToast();
 
  const [rentingDays, setRentingDays] = useState(null);      
  const [transitioning, setTransitioning] = useState(false);   
  const [optimistic, setOptimistic] = useState(null);  

  // Свежие данные от сервера мержим с оптимистичным override поверх.
  const rawEffectiveStatus = useMemo(
      () => (optimistic ? { ...(statusData || {}), ...optimistic } : statusData),
      [optimistic, statusData]
  );

  const rawExpiresAt = rawEffectiveStatus?.expires_at;

  // Секундный тик — единственное, что двигает таймер.
  const [nowTick, setNowTick] = useState(Date.now());
  useEffect(() => {
      const interval = setInterval(() => setNowTick(Date.now()), 1000);
      return () => clearInterval(interval);
  }, []);

  const timeLeft = useMemo(() => {
      if (!rawExpiresAt) return '';
      const diff = parseUtcDate(rawExpiresAt) - nowTick;
      if (diff <= 0) return '';
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      return `${days}дн. ${hours}ч. ${minutes}м.`;
  }, [rawExpiresAt, nowTick]);

  const expiredLocal = !!rawExpiresAt && parseUtcDate(rawExpiresAt) <= nowTick;

  // Финальный статус: если локально знаем, что аренда истекла — показываем
  // это сразу, не дожидаясь, пока syncExpiry почистит запись на бэке.
  const effectiveStatus = useMemo(() => {
      if (!rawEffectiveStatus) return rawEffectiveStatus;
      if (expiredLocal && rawEffectiveStatus.has_active_rental) {
          return {
              ...rawEffectiveStatus,
              has_active_rental: false,
              available_rooms: typeof rawEffectiveStatus.available_rooms === 'number'
                  ? rawEffectiveStatus.available_rooms + 1
                  : rawEffectiveStatus.available_rooms,
          };
      }
      return rawEffectiveStatus;
  }, [rawEffectiveStatus, expiredLocal]);

  const hasActiveRental = effectiveStatus?.has_active_rental;
  const roomNumber = effectiveStatus?.room_number;
  const prices = effectiveStatus?.prices || {};
  const availableRooms = effectiveStatus?.available_rooms;
  const maxRooms = effectiveStatus?.max_rooms;

  const restState = (() => {
      if (expiredLocal) return 'entrance';
      if (optimistic?.rest_state) return optimistic.rest_state;
      if (effectiveStatus && effectiveStatus.has_active_rental === false) return 'entrance';
      return character?.rest_state ?? effectiveStatus?.rest_state;
  })(); 

  useEffect(() => {
      // При заходе в гостиницу: серверный cleanup истёкших аренд + свежий статус.
      (async () => {
          try {
              await syncExpiry().unwrap();
          } catch {
              // не роняем UI, если endpoint временно недоступен
          }
          refetch();
          dispatch(characterApi.util.invalidateTags(['Character']));
      })();
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Живое обновление счётчика номеров: бэк шлёт rest_state_updated, когда
  // кто угодно в гостинице арендует/выходит/у него истекла аренда.
  // Мы просто перечитываем статус — сервер сам решит, что показать.
  useEffect(() => {
    const handleRestUpdate = (event) => {
      const incomingSlug = event.detail?.location_slug;
      // Реагируем, только если событие про нашу локацию (1.12.inn).
      if (incomingSlug && character?.location_slug === incomingSlug) {
        refetch();
      }
    };
    window.addEventListener('rest-updated', handleRestUpdate);
    return () => window.removeEventListener('rest-updated', handleRestUpdate);
  }, [character?.location_slug, refetch]);
  

  useEffect(() => {
    if (!expiredLocal) return;
    let cancelled = false;
    // Аренда истекла → вышли из номера. Переключаем чат в общее
    // пространство локации и убираем себя из кэша inn:inside.
    // Без этого chatRoomId остаётся 'inn:inside', список показывает
    // чужие ники из номеров, а себя там нет (бэк уже выкинул).
    const globalState = chatApi.endpoints.getOnlineCharacters.select({
      locationSlug: null, limit: 50, offset: 0,
    })(storeRef.current.getState());
    const userObject = globalState?.data?.objects?.find(u => u.id === character.id);
    if (userObject) {
      moveOnlineUser(dispatch, {
        characterId: character.id,
        oldLocationSlug: 'inn:inside',
        newLocationSlug: character.location_slug,
        userData: userObject,
      });
    }
    dispatch(commitChatRoom(character.location_slug));
    (async () => {
      try {
        await syncExpiry().unwrap();
      } catch {
        // Сервер недоступен: effective_state в get_status спасёт рендер
      }
      if (!cancelled) {
        dispatch(characterApi.util.invalidateTags(['Character']));
      }
    })();
    return () => { cancelled = true; };
  }, [expiredLocal, syncExpiry, dispatch, character.location_slug, character.id]);

  // Автоматический refetch при смене состояния
  useEffect(() => {
    if (character?.rest_state !== restState) {
      refetch();
    }
  }, [character?.rest_state, restState, refetch]);
  

  const handleRent = async (days) => {
      setRentingDays(days);
      try {
          const rental = await rentRoom(days).unwrap();
          
          setNowTick(Date.now()); 
          setOptimistic({
              rest_state: 'inside',
              has_active_rental: true,
              expires_at: rental.expires_at,
              room_number: rental.room_number,
              days: rental.days,
              available_rooms: typeof availableRooms === 'number'
                  ? Math.max(0, availableRooms - 1)
                  : undefined,
          });

          // Оптимистично переводим себя из «снаружи» в комнату номера.
          // Без этого globalData продолжает показывать тебя снаружи, и
          // фильтр «внутри номера» тебя не находит.
          const globalState = chatApi.endpoints.getOnlineCharacters.select({
            locationSlug: null, limit: 50, offset: 0,
          })(storeRef.current.getState());
          const userObject = globalState?.data?.objects?.find(u => u.id === character.id);
          if (userObject) {
            moveOnlineUser(dispatch, {
              characterId: character.id,
              oldLocationSlug: character.location_slug,
              newLocationSlug: 'inn:inside',
              userData: userObject,
            });
          }

          dispatch(commitCharacterFields({ rest_state: 'inside' }));
          dispatch(commitChatRoom('inn:inside'));

          dispatch(characterApi.util.invalidateTags(['Character']));
          refetch().finally(() => setOptimistic(null));
      } catch (e) {
          showError(getErrorMessage(e, 'Ошибка при аренде'));
      } finally {
          setRentingDays(null);
      }
  };

  const handleExit = async () => {
      setTransitioning(true);
      try {
          await exitRoom().unwrap();
          setOptimistic({ rest_state: 'entrance' });

          // Симметрично: возвращаем себя из комнаты в локацию.
          const globalState = chatApi.endpoints.getOnlineCharacters.select({
            locationSlug: null, limit: 50, offset: 0,
          })(storeRef.current.getState());
          const userObject = globalState?.data?.objects?.find(u => u.id === character.id);
          if (userObject) {
            moveOnlineUser(dispatch, {
              characterId: character.id,
              oldLocationSlug: 'inn:inside',
              newLocationSlug: character.location_slug,
              userData: userObject,
            });
          }

          dispatch(commitCharacterFields({ rest_state: 'entrance' }));
          dispatch(commitChatRoom(character.location_slug));
          dispatch(characterApi.util.invalidateTags(['Character']));
          refetch().finally(() => setOptimistic(null));
      } catch (e) {
          showError(getErrorMessage(e, 'Ошибка при выходе'));
      } finally {
          setTransitioning(false);
      }
  };

    const handleEnter = async () => {
      setTransitioning(true);
      try {
          await enterRoom().unwrap();
          setOptimistic({ rest_state: 'inside' });

          // Симметрично handleRent: переводим себя из общего пространства
          // локации в комнату номера. Без этого при входе кнопкой «Войти в
          // комнату» фильтр «внутри номера» тебя не находит — свой ник
          // не видно в списке.
          const globalState = chatApi.endpoints.getOnlineCharacters.select({
            locationSlug: null, limit: 50, offset: 0,
          })(storeRef.current.getState());
          const userObject = globalState?.data?.objects?.find(u => u.id === character.id);
          if (userObject) {
            moveOnlineUser(dispatch, {
              characterId: character.id,
              oldLocationSlug: character.location_slug,
              newLocationSlug: 'inn:inside',
              userData: userObject,
            });
          }

          dispatch(commitCharacterFields({ rest_state: 'inside' }));
          dispatch(commitChatRoom('inn:inside'));
          dispatch(characterApi.util.invalidateTags(['Character']));
          refetch().finally(() => setOptimistic(null));
      } catch (e) {
          showError(getErrorMessage(e, 'Ошибка при входе'));
      } finally {
          setTransitioning(false);
      }
  };


  if (!character) return null;

  // Состояние 2: Внутри номера
  if (restState === 'inside' && !expiredLocal) {
    return (
      <div className={styles.wrapper}>
        <ErrorToast message={currentError} />
        <div className={styles.contentBox}>
          <div className={styles.tables}>
            <div className={styles.innTitle}>Гостиница "Уставшая Душа"</div>

            <div className={styles.borderBox}>
              <table className={styles.roomTable}>
                <colgroup>
                  <col style={{ width: '100%' }} />
                </colgroup>
                <thead>
                  <tr>
                    <th>Комната №{roomNumber}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className={styles.roomInfo}>
                      <div className={styles.rentalTime}>
                        Аренда комнаты еще {timeLeft}
                      </div>
                      <button
                        className={btn.textLinkDanger}
                        onClick={handleExit}
                        disabled={transitioning}
                      >
                        Выйти из комнаты
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Состояние 1: На входе
  return (
    <div className={styles.wrapper}>
      <ErrorToast message={currentError} />
      <div className={styles.contentBox}>
        <div className={styles.tables}>
          <div className={styles.innTitle}>Гостиница "Уставшая Душа"</div>

          <div className={styles.availability}>
            Свободно номеров: {availableRooms} / {maxRooms}
          </div>

          <div className={styles.borderBox}>
            <table className={styles.pricesTable}>
              <colgroup>
                <col style={{ width: '20%' }} />
                <col style={{ width: '40%' }} />
                <col style={{ width: '40%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Дни</th>
                  <th>Цена</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(prices).map(([days, price]) => (
                  <tr key={days}>
                    <td>{days}</td>
                    <td className={styles.priceCell}>
                      <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                      {Number(price).toFixed(2)} дт.
                    </td>
                    <td className={styles.actionCell}>
                      <button
                        className={btn.textLinkDanger}
                        onClick={() => handleRent(Number(days))}
                        disabled={rentingDays === Number(days)}
                      >
                        Арендовать
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Кнопка "Войти в номер" если есть активная аренда И она не истекла */}
          {hasActiveRental && !expiredLocal && (
            <div className={styles.enterButton}>
              <button
                className={btn.gameButton}
                onClick={handleEnter}
                disabled={transitioning}
              >
                Войти в комнату
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default InnPage;