// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useEffect, useRef } from 'react';
import { MINING_TIMERS } from '../../../../../entities/character/config/mining';
import styles from '../../WorkshopView.module.css';
import btn from '../../../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

export const CraftingForm = ({
  captchaData,
  captchaInput,
  isCaptchaLoading,
  isSubmitting,
  activeTab,
  selectedStartCreatingId,
  selectedRecipe,
  onSubmit,
  onInputChange,
  onCaptchaRefresh
}) => {
  
  // ── Refs ──
  const captchaInputRef = useRef(null);
  const initialCaptchaShownRef = useRef(false);

  // ── Effects ──

  // Автофокус на поле капчи после смены изображения
  useEffect(() => {
    if (!captchaData) return;
    
    // Пропускаем первый показ капчи (когда компонент только смонтировался)
    if (!initialCaptchaShownRef.current) {
      initialCaptchaShownRef.current = true;
      return;
    }
    
    // Фокусируемся только если нет активного крафта
    if (!isSubmitting) {
      const timer = setTimeout(() => {
        captchaInputRef.current?.focus();
      }, MINING_TIMERS.FOCUS_DELAY);
      
      return () => clearTimeout(timer);
    }
  }, [captchaData, isSubmitting]);

  // ── Derived ──
  const isDisabled = 
    (activeTab === 'crafting' && !selectedStartCreatingId) ||
    (activeTab === 'recipes' && !selectedRecipe) ||
    isSubmitting ||
    isCaptchaLoading;

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <form onSubmit={onSubmit}>
      <div className={styles.captchaMiniRow}>
        <img
          src={captchaData.image_url}
          alt="Капча"
          className={styles.captchaMiniImage}
          onClick={onCaptchaRefresh}
          title="Нажмите для обновления капчи"
        />
        <input
          type="text"
          placeholder="Код"
          className={styles.captchaMiniInput}
          value={captchaInput}
          onChange={onInputChange}
          autoComplete="off"
          ref={captchaInputRef}
        />
      </div>
      <button
        type="submit"
        className={`${btn.gameButton} ${styles.submitButton}`}        
        disabled={isDisabled}
      >
        Создать
      </button>
    </form>
  );
};