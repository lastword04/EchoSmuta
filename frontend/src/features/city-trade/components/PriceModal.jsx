// ========================= PriceModal =========================
import { useEffect, useRef } from "react";
import styles from "./MyShopView.module.css";
import btn from '../../../shared/styles/buttons.module.css';
import { getMinAllowedPrice } from '../../../shared/config/trade/priceConfig';
import { getLocationTexts } from "../config/locationTextConfig";
import { formatLicenseTime, formatWear } from '../utils/dateFormatter';
import { useEscapeKey } from '../../../shared/hooks/ui/useEscapeKey';
import { decimalInputHandler } from '../../../shared/lib/validation/numberInput';

function PriceModal({
  mode = "sale",
  title,
  item,
  amount = 1,
  onChangeAmount,
  price,
  onChangePrice,
  onConfirm,
  onCancel,
  confirmLabel,
  cancelLabel,
  priceLabel,
  locationSlug,
  isSubmitting = false,
}) {
  const texts = getLocationTexts(locationSlug);
  const basePrice = item?.item_price ?? item?.price ?? 0;
  const minPrice = getMinAllowedPrice(basePrice);
  const showAmount = mode === "sale" && item && item.amount > 1;
  const inputRef = useRef(null);

  // Возвращаем фокус после изменений
  // Возвращаем фокус в поле цены после завершения запроса
  useEffect(() => {
    if (!isSubmitting) {
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [isSubmitting]);
    

  useEscapeKey(onCancel, !isSubmitting);

  return (
    <div className={styles.modalOverlay} onClick={onCancel} role="dialog" aria-modal="true" aria-labelledby="price-modal-title">
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h3 id="price-modal-title" className={styles.modalTitle}>{title}</h3>
        </div>
        <div className={styles.modalBody}>
          {item && (
            <>
              <div className={styles.modalItemName}>
                {item.item_name} {mode === "sale" ? amount : 1} шт.
              </div>
              <div className={styles.modalItemInfo}>
                {texts.wearColumnLabel === 'Износ' 
                  ? `Износ: ${formatWear(item)}`
                  : `${texts.wearColumnLabel}: ${formatLicenseTime(item.expired_date)}`
                }
              </div>
            </>
          )}
          {showAmount && (
            <div className={styles.modalRow}>
              <span className={styles.modalRowLabel}>Количество:</span>
              <button type="button" className={styles.controlButton} onClick={() => onChangeAmount(Math.max(1, amount - 1))}>-</button>
              <input type="number" min="1" max={item.amount} value={amount}
                onChange={(e) => {
                  const v = parseInt(e.target.value, 10);
                  if (isNaN(v)) return onChangeAmount(1);
                  onChangeAmount(Math.min(Math.max(1, v), item.amount));
                }}
                className={styles.modalAmountInput}
              />
              <button type="button" className={styles.controlButton} onClick={() => onChangeAmount(Math.min(item.amount, amount + 1))}>+</button>
              <span className={styles.modalRowLabel}>шт.</span>
            </div>
          )}
          <div className={styles.modalRow}>
            <span className={styles.modalRowLabel}>{priceLabel}</span>
            <input 
              ref={inputRef}
              type="text" 
              inputMode="decimal"
              pattern="[0-9]*[.,]?[0-9]*"
              value={price} 
              onChange={decimalInputHandler(onChangePrice, 7, 2, { strip: true })}
              className={styles.modalAmountInput} 
              autoFocus 
            />
            <span className={styles.modalRowLabel}>дт.</span>
          </div>
        </div>

        {minPrice > 0 && (
            <div className={styles.modalItemInfo}>Мин. цена: {minPrice.toFixed(2)} дт.</div>
          )}
        <div className={styles.modalFooter}>
          <button 
            className={btn.gameButton} 
            onMouseDown={(e) => e.preventDefault()} 
            onClick={onConfirm}
            disabled={isSubmitting}
          >
            {confirmLabel}
          </button>
          <button
            className={btn.gameButton} 
            onMouseDown={(e) => e.preventDefault()} 
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default PriceModal;