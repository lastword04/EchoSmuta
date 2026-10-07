import { useState, useEffect, useCallback, useRef } from "react";
import { useSelector } from "react-redux";
import { useGetCityShopQuery } from "../../../entities/items/api/inventoryApi";
import LicenseView from "./LicenseView";

function LicenseViewContainer({ locationSlug, shopType, onRefresh }) {
  
  // ── Redux & hooks ──
  const activeCharacterId = useSelector(state => state.local.activeCharacterId);
  const lastDataRef = useRef(null);

  // ── RTK Query (кэш общий с CityTradeLocation) ──
  const { 
    data: cityShopData, 
    isError: isCityShopError,
    refetch: refetchCityShop,
  } = useGetCityShopQuery(
    { locationSlug, characterId: activeCharacterId },
    { 
      skip: !locationSlug || !activeCharacterId,
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
  const handleRefresh = useCallback(async () => {
    await refetchCityShop();
    await onRefresh?.();
  }, [refetchCityShop, onRefresh]);
 

  // ── Guards ──
  if (hasShop === null) return null;

  return (
    <LicenseView
      initialShopData={shopData}
      initialHasShop={hasShop}
      locationSlug={locationSlug}
      shopType={shopType}
      onRefresh={handleRefresh}     
    />
  );
}

export default LicenseViewContainer;