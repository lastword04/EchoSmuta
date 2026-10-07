// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useEffect, useCallback, useRef } from "react";
import { useSelector } from "react-redux";
import { useRenewTradeLicenseMutation, useGetTradeLicenseStatusQuery } from "../../../entities/items/api/inventoryApi";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import { formatLicenseTime } from '../../city-trade/utils/dateFormatter';
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import styles from "../../city-trade/components/LicenseView.module.css";
import btn from '../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function TradeLicenseView({ onRefresh }) {
  
  // ── Redux & hooks ──
  const activeCharacterId = useSelector(state => state.local.activeCharacterId);
  const { currentError, showError } = useErrorToast();
  const [renewLicense] = useRenewTradeLicenseMutation();
  const lastDataRef = useRef(null);

  // ── RTK Query (прямое использование) ──
  const { 
    data: tradeLicenseData, 
    isError: isTradeLicenseError,    
  } = useGetTradeLicenseStatusQuery(
    { characterId: activeCharacterId },
    { 
      skip: !activeCharacterId,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (tradeLicenseData !== undefined && tradeLicenseData !== null) {
    lastDataRef.current = tradeLicenseData;
  }
  const displayData = tradeLicenseData !== undefined ? tradeLicenseData : lastDataRef.current;
  

  // ── State ──
  const [license, setLicense] = useState(null);
  const [isRenewing, setIsRenewing] = useState(false);

  // ── Синхронизация RTK Query → state ──
  useEffect(() => {
    if (isTradeLicenseError) {
      setLicense(null);
      return;
    }
    if (displayData !== undefined) {
      setLicense(displayData);
    }
  }, [displayData, isTradeLicenseError]);

  // ── Callbacks ──
  const handleRenew = useCallback(async () => {
    if (isRenewing) return;
    setIsRenewing(true);
    try {
      await renewLicense().unwrap();
      await onRefresh?.();
    } catch (e) {
      const errorData = e?.data;
      let errorMessage = "Ошибка продления лицензии";
      if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP') {
        errorMessage = `Недостаточно средств. Требуется: ${errorData.extras?.required_ducats || '?'} дт.`;
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setIsRenewing(false);
    }
  }, [isRenewing, renewLicense, onRefresh, showError]);

  // ── Effects ──
  

  // ── Guards ──
  if (!license) return null;

  // ── Derived ──
  const licenseExpired = !license.active;
  const licenseTime = formatLicenseTime(license.end_date);

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.licenseContainer}>
      <div className={styles.borderBox}>
        <ErrorToast message={currentError} />
        <div className={styles.header}>
          <h2 className={styles.title}>Лицензия торговца</h2>
        </div>
        <div className={styles.content}>
          <div className={styles.section}>
            <div className={styles.licenseStatus}>
              Лицензия: {licenseExpired 
                ? <span className={styles.expired}>Не активна</span> 
                : <span className={styles.active}>Активна ({licenseTime})</span>}
            </div>
            <div className={styles.licenseCost}>Стоимость лицензии на 2 недели: 15 дт.</div>
            <button 
              className={`${btn.gameButton} ${btn.sizeLarge}`} 
              onClick={handleRenew}
              disabled={isRenewing}
            >
              {licenseExpired ? "Купить лицензию" : "Продлить лицензию"}
            </button>
          </div>
          <div className={styles.licenseMain}>
            <img src='/images/trade-hall/tradelicense.png' alt="Лицензия" className={styles.licenseImage} />
            <div className={styles.licenseDescription}>
              <p><strong>Преимущества активной лицензии:</strong></p>
              <ul className={styles.licenseList}>
                <li>Налог на сделки: 3% вместо 10%</li>
                <li>Налог на бирже: 5% вместо 15%</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TradeLicenseView;