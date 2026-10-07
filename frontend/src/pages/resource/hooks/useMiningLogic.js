import { useCallback, useEffect, useState, useRef } from "react";
import { useGetResourcesQuery, useMineResourceMutation, resourcesApi } from "../../../entities/resources/api/resourcesApi";
import { captchaApi, useGetCaptchaQuery } from "../../../entities/captcha/api/captchaApi";
import { useDispatch, useSelector } from 'react-redux';
import { setLastMining, clearLastMining } from '../../../entities/resources/store/miningSlice';
import { 
  parseMiningMessage,
  MINING_LIMITS,
  MINING_STATUS,
  MINING_ERRORS,
  MINING_TIMERS,
  MINING_REGEX,
} from '../../../entities/character/config/mining';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import { storeRef } from '../../../shared/store/storeRef';

const CAPTCHA_FETCH_ERROR = "Не удалось загрузить капчу";

export const useMiningLogic = ({ character, onRefresh }) => {
  // === RTK Query ===
  const { 
    data: resourcesData,     
  } = useGetResourcesQuery(character?.location_slug, {
    skip: !character?.location_slug
  });
  const [mineResource] = useMineResourceMutation();

  // === Redux ===
  const dispatch = useDispatch();
  const lastMiningId = useSelector((state) => state.session?.mining?.lastMiningId);
  const locationMining = useSelector((state) => state.session?.mining?.locationSlug);

  // === Стейты майнинга ===
  const [miningId, setMiningId] = useState(null);
  const [miningMessage, setMiningMessage] = useState("");
  const [endTime, setEndTime] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [miningResult, setMiningResult] = useState("");

  // === Стейт ввода капчи ===
  const [captchaInput, setCaptchaInput] = useState("");

  // === Капча: query вместо мутации (паритет с мастерской) ===
  const {
    data: captchaData,
    error: captchaQueryError,
    isFetching: isCaptchaFetching,
    refetch: refetchCaptcha,
  } = useGetCaptchaQuery(undefined, { skip: Boolean(miningId) });
  const captchaFailed = Boolean(captchaQueryError);
  const captchaPrefetchedRef = useRef(false);

  // === Стейты UI ===
  const [captchaError, setCaptchaError] = useState("");
  const [isMiningRequestInProgress, setIsMiningRequestInProgress] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // === Refs ===
  const onRefreshRef = useRef(onRefresh);
  const isMountedRef = useRef(true);
  const captchaInputRef = useRef(null);
  const initialCaptchaShownRef = useRef(false);
  const miningIdRef = useRef(miningId);
  const endTimeRef = useRef(endTime);

  // === Вычисляемые значения ===
  const minLevel = MINING_LIMITS.MIN_LEVEL;
  const maxTiredness = MINING_LIMITS.MAX_TIREDNESS;
  const isLevelAllowed = character && character.level >= minLevel;
  const isTiredAllowed = character && character.tiredness <= maxTiredness;
  const canMine = isLevelAllowed && isTiredAllowed;

  const levelTiredError = !isLevelAllowed
    ? `Добывать ресурсы можно с ${minLevel}-го уровня`
    : !isTiredAllowed
    ? "Вы слишком устали. Отдохните, чтобы продолжить работу"
    : "";

  const errorMessage = levelTiredError || captchaError || (captchaFailed ? CAPTCHA_FETCH_ERROR : "");

  // === Синхронизация refs ===
  useEffect(() => { miningIdRef.current = miningId; }, [miningId]);
  useEffect(() => { endTimeRef.current = endTime; }, [endTime]);
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  // === Загрузка капчи ===
  const fetchNewCaptcha = useCallback(async () => {
    try {
      await refetchCaptcha();
    } catch {
      // ошибка отражается через captchaFailed (ошибка query)
    }
  }, [refetchCaptcha]);

  // === Сброс и инициализация при смене локации ===    
  useEffect(() => {
    if (!character) return;

    setCaptchaInput("");    
    setMiningMessage("");
    setMiningResult("");
    setMiningId(null);
    setEndTime(null);
    setCountdown(0);
    setCaptchaError("");
    captchaPrefetchedRef.current = false;

    if (lastMiningId && locationMining && character.location_slug !== locationMining) {
      dispatch(clearLastMining());
    }

    async function init() {
      try {
        const miningStatus = await storeRef.current
          .dispatch(resourcesApi.endpoints.getMiningStatus.initiate(undefined, { forceRefetch: true }))
          .unwrap()
          .catch(() => ({ status: MINING_STATUS.IDLE }));

        if (!isMountedRef.current) return;

        if (miningStatus.status === MINING_STATUS.IN_PROGRESS &&
            miningStatus.id &&
            miningStatus.location_slug === character.location_slug) {
          setMiningId(miningStatus.id);
          const parsed = parseMiningMessage(miningStatus.message);
          setMiningMessage(parsed.text);
          const finishTime = parseUtcDate(miningStatus.finish_time).getTime();
          setEndTime(finishTime);
          setCountdown(Math.max(0, Math.ceil((finishTime - Date.now()) / 1000)));
        }
      } catch (error) {
        console.error("Ошибка инициализации страницы:", error);
      }
    }

    init();
    // dispatch стабилен; character/lastMiningId/locationMining сознательно не в deps —
    // их изменение не должно перезапускать сброс, иначе активный майнинг стирается посреди процесса
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [character?.location_slug, dispatch]);

  // === Таймер обратного отсчёта ===
  useEffect(() => {
    if (!endTime) return;

    const timer = setInterval(() => {
      const remaining = Math.max(0, Math.ceil((endTimeRef.current - Date.now()) / 1000));
      setCountdown(remaining);

      if (remaining <= MINING_TIMERS.CAPTCHA_PREFETCH_AT && !captchaPrefetchedRef.current) {
        captchaPrefetchedRef.current = true;
        dispatch(
          captchaApi.endpoints.getCaptcha.initiate(undefined, { forceRefetch: true, subscribe: false })
        ).catch(() => null);
      }

      if (remaining <= 0) {
        clearInterval(timer);
      }
    }, MINING_TIMERS.TIMER_TICK);

    return () => clearInterval(timer);
  }, [endTime, dispatch]);

  // === Слушатель завершения майнинга через WebSocket ===
  useEffect(() => {
    const handleEconomyUpdate = async (event) => {
      const detail = event.detail || {};     
      
      if (detail.action !== 'mining_finished' || !miningIdRef.current) {       
        return;
      }
      
      if (detail.initiator_character_id !== character?.id) {        
        return;
      }      

      try {
        const resultMessage = detail.message;               
        const refreshPromise = onRefreshRef.current ? onRefreshRef.current() : Promise.resolve();
        await refreshPromise;

        if (!isMountedRef.current) {          
          return;
        }
        
        setMiningResult(resultMessage);
        setMiningId(null);
        setEndTime(null);
        setCountdown(0);
        setMiningMessage("");
        setCaptchaError("");
        captchaPrefetchedRef.current = false;
        dispatch(clearLastMining());                
        dispatch(resourcesApi.util.invalidateTags([{ type: 'Resources', id: character?.location_slug }]));        
      } catch (e) {
        console.error("Ошибка при получении результата майнинга:", e);
        if (isMountedRef.current) {
          setCaptchaError("Ошибка при завершении добычи");
        }
      }
    };

    window.addEventListener('economy-updated', handleEconomyUpdate);
    return () => window.removeEventListener('economy-updated', handleEconomyUpdate);
  }, [character?.id, character?.location_slug, dispatch]);

  // === Обработчик кнопки "Добывать" ===
  async function handleMine() {
    if (isMiningRequestInProgress || !captchaData) return;

    try {
      setIsMiningRequestInProgress(true);

      const response = await mineResource({
        captcha_id: captchaData.captcha_id,
        user_input: captchaInput
      }).unwrap();

      setCaptchaError("");
      setMiningResult("");
      setCaptchaInput("");

      dispatch(captchaApi.util.invalidateTags(['Captcha']));
      captchaPrefetchedRef.current = false;

      setMiningId(response.id);
      dispatch(setLastMining({
        lastMiningId: response.id,
        locationSlug: character?.location_slug
      }));

      const parsed = parseMiningMessage(response.message);
      setMiningMessage(parsed.text);
      setCountdown(parsed.seconds);

      const finishTime = parseUtcDate(response.finish_time).getTime();
      setEndTime(finishTime);
    } catch (e) {
      const err = e?.data || e?.response?.data || e?.error;
      if (!err) return;

      if (err.error_code === MINING_ERRORS.CAPTCHA_EXPIRED || err.error_code === MINING_ERRORS.INVALID_CAPTCHA_INPUT) {
        if (!captchaError) setCaptchaError("Неправильный код");
        await fetchNewCaptcha();
        setCaptchaInput("");
        return;
      }

      if (err.error_code === MINING_ERRORS.INSUFFICIENT_CHARACTER_LEVEL) {
        setCaptchaError(`Добывать ресурсы можно с ${err.extras.required_level}-го уровня`);
        return;
      }

      if (err.error_code === MINING_ERRORS.INSUFFICIENT_CHARACTER_TIREDNESS) {
        setCaptchaError("Вы слишком устали. Отдохните, чтобы продолжить работу");
        return;
      }
    } finally {
      setIsMiningRequestInProgress(false);
    }
  }

  // === UI-эффекты ===
  useEffect(() => {
    if (!captchaData) return;
    if (!initialCaptchaShownRef.current) {
      initialCaptchaShownRef.current = true;
      return;
    }
    if (!miningId) {
      setTimeout(() => captchaInputRef.current?.focus(), MINING_TIMERS.FOCUS_DELAY);
    }
  }, [captchaData, miningId]);

  useEffect(() => {
    if (captchaData) setCaptchaInput("");
  }, [captchaData]);

  // === Обработчик ввода капчи ===
  const handleInputChange = (e) => {
    const value = e.target.value;
    if (MINING_REGEX.CAPTCHA_INPUT.test(value)) {
      setCaptchaInput(value);
    }
  };

  // === onRefresh sync ===
  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  return {
    // Данные
    resourcesData,
    
    // Состояние майнинга
    miningId,
    miningMessage,
    endTime,
    countdown,
    miningResult,
    
    // Состояние капчи
    captchaData,
    captchaInput,
    isCaptchaFetching,
    
    // UI
    isCollapsed,
    setIsCollapsed,
    canMine,
    errorMessage,
    isMiningRequestInProgress,
    
    // Refs
    captchaInputRef,
    
    // Handlers
    handleInputChange,
    handleMine,
    fetchNewCaptcha,
  };
};