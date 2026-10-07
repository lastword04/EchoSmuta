import { MINING_ERRORS, MINING_LIMITS } from '../../../../../entities/character/config/mining';

/**
 * Обрабатывает ошибку создания/продолжения крафта
 * 
 * @param {Object} error - axios-ошибка ({response}) или RTK Query unwrap ({status, data})
 * @param {Object} handlers - функции для обработки различных сценариев
 * @returns {{ type: string, data?: any }} - тип ошибки и дополнительные данные
 */
export const handleCraftingError = (error, handlers) => {
  const { 
    showError, 
    fetchNewCaptcha, 
    loadStartedCrafting, 
    onRefresh, 
    setCaptchaInput, 
    setSelectedRecipe 
  } = handlers;
  
  // error приходит в двух формах: axios ({ response: { status, data } }) и RTK unwrap ({ status, data })
  const errStatus = error?.response?.status ?? error?.status;
  const err = error?.response?.data ?? error?.data;
  const errCode = (err?.error_code || '').toUpperCase();
  const errDetail = err?.detail || '';
  const errMsg = (error?.message || '').toLowerCase();

  // 409 — конфликт: активный крафт уже существует
  if (errStatus === 409) {
    return { type: 'CONFLICT', data: err };
  }

  // 410 — капча истекла
  if (errStatus === 410) {
    showError('Время действия капчи истекло. Попробуйте снова.');
    fetchNewCaptcha();
    setCaptchaInput?.('');
    setSelectedRecipe?.(null);
    return { type: 'CAPTCHA_EXPIRED' };
  }

  if (err?.error_code === 'ITEM_CRAFT_ALREADY_STARTED') {
    showError(err?.detail || 'Крафт этого товара уже начат — продолжите его во вкладке "Изготовление"');
    loadStartedCrafting?.();
    fetchNewCaptcha();
    return { type: 'ITEM_CRAFT_ALREADY_STARTED' };
  }

  if (err?.error_code === 'CAPTCHA_EXPIRED' || err?.error_code === 'INVALID_CAPTCHA_INPUT') {
    showError('Неправильный код');
    fetchNewCaptcha();
    setCaptchaInput?.('');
    return { type: 'INVALID_CAPTCHA' };
  }

  if (err?.error_code === MINING_ERRORS.INSUFFICIENT_CHARACTER_LEVEL) {
    showError(`Изготавливать предметы можно с ${err.extras?.required_level || MINING_LIMITS.MIN_LEVEL}-го уровня`);
    return { type: 'INSUFFICIENT_LEVEL' };
  }

  if (err?.error_code === MINING_ERRORS.INSUFFICIENT_CHARACTER_TIREDNESS) {
    showError('Вы слишком устали. Отдохните, чтобы продолжить работу');
    return { type: 'INSUFFICIENT_TIREDNESS' };
  }

  if (err?.error_code === 'LICENSE_EXPIRED' || err?.error_code === 'NO_CRAFTING_LICENSE' || err?.error_code === 'SHOP_LICENSE_EXPIRED') {
    showError('Срок действия вашей лицензии истёк. Приобретите новую.');
    setCaptchaInput?.('');
    setSelectedRecipe?.(null);
    fetchNewCaptcha();
    onRefresh?.();
    return { type: 'LICENSE_EXPIRED' };
  }

  if (err?.error_code === 'NOT_ENOUGH_DUCATS') {
    showError(`Недостаточно дукатов. Требуется: ${err.extras?.required_ducats || '?'} дт.`);
    return { type: 'NOT_ENOUGH_DUCATS' };
  }

  if (err?.error_code === 'ITEM_NOT_FOUND' || err?.error_code === 'RECIPE_NOT_FOUND') {
    showError('Рецепт не найден');
    fetchNewCaptcha();
    return { type: 'RECIPE_NOT_FOUND' };
  }

  if (err?.error_code === 'CRAFTING_LIMIT_REACHED') {
    showError('Достигнут лимит активных крафтов');
    fetchNewCaptcha();
    return { type: 'CRAFTING_LIMIT_REACHED' };
  }

  if (errCode === 'INSUFFICIENT_RESOURCES_FOR_CRAFTING' || 
      errCode.includes('INSUFFICIENT_RESOURCES')) {
    showError('Недостаточно ресурсов для создания этого товара');
    fetchNewCaptcha();
    setCaptchaInput?.('');
    return { type: 'INSUFFICIENT_RESOURCES' };
  }

  // fallback: ищем подсказку в любом поле ответа
  const allErrorText = `${errCode} ${errDetail} ${errMsg} ${JSON.stringify(err || '')}`.toLowerCase();
  
  if (allErrorText.includes('insufficient resources') || 
      allErrorText.includes('недостаточно ресурсов')) {
    showError('Недостаточно ресурсов для создания этого предмета');
    fetchNewCaptcha();
    setCaptchaInput?.('');
    return { type: 'INSUFFICIENT_RESOURCES' };
  }

  if (allErrorText.includes('license') && allErrorText.includes('expired')) {
    showError('Срок действия вашей лицензии истёк. Приобретите новую.');
    setCaptchaInput?.('');
    setSelectedRecipe?.(null);
    fetchNewCaptcha();
    onRefresh?.();
    return { type: 'LICENSE_EXPIRED' };
  }

  showError(errDetail || 'Ошибка при создании');
  fetchNewCaptcha();
  setCaptchaInput?.('');
  return { type: 'UNKNOWN_ERROR' };
};