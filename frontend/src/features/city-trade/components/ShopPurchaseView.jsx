// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import styles from "./ShopPurchaseView.module.css";
import { getLocationTexts } from '../config/locationTextConfig';
import btn from '../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function ShopPurchaseView({ purchaseInfo, onPurchase, isPurchasing, locationSlug }) {
  const texts = getLocationTexts(locationSlug);
  
  // Guard: если данные не готовы — не рендерим
  if (!purchaseInfo?.description) return null;

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.purchaseContainer}>
      <div className={styles.borderBox}>
        <div className={styles.content}>
          <div className={styles.description}>
            {purchaseInfo.description.split('\n\n').map((paragraph, index) => (
              <p key={index} className={styles.paragraph}>{paragraph}</p>
            ))}
          </div>
          <button 
            className={`${btn.gameButton} ${btn.sizeLarge} ${styles.purchaseButton}`} 
            onClick={onPurchase} 
            disabled={isPurchasing}
          >
            {texts.purchaseButton} {purchaseInfo.accusative}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ShopPurchaseView;