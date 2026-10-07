// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useEffect, useCallback, useRef } from "react";
import { useSelector } from "react-redux";
import { useGetCityShopQuery } from "../../../entities/items/api/inventoryApi";
import LicenseView from "../../city-trade/components/LicenseView";
import TradeLicenseView from "./TradeLicenseView";
import SalesHistoryView from "../../city-trade/components/SalesHistoryView";
import styles from "./LicensesView.module.css";
import btn from '../../../shared/styles/buttons.module.css';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function LicensesView({ character }) {
  
  // ── Redux & hooks ──
  const activeCharacterId = useSelector(state => state.local.activeCharacterId);
  const lastDataRef = useRef(null);
  

  // ── RTK Query (кэш общий с TradeHallPage) ──
  const { 
    data: cityShopData, 
    isError: isCityShopError,
    refetch: refetchCityShop,
  } = useGetCityShopQuery(
    { locationSlug: character?.location_slug, characterId: character?.id },
    { 
      skip: !character?.location_slug || !activeCharacterId,
      refetchOnFocus: true,      
    }
  );

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (cityShopData !== undefined && cityShopData !== null) {
    lastDataRef.current = cityShopData;
  }
  const displayData = cityShopData !== undefined ? cityShopData : lastDataRef.current;

  // ── State ──
  const [shopData, setShopData] = useState(null);
  const [hasShop, setHasShop] = useState(null);  
  const [activeSubTab, setActiveSubTab] = useState("licenses");
  const [isRefreshingTab, setIsRefreshingTab] = useState(false);

  // ── Синхронизация RTK Query → локальный state ──
  useEffect(() => {
    if (isCityShopError) {
      setShopData(null);
      setHasShop(false);         
      return;
    }
    if (displayData !== undefined) { 
      setShopData(displayData);
      setHasShop(!!displayData);           
    }
  }, [displayData, isCityShopError]); 

  // ── Refresh через RTK Query ──
  const reloadAll = useCallback(async () => {
    await refetchCityShop();
  }, [refetchCityShop]);


  const handleTabChange = useCallback((tab) => {
    if (tab === activeSubTab) {
      // Защита от спама
      if (isRefreshingTab) return;      
      setIsRefreshingTab(true);
      reloadAll();      
      setTimeout(() => {
        setIsRefreshingTab(false);
      }, 300);
    } else {
      setActiveSubTab(tab);
    }
  }, [activeSubTab, isRefreshingTab, reloadAll]);

  // ── Effects ──

  // Умный сброс при РЕАЛЬНОЙ смене локации
  const prevLocationSlugRef = useRef(character?.location_slug); // ← ДОБАВИТЬ useRef

  useEffect(() => {
    if (prevLocationSlugRef.current !== character?.location_slug) {
      setShopData(null);
      setHasShop(null);
      prevLocationSlugRef.current = character?.location_slug;
    }
  }, [character?.location_slug]); 

  

  // ── Guards ──
  if (hasShop === null) return null;

  // ═══════════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ═══════════════════════════════════════════════════════════════════════

  return (
    <div className={styles.licensesContainer}>
      
      {/* Саб-нав показываем только владельцам палатки */}
      {hasShop && (
        <div className={styles.subNav}>
          <button
            className={`${btn.gameButton} ${activeSubTab === 'licenses' ? btn.gameButtonActive : ''}`}
            onClick={() => handleTabChange("licenses")} disabled={isRefreshingTab}
          >
            Лицензии
          </button>
          <span className={styles.dot}>•</span>
          <button
            className={`${btn.gameButton} ${activeSubTab === 'sales-history' ? btn.gameButtonActive : ''}`}
            onClick={() => handleTabChange("sales-history")} disabled={isRefreshingTab}
          >
            История продаж
          </button>
        </div>
      )}

      {/* Основная раскладка с лицензиями */}
      {(!hasShop || activeSubTab === "licenses") && (
        <div className={styles.licensesLayout}>
          <div className={styles.leftBlock}>
            <LicenseView
              initialShopData={shopData}
              initialHasShop={hasShop}
              locationSlug={character?.location_slug}
              shopType="Палатка"              
              onRefresh={reloadAll}             
            />
          </div>
          <div className={styles.rightBlock}>
            <TradeLicenseView            
              onRefresh={reloadAll}
            />
          </div>
        </div>
      )}

      {/* История продаж */}
      {hasShop && activeSubTab === "sales-history" && (
        <SalesHistoryView
          key={character?.location_slug}
          locationSlug={character?.location_slug}
        />
      )}
    </div>
  );
}

export default LicensesView;