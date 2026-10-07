import { useCallback, useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import {
  inventoryApi,
  useCancelExpiredCraftingMutation,
  useContinueCraftingMutation,
  useGetCityShopQuery,
  useGetCityShopStatsQuery,
  useGetCraftingLicenseStatusQuery,
  useGetCraftingStatusQuery,
  useGetStartedCraftingQuery,
  useGetStockRecipesQuery,
  useLazyGetCraftingActionQuery,
  useStartNewCraftingMutation,
} from '../../../../../entities/items/api/inventoryApi';
import { captchaApi, useGetCaptchaQuery } from '../../../../../entities/captcha/api/captchaApi';
import { MINING_LIMITS, MINING_REGEX, MINING_TIMERS, parseMiningMessage } from '../../../../../entities/character/config/mining';
import { clearLastCrafting, resetCraftingFlag, setLastCrafting } from '../../../store/craftingSlice';
import { getTradeLocationConfig } from '../../../../../shared/config/locations/tradeConfig';
import { getLocationTexts } from '../../../config/locationTextConfig';
import { useCraftingTimer } from './useCraftingTimer';
import { handleCraftingError } from '../utils/craftingErrors';
import { parseUtcDate } from '../../../../../shared/lib/utils/utcDate';

export const useWorkshopLogic = ({ locationSlug, onRefresh, character }) => {
  // ── Redux ──
  const dispatch = useDispatch();
  const activeCharacterId = useSelector((state) => state.local.activeCharacterId);
  const shouldReset = useSelector((state) => state.session?.crafting?.shouldReset);
  

  // ── Конфигурация ──
  const locationConfig = getTradeLocationConfig(locationSlug);
  const texts = getLocationTexts(locationSlug);
  const isProduction = Boolean(locationConfig?.isProduction);

  // ── State ──
  const [activeTab, setActiveTab] = useState('crafting');
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [selectedStartCreatingId, setSelectedStartCreatingId] = useState(null);
  
  const [captchaInput, setCaptchaInput] = useState('');  
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [craftingResult, setCraftingResult] = useState('');
  const [craftingId, setCraftingId] = useState(null);
  const [craftingMessage, setCraftingMessage] = useState('');
  const [endTime, setEndTime] = useState(null);
  const [isCheckingResult, setIsCheckingResult] = useState(false);
  const [isInitialized, setIsInitialized] = useState(true);
  const [isRefreshingTab, setIsRefreshingTab] = useState(false);

  // ── Refs ──
  const initializationRef = useRef(false);
  const checkingResultRef = useRef(false);
  const finishCheckingResultRef = useRef(null);
  const onRefreshRef = useRef(onRefresh);

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  const lastStartedCraftingRef = useRef(undefined);
  const lastRecipesRef = useRef(undefined);
  const lastStatsRef = useRef(null);

  // ═══ RTK Query ═══
  

  const {
    currentData: startedCrafting,
    isLoading: isStartedCraftingLoading,
    refetch: refetchStartedCrafting,
  } = useGetStartedCraftingQuery(locationSlug, {
    skip: !locationSlug,
    refetchOnFocus: true,
  });

  const {
    currentData: recipes, 
    isLoading: isRecipesLoading,    
    refetch: refetchRecipes,
  } = useGetStockRecipesQuery(locationSlug, { 
    skip: !locationSlug,
    refetchOnFocus: true,    
  });

  const { data: stats, isLoading: isStatsLoading } = useGetCityShopStatsQuery(locationSlug, { 
    skip: !locationSlug,
    refetchOnFocus: true,    
  });

  const { data: craftingStatus, isLoading: isCraftingStatusLoading, refetch: refetchCraftingStatus } =
    useGetCraftingStatusQuery(undefined, { 
      skip: !character,
      refetchOnFocus: true,      
    });

  const { data: productionLicense, isLoading: isProductionLicenseLoading } =
    useGetCraftingLicenseStatusQuery(
      { locationSlug, characterId: activeCharacterId },
      { 
        skip: !locationSlug || !activeCharacterId || !isProduction,
        refetchOnFocus: true,        
      }
    );

  const { data: cityShop, isLoading: isCityShopLoading } =
    useGetCityShopQuery(
      { locationSlug, characterId: activeCharacterId },
      { 
        skip: !locationSlug || !activeCharacterId || isProduction,
        refetchOnFocus: true,        
      }
    );

        // ═══ lastDataRef обновление ═══
    // Рефы нужны только для stats (или других специфичных случаев), 
    // но НЕ для startedCrafting и recipes.
    if (stats !== undefined) {
      lastStatsRef.current = stats;
    }

    // ═══ Формирование данных для рендера ═══
    // Просто передаем currentData. Если он undefined, Guard в таблице перехватит это и вернет null.
    // Никаких подмен на старые значения из рефов!
    const displayStartedCrafting = startedCrafting; 
    const displayRecipes = recipes;                 
    const displayStats = stats ?? lastStatsRef.current;


  // Капча как query: гейт прогревает до монтирования, подписка читает кэш.
  // skip на время крафта/проверки результата: капча одноразовая, между
  // крафтами её «не существует» — как в старой логике (TTL-безопасно).
  const {
    data: captchaData,
    error: captchaError,
    isFetching: isCaptchaFetching,
    refetch: refetchCaptcha,
  } = useGetCaptchaQuery(undefined, { skip: Boolean(craftingId) || isCheckingResult });
  const captchaFailed = Boolean(captchaError);
  const [startNewCrafting, startRequest] = useStartNewCraftingMutation();
  const [continueCrafting, continueRequest] = useContinueCraftingMutation();
  const [cancelExpiredCrafting] = useCancelExpiredCraftingMutation();
  const [getCraftingAction] = useLazyGetCraftingActionQuery();

  // ═══ Производные значения ═══
  const minLevel = MINING_LIMITS.MIN_LEVEL;
  const maxTiredness = MINING_LIMITS.MAX_TIREDNESS;
  const isLevelAllowed = Boolean(character && character.level >= minLevel);
  const isTiredAllowed = Boolean(character && character.tiredness < maxTiredness);
  const canCraft = isLevelAllowed && isTiredAllowed;
  const isSubmitting = startRequest.isLoading || continueRequest.isLoading;
  const isLicenseLoading = isProduction ? isProductionLicenseLoading : isCityShopLoading;
  const isLicenseValid = isProduction
    ? productionLicense?.is_active === true
    : Boolean(cityShop?.shop?.end_license && parseUtcDate(cityShop.shop.end_license) >= Date.now());
  const isReadyForCaptcha = Boolean(character && canCraft && isLicenseValid && !craftingId && !isCheckingResult);

  const isLoadingTabData = activeTab === 'crafting' ? isStartedCraftingLoading : isRecipesLoading;
  const canShowForm = isInitialized && isReadyForCaptcha && Boolean(captchaData) && !isLicenseLoading;
  const isInitialDataLoading =
    isStartedCraftingLoading || isRecipesLoading || isStatsLoading || isCraftingStatusLoading || isLicenseLoading ||
    (isReadyForCaptcha && !captchaData && !captchaFailed);

  // ═══ Колбэки ═══
  const showError = useCallback((message) => {
    setErrorMessage(message);
    setSuccessMessage('');
    setCraftingResult('');
  }, []);

  const clearMessages = useCallback(() => {
    setErrorMessage('');
    setSuccessMessage('');
    setCraftingResult('');
  }, []);

  // Обновить капчу вручную (кнопка / невалидный ввод): сервер отдаёт новую
  const fetchNewCaptcha = useCallback(async () => {
    try {
      await refetchCaptcha();
    } catch {
      showError('Не удалось загрузить капчу');
    }
  }, [refetchCaptcha, showError]);


  const wsTimeoutRef = useRef(null);

  const { countdown, resetTimer } = useCraftingTimer(
    endTime,
    () => {
      // Не вызываем finishCheckingResult сразу, а ждём WS-событие 3 секунды
      if (wsTimeoutRef.current) clearTimeout(wsTimeoutRef.current);
      wsTimeoutRef.current = setTimeout(() => {
        // Если WS не пришёл за 3 секунды — делаем fallback через HTTP
        if (finishCheckingResultRef.current) {
          finishCheckingResultRef.current();
        }
      }, 3000);
    },
  );

  // Префетч новой капчи незадолго до конца крафта: к моменту результата она
  // уже в кэше → форма появляется мгновенно. forceRefetch — сервер отдаёт новую.
  const captchaPrefetchedRef = useRef(false);
  useEffect(() => {
    if (!craftingId || countdown <= 0 || countdown > MINING_TIMERS.CAPTCHA_PREFETCH_AT) return;
    if (captchaPrefetchedRef.current) return;
    captchaPrefetchedRef.current = true;
    dispatch(
      captchaApi.endpoints.getCaptcha.initiate(undefined, { forceRefetch: true, subscribe: false })
    ).catch(() => null);
  }, [craftingId, countdown, dispatch]);


  const applyActiveCrafting = useCallback((crafting) => {
    const finishTime = parseUtcDate(crafting.finish_time).getTime();
    const remainingSeconds = Math.max(0, Math.ceil((finishTime - Date.now()) / 1000));
    if (!crafting?.id || remainingSeconds <= 0) return false;

    const parsed = parseMiningMessage(crafting.message);
    setCraftingId(crafting.id);
    setCraftingMessage(parsed.text);
    setEndTime(finishTime);   
    setCaptchaInput('');
    dispatch(setLastCrafting({
      lastCraftingId: crafting.id,
      locationSlug,
      workshopLocationSlug: character?.location_slug,
    }));
    captchaPrefetchedRef.current = false;
    return true;
  }, [character?.location_slug, dispatch, locationSlug]);


  const finishCheckingResult = useCallback(async (wsResult = null) => {
    if (!craftingId || checkingResultRef.current) return;

    checkingResultRef.current = true;
    setIsCheckingResult(true);

    // ═══ БЫСТРЫЙ ПУТЬ: результат пришёл из WS — обновляем UI мгновенно ═══
    if (wsResult) {
      const isFailedResult =
        wsResult.result_status === 'failure' ||
        wsResult.status === 'failed' ||
        wsResult.status === 'error' ||
        wsResult.status === 'cancelled';

      // Одним батчем: гасим таймер и показываем результат
      setCraftingId(null);
      setEndTime(null);
      setCraftingMessage('');
      setCaptchaInput('');
      setIsCheckingResult(false);
      dispatch(clearLastCrafting());

      if (isFailedResult) {
        showError(wsResult.message || 'Ошибка при изготовлении');
      } else {
        setCraftingResult(wsResult.message || 'Изготовление завершено');
        setErrorMessage('');
        setSuccessMessage('');
      }

      

      // Данные обновляем В ФОНЕ, UI уже показывает результат
      dispatch(
        inventoryApi.util.invalidateTags([{ type: 'WorkshopStats', id: locationSlug || 'ALL' }])
      );
      Promise.all([
        refetchStartedCrafting(),
        refetchRecipes(),
        refetchCraftingStatus(),
        onRefreshRef.current?.(),
      ]).catch(() => {});

      checkingResultRef.current = false;
      return;
    }

    // ═══ СТАРЫЙ ПУТЬ (fallback через HTTP) — БЕЗ ИЗМЕНЕНИЙ ═══
    let finalResult = null;
    let finalError = null;

    try {
      const result = await getCraftingAction(craftingId).unwrap();

      if (result.status === 'in_progress') {
        if (applyActiveCrafting(result)) {
          checkingResultRef.current = false;
          setIsCheckingResult(false);
          return;
        }
        window.setTimeout(() => {
          checkingResultRef.current = false;
          finishCheckingResultRef.current?.();
        }, 1000);
        return;
      }
      finalResult = result;
    } catch (error) {
      console.error('[WorkshopView] Ошибка проверки результата:', error);
      finalError = error;
    }

    dispatch(
      inventoryApi.util.invalidateTags([{ type: 'WorkshopStats', id: locationSlug || 'ALL' }])
    );

    await Promise.all([
      refetchStartedCrafting(),
      refetchRecipes(),
      refetchCraftingStatus(),
      onRefreshRef.current?.(),
    ]);

    dispatch(clearLastCrafting());
    setCraftingId(null);
    setEndTime(null);
    setCraftingMessage('');
    setCaptchaInput('');
    setIsCheckingResult(false);

    if (finalError) {
      showError('Не удалось проверить результат изготовления');
    } else if (finalResult) {
      const isFailedResult =
        finalResult.result_status === 'failure' ||
        finalResult.status === 'failed' ||
        finalResult.status === 'error' ||
        finalResult.status === 'cancelled';

      if (isFailedResult) {
        showError(finalResult.message || 'Ошибка при изготовлении');
      } else {
        setCraftingResult(finalResult.message || 'Изготовление завершено');
        setErrorMessage('');
        setSuccessMessage('');
      }
    }

    checkingResultRef.current = false;
  }, [applyActiveCrafting, craftingId, dispatch, getCraftingAction, locationSlug, refetchCraftingStatus, refetchRecipes, refetchStartedCrafting, showError]);

  const handleTabClick = useCallback((tab) => {
    if (tab === activeTab) {    
      if (isRefreshingTab) return;    
      setIsRefreshingTab(true);    
      if (tab === 'crafting') refetchStartedCrafting();
      else refetchRecipes();    
      // Сбрасываем через 300мс
      setTimeout(() => {
        setIsRefreshingTab(false);
      }, 300);    
      return;
    }
    setActiveTab(tab);
  }, [activeTab, isRefreshingTab, refetchStartedCrafting, refetchRecipes]);

  const handleCaptchaRefresh = useCallback(async () => {
    if (isCaptchaFetching) return;
    setCaptchaInput('');
    await fetchNewCaptcha();
  }, [isCaptchaFetching, fetchNewCaptcha]);

  const handleCreate = useCallback(async (event) => {
    event.preventDefault();
    if (isSubmitting || isCheckingResult || craftingId) return;
    if (isCaptchaFetching) return showError('Подождите, обновляем капчу...');
    if (!captchaData || !captchaInput) {
      return showError(!captchaData ? 'Капча не загружена. Попробуйте обновить.' : 'Введите код с картинки');
    }

    const isStartingNew = activeTab === 'recipes' && selectedRecipe;
    const isContinuing = activeTab === 'crafting' && selectedStartCreatingId;

    if (!isStartingNew && !isContinuing) {
      return showError('Выберите рецепт для продолжения');
    }    

    try {
      const args = {
        recipeId: isStartingNew ? selectedRecipe : selectedStartCreatingId,
        captchaId: captchaData.captcha_id,
        userInput: captchaInput,
        locationSlug,
      };

      const response = isStartingNew
        ? await startNewCrafting(args).unwrap()
        : await continueCrafting(args).unwrap();

      clearMessages();
      setCaptchaInput('');
      // Капча израсходована: помечаем невалидной. Хук в skip (крафт идёт),
      // refetch не стартует — но при возврате в мастерскую гейт увидит
      // invalidated и закачает свежую, а не подсунет сожжённую.
      dispatch(captchaApi.util.invalidateTags(['Captcha']));

      applyActiveCrafting(response);

      // Обновляем список начатых крафтов
      const refetchResult = await refetchStartedCrafting();
      const freshStartedCrafting = refetchResult.data || [];            

      if (isStartingNew) {
        // Находим рецепт по selectedRecipe, достаем item_slug
        const recipe = recipes.find(r => r.id === selectedRecipe);
        const itemSlug = recipe?.item_details?.item?.slug;

        if (itemSlug) {
          // Ищем свежесозданную запись по item_slug (craft_stage=0)
          const newCrafting = freshStartedCrafting.find(
            r => r.item_details?.item?.slug === itemSlug && r.craft_stage === 0
          );
          if (newCrafting) {
            setSelectedStartCreatingId(newCrafting.id);
          }
        }
        setActiveTab('crafting');
      }

      setSuccessMessage('Изготовление начато!');
    } catch (error) {
      const errorResult = handleCraftingError(error, {
        showError,
        fetchNewCaptcha,
        loadStartedCrafting: refetchStartedCrafting,
        onRefresh: onRefreshRef.current,
        setCaptchaInput,
        setSelectedRecipe,
      });

      if (errorResult.type === 'CONFLICT') {
        try {
          const status = await refetchCraftingStatus().unwrap();
          if (status.status === 'in_progress' && applyActiveCrafting(status)) {
            showError('У вас уже есть активное изготовление');
          } else if (status.status === 'in_progress') {
            await cancelExpiredCrafting().unwrap();
            showError('Зависший крафт сброшен. Попробуйте снова.');
            await fetchNewCaptcha();
          } else {
            await fetchNewCaptcha();
          }
        } catch {
          showError('Ошибка проверки статуса изготовления');
          await fetchNewCaptcha();
        }
      }
    }
  }, [
    isSubmitting, isCheckingResult, craftingId, isCaptchaFetching,
    captchaData, captchaInput, activeTab, selectedStartCreatingId, selectedRecipe,
    locationSlug, showError, startNewCrafting, continueCrafting, clearMessages,
    applyActiveCrafting, refetchStartedCrafting, refetchCraftingStatus,
    cancelExpiredCrafting, fetchNewCaptcha, dispatch, recipes
  ]);

 
  // ═══ Effects ═══

  // === WebSocket-слушатель для крафта ===
  useEffect(() => {
    const handleEconomyUpdate = (event) => {   
      
      const detail = event.detail || {};
      
      // 1. Фильтр по типу события
      if (detail.action !== 'crafting_stage_completed') {      
        return;
      }   
      
      // 2. Фильтр по инициатору (событие приходит всем в локации)
      if (detail.initiator_character_id !== character?.id) {      
        return;
      }  
      
      // 3. Проверка что есть активный крафт
      if (!craftingId) {      
        return;
      }   

      // 4. Отменяем fallback-таймаут (WS пришёл вовремя)
      if (wsTimeoutRef.current) {
        clearTimeout(wsTimeoutRef.current);
        wsTimeoutRef.current = null;
      }

      // 5. Передаём результат в finishCheckingResult БЕЗ HTTP-запроса    
      if (finishCheckingResultRef.current) {
        finishCheckingResultRef.current({
          message: detail.message,
          result_status: detail.result_status,
        });
      }
    };

    window.addEventListener('economy-updated', handleEconomyUpdate);
    return () => window.removeEventListener('economy-updated', handleEconomyUpdate);
  }, [character?.id, craftingId]);

  useEffect(() => {
    finishCheckingResultRef.current = finishCheckingResult;
  }, [finishCheckingResult]);

  useEffect(() => {
    onRefreshRef.current = onRefresh;
  }, [onRefresh]);

  useEffect(() => {
    initializationRef.current = false;
    checkingResultRef.current = false;
    setIsInitialized(false);
    setCraftingId(null);
    setCraftingMessage('');
    setEndTime(null);    
    setCaptchaInput('');
    setErrorMessage('');
    setSuccessMessage('');
    setCraftingResult('');
    setSelectedRecipe(null);
    setSelectedStartCreatingId(null);
    resetTimer();
  }, [locationSlug, resetTimer]);

  useEffect(() => {
    if (!character || isCraftingStatusLoading || initializationRef.current) return;
    initializationRef.current = true;
    if (shouldReset) dispatch(resetCraftingFlag());
    const belongsToWorkshop = !craftingStatus?.location_slug || craftingStatus.location_slug === character.location_slug;
    if (craftingStatus?.status === 'in_progress' && belongsToWorkshop) {
      // Активный крафт: перезапускаем таймер и показываем «крафт идёт».
      applyActiveCrafting(craftingStatus);
    } else {
      dispatch(clearLastCrafting());
    }
    // ОБЯЗАТЕЛЬНО: effect сброса выше на МОНТИРОВАНИИ гасит isInitialized
    // (effects всегда гоняются при маунте, не только при смене deps).
    // Здесь, после решения о крафте, возвращаем флаг в true.
    setIsInitialized(true);
  }, [applyActiveCrafting, character, craftingStatus, dispatch, isCraftingStatusLoading, shouldReset]);

  

  useEffect(() => {
    if (captchaData) setCaptchaInput('');
  }, [captchaData]);

  // ═══ Возврат всего необходимого для рендера ═══
  return {
    // State
    activeTab, setActiveTab,
    selectedRecipe, setSelectedRecipe,
    selectedStartCreatingId, setSelectedStartCreatingId,
    captchaData,
    captchaFailed,
    isCaptchaLoading: isCaptchaFetching,
    captchaInput, setCaptchaInput,
    errorMessage, setErrorMessage,
    successMessage, setSuccessMessage,
    craftingResult, setCraftingResult,
    craftingId,
    craftingMessage,
    endTime,
    isCheckingResult,
    isInitialized,
    isRefreshingTab,
    
    // Derived
    texts,
    locationConfig,
    isProduction,
    minLevel,
    maxTiredness,
    isLevelAllowed,
    isTiredAllowed,
    canCraft,
    isSubmitting,
    isLicenseLoading,
    isLicenseValid,
    isReadyForCaptcha,
    isLoadingTabData,
    canShowForm,
    isInitialDataLoading,
    countdown,

    // Data
    startedCrafting: displayStartedCrafting,  
    recipes: displayRecipes,                  
    stats: displayStats,                     
    isStatsLoading,

    // Handlers
    handleTabClick,
    handleCaptchaRefresh,
    handleCreate,
  };
};