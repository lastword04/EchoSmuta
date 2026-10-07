// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useEffect, useState, useCallback } from "react";

import { useLocationPageController } from '../../shared/hooks/location/useLocationPageController';
import { useShopStatus } from '../../entities/items/hooks/useShopStatus';
import { useErrorToast } from "../../shared/hooks/ui/useErrorToast";
import ErrorToast from "../../shared/ui/ErrorToast/ErrorToast";
import { ErrorBoundary } from '../../shared/ui/ErrorBoundary/ErrorBoundary';
import MyShopView from "../city-trade/components/MyShopView";
import DealsView from "./components/DealsView";
import ShopsListView from "../city-trade/components/ShopsListView";
import ShopDetailView from "../city-trade/components/ShopDetailView";
import LicensesView from "./components/LicensesView";
import styles from "./TradeHallPage.module.css";

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                   ВСПОМОГАТЕЛЬНЫЙ КОМПОНЕНТ                        ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function NoShopNotice() {
  return (
    <div className={styles.noShop}>
      Сначала приобретите палатку во вкладке "Лицензии".
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        ОСНОВНОЙ КОМПОНЕНТ                          ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function TradeHallPage({ character, onRefresh }) {
  
  // ── Redux & hooks ──
  const { currentError } = useErrorToast();  
  const { activeTab } = useLocationPageController(character);

  // ── State ──  
  const [selectedShopId, setSelectedShopId] = useState(null);
  
  const { hasShop } = useShopStatus(character?.location_slug);

 
  // ── Callbacks ──
  


  const [initialShopData, setInitialShopData] = useState(null);
  
  const handleShopClick = useCallback((shopId, shopData = null) => {
    setSelectedShopId(shopId);
    setInitialShopData(shopData);
  }, []);

  const handleBack = useCallback(() => {
    setSelectedShopId(null);
  }, []);

   // ── Effects ──

  // Сброс выбранного магазина при смене вкладки или локации
  // (переключение вкладок и рефреш теперь обрабатывает useLocationPageController)
  useEffect(() => {
    setSelectedShopId(null);
  }, [activeTab, character?.location_slug]);
  



  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.wrapper}>
      <ErrorToast message={currentError} />
      <div className={styles.contentBox}>
        {/* Сделки: единственная вкладка, которая живёт скрытой (display:none).
            Причина: activeDealId в useState — при размонтировании терялся бы
            экран активной сделки. Этап 2 (перенос в Redux) — отдельно. */}
        <div style={{ display: activeTab === "deals" ? 'block' : 'none' }}>
          <ErrorBoundary>
            <DealsView 
              key={character?.location_slug} 
              character={character} 
              onRefresh={onRefresh}                          
            />
          </ErrorBoundary>
        </div>

        {activeTab === "licenses" && (
          <ErrorBoundary>
            <LicensesView 
              key={character?.location_slug} 
              character={character}                                           
            />
          </ErrorBoundary>
        )}

        {activeTab === "tents" && !selectedShopId && (
          <ErrorBoundary>
            <ShopsListView
              key={character?.location_slug}
              parentLocationSlug={character?.location_slug}
              onShopClick={handleShopClick}
              emptyMessage="Палаток не найдено"              
            />
          </ErrorBoundary>
        )}

        {activeTab === "tents" && selectedShopId && (
          <ErrorBoundary>
            <ShopDetailView
              key={selectedShopId}
              shopId={selectedShopId}
              locationSlug={character?.location_slug}
              character={character}
              onBack={handleBack}                          
              initialShopData={initialShopData}
            />
          </ErrorBoundary>
        )}

        {activeTab === "your-tent" && hasShop && (
          <ErrorBoundary>
            <MyShopView 
              key={character?.location_slug} 
              locationSlug={character?.location_slug} 
              character={character}                          
            />
          </ErrorBoundary>
        )}

        {activeTab === "your-tent" && hasShop === false && (
          <ErrorBoundary>
            <NoShopNotice />
          </ErrorBoundary>
        )}
      </div>
    </div>
  );
}

export default TradeHallPage;