// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import React, { useState, useRef, useCallback } from "react";
import { useSelector } from "react-redux";
import { useBuyCraftingLicenseMutation, useRenewCraftingLicenseMutation, useGetCraftingLicenseStatusQuery } from "../../../entities/items/api/inventoryApi";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import { formatLicenseTime } from '../utils/dateFormatter';
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import ShopPurchaseView from "./ShopPurchaseView";
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from "./LicenseView.module.css";
import btn from '../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function ProductionLicenseView({ locationSlug, config }) {
  
  // ── Redux & hooks ──
  const activeCharacterId = useSelector(state => state.local.activeCharacterId);
  const { currentError, showError } = useErrorToast();
  const [buyLicense] = useBuyCraftingLicenseMutation();
  const [renewLicense] = useRenewCraftingLicenseMutation();
  const lastDataRef = useRef(null);

  // ── State ──
 
  const [isBuying, setIsBuying] = useState(false);
  const [isRenewing, setIsRenewing] = useState(false);  

  // ── Callbacks ──

  // RTK Query — кэш общий с CityTradeLocation
  const { 
    data: licenseStatusData, 
    isError: isLicenseError,
    refetch: refetchLicense,
  } = useGetCraftingLicenseStatusQuery(
    { locationSlug, characterId: activeCharacterId },
    { 
      skip: !locationSlug || !activeCharacterId,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (licenseStatusData !== undefined && licenseStatusData !== null) {
    lastDataRef.current = licenseStatusData;
  }
  const displayData = licenseStatusData !== undefined ? licenseStatusData : lastDataRef.current;


  // Helper для единообразной обработки ошибок покупки/продления лицензии
  const handleLicenseError = useCallback((e, defaultMsg) => {
    const errorData = e?.data;
    if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_LEVEL_FOR_CITY_TRADE_SHOP') {
      return `Недостаточный уровень. Требуется ${errorData.extras?.required_level || '?'} уровень.`;
    }
    if (errorData?.error_code === 'INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP') {
      return `Недостаточно средств. Требуется ${errorData.extras?.required_ducats || '?'} дт.`;
    }
    if (errorData?.detail) return errorData.detail;
    return defaultMsg;
  }, []);

  const handleBuy = useCallback(async () => {
    if (isBuying) return;
    setIsBuying(true);
    try {
      await buyLicense(locationSlug).unwrap();
      await refetchLicense();      
    } catch (e) {
      showError(handleLicenseError(e, "Ошибка покупки лицензии"));
    } finally {
      setIsBuying(false);
    }
  }, [isBuying, locationSlug, buyLicense, refetchLicense, handleLicenseError, showError]);

  const handleRenew = useCallback(async () => {
    if (isRenewing) return;
    setIsRenewing(true);
    try {
      await renewLicense(locationSlug).unwrap();
      await refetchLicense();     
    } catch (e) {
      showError(handleLicenseError(e, "Ошибка продления лицензии"));
    } finally {
      setIsRenewing(false);
    }
  }, [isRenewing, locationSlug, renewLicense, refetchLicense, handleLicenseError, showError]);

  // ── Effects ──
  

  // ── Guards ──
  const license = isLicenseError ? null : (displayData ?? null);
  if (license === null) return null;

  if (!license?.is_active && config?.purchaseInfo) {
    return (
      <>
        <ErrorToast message={currentError} />
        <ShopPurchaseView
          purchaseInfo={{
            title: config.shopType,
            description: config.purchaseInfo.description,
            accusative: config.purchaseInfo.accusative
          }}
          onPurchase={handleBuy}
          isPurchasing={isBuying}
          locationSlug={locationSlug}
        />
      </>
    );
  }

  // ── Derived ──
  const licenseExpired = license?.end_date ? parseUtcDate(license.end_date) < Date.now() : true;
  const licenseTime = formatLicenseTime(license?.end_date);

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.licenseContainer}>
      <ErrorToast message={currentError} />
      <div className={styles.header}>
        <h2 className={styles.title}>{config.shopType} № {license.number}</h2>
      </div>
      <div className={styles.content}>
        <div className={styles.section}>
          <div className={styles.licenseStatus}>
            Лицензия: {licenseExpired 
              ? <span className={styles.expired}>Истек срок лицензии</span> 
              : <span className={styles.active}>Активна ({licenseTime})</span>}
          </div>
          <div className={styles.licenseCost}>Стоимость лицензии на 2 недели: 15 дт.</div>
          <button 
            className={`${btn.gameButton} ${btn.sizeLarge}`} 
            onClick={handleRenew} 
            disabled={isRenewing}
          >
            Продлить лицензию
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProductionLicenseView;