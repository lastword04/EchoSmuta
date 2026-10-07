import { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { CharacterStatsWebSocket } from '../../../shared/lib/websocket/CharacterStatsWebSocket';
import { useGetOnlyMeQuery} from '../api/characterApi';
import { useGetCharacterBuffsQuery } from '../api/characterStatsApi';
import { applySnapshot, applyVolatile, clearVolatile, selectCharacter } from '../store/characterSlice';


/**
 * Синхронизирует внешние источники в characterSlice (единственный источник правды):
 *  - RTK-снапшот → applySnapshot (merge внутри редьюсера, без моргания статов);
 *  - WebSocket-тики → applyVolatile;
 *  - location_slug здесь НЕ пишется: им владеет коммит перехода (useLocationTransition).
 * Возвращает { character } — чтение из стора.
 */
export const useCharacter = () => {
  const activeCharacterId = useSelector(state => state.local.activeCharacterId); 
  const dispatch = useDispatch();
  const characterFromStore = useSelector(selectCharacter);

  const { data: freshCharacter, refetch: refetchCharacter } = useGetOnlyMeQuery(undefined, {
    skip: !activeCharacterId,
    refetchOnMountOrArgChange: 5,
    refetchOnFocus: true,
  });

  const { data: freshBuffs, isFetching: buffsIsFetching, refetch: refetchBuffs } = useGetCharacterBuffsQuery(freshCharacter?.id, {
    skip: !freshCharacter?.id || !activeCharacterId,
    refetchOnMountOrArgChange: 5,
    refetchOnFocus: true,
  });

  // Ref для refetch-функций: WS-эффект не должен пересоздаваться из-за их смены
  const refetchRef = useRef({});
  refetchRef.current = { refetchCharacter, refetchBuffs };

  // Синхронизация RTK Query → slice
  useEffect(() => {
    if (!freshCharacter) return;
    
    // Защита от чужого/устаревшего in-flight ответа при смене персонажа
    if (activeCharacterId && freshCharacter.id !== activeCharacterId) return;
    dispatch(applySnapshot({ character: freshCharacter, buffs: freshBuffs, buffsIsFetching }));
      
  }, [freshCharacter, freshBuffs, buffsIsFetching, activeCharacterId, dispatch]);

  // WebSocket статов
  useEffect(() => {
    if (!characterFromStore?.id) return;
    const handleStatsUpdate = (statsData) => {
      // WS-тик → slice (volatile-поля)
      dispatch(applyVolatile(statsData));      
    };

    // Self-healing при reconnect: очищаем volatile, REST-рефетч обновит snapshot
    const handleReconnect = () => {
      dispatch(clearVolatile());
      refetchRef.current.refetchCharacter();
      refetchRef.current.refetchBuffs();
    };

    const statsSocket = new CharacterStatsWebSocket(
      characterFromStore.id, 
      handleStatsUpdate, 
      (error) => console.error('[CharacterStatsWS] Error:', error), 
      () => {},
      handleReconnect  
    );
    statsSocket.connect();
    return () => statsSocket.disconnect();
  }, [characterFromStore?.id, dispatch]);

  // Мгновенная реакция на истечение баффов.
  // Раз в секунду смотрим: есть ли в списке бафф, чей expires_at уже прошёл.
  // Если да — один раз refetch'им статы и баффы, не дожидаясь Celery-тика.
  const expiryRefetchInProgress = useRef(false);
  useEffect(() => {
    if (!characterFromStore?.id) return;
    const timer = setInterval(() => {
      const now = Date.now();
      const hasExpired = (characterFromStore.buffs || []).some(b => {
        if (!b.is_active || !b.expires_at) return false;
        // expires_at приходит без таймзоны, но это UTC — добавляем Z,
        // иначе Date.parse посчитает его локальным временем
        const iso = b.expires_at.endsWith('Z') ? b.expires_at : b.expires_at + 'Z';
        return Date.parse(iso) <= now;
      });
      if (!hasExpired || expiryRefetchInProgress.current) return;

      expiryRefetchInProgress.current = true;
      Promise.all([refetchCharacter(), refetchBuffs()]).finally(() => {
        expiryRefetchInProgress.current = false;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [characterFromStore?.id, characterFromStore?.buffs, refetchCharacter, refetchBuffs]);

  return { character: characterFromStore };
};