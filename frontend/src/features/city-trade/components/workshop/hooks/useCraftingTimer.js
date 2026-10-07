import { useState, useEffect, useLayoutEffect, useRef, useCallback } from 'react';
import { MINING_TIMERS } from '../../../../../entities/character/config/mining';

/**
 * Хук таймера активного крафта: обратный отсчёт до endTime.
 * Префетч капчи — домен данных, живёт в useWorkshopLogic (смотрит на countdown).
 *
 * @param {number|null} endTime - timestamp окончания крафта
 * @param {Function} onTimerEnd - callback при окончании таймера
 * @returns {Object} - countdown и функции управления
 */
export const useCraftingTimer = (endTime, onTimerEnd) => {
  const [countdown, setCountdown] = useState(0);

  const countdownRef = useRef(0);
  const onTimerEndRef = useRef(onTimerEnd);

  useEffect(() => {
    onTimerEndRef.current = onTimerEnd;
  }, [onTimerEnd]);

  // useLayoutEffect + немедленный первый тик: без него до первого интервального
  // тика в UI мелькает "Осталось 0:00"
  useLayoutEffect(() => {
    if (!endTime) return;

    let timer;
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((endTime - Date.now()) / 1000));

      if (remaining !== countdownRef.current) {
        countdownRef.current = remaining;
        setCountdown(remaining);
      }

      if (remaining <= 0) {
        clearInterval(timer);
        onTimerEndRef.current?.();
      }
    };

    tick();
    timer = setInterval(tick, MINING_TIMERS.TIMER_TICK);

    return () => clearInterval(timer);
    // onTimerEnd не в deps: читается через ref, иначе смена identity пересоздаёт interval
  }, [endTime]);

  const resetTimer = useCallback(() => {
    setCountdown(0);
    countdownRef.current = 0;
  }, []);

  return {
    countdown,
    countdownRef,
    resetTimer
  };
};