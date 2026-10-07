import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { useDispatch } from 'react-redux';
import { inventoryApi } from '../../../../entities/items/api/inventoryApi';

// --- Shared / API ---
import { DealsWebSocket } from "../../../../shared/lib/websocket/DealsWebSocket";
import { adaptItemForCard } from '../../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { useGetMyResourcesQuery } from "../../../../entities/resources/api/resourcesApi";
import { useResourceInfo } from '../../../../entities/resources/hooks/useResourceInfo';
import {
  useCreateDealMutation, useAcceptDealMutation, useConfirmDealMutation,
  useCancelDealMutation, useSetDealDucatsMutation, useSetDealGoldMutation,
  useAddDealResourceMutation, useRemoveDealResourceMutation,
  useAddDealItemMutation, useRemoveDealItemMutation,
} from "../../../../entities/items/api/inventoryApi";
import {
  useGetNearbyPartnersQuery,
  useGetTradeLicenseStatusQuery,
  useGetCharacterItemsQuery,
  useGetMyEquipmentQuery,
  useGetDealQuery,  
} from '../../../../entities/items/api/inventoryApi';


// 🆕 Импортируем константы из общего файла
import { 
  DEAL_STATUS, 
  FINAL_DEAL_STATUSES, 
  DEAL_ALLOWED_LOCATIONS, 
  DEAL_ERROR_TEXTS 
} from "../constants";

// ==========================================
// UTILS
// ==========================================


const getDealError = (e, fallback) => {
  const errorCode = e?.data?.error_code || e?.response?.data?.error_code;
  const detail = e?.data?.detail || e?.response?.data?.detail;
  // 1. Точный detail из бэка — самый конкретный вариант
  if (detail && DEAL_ERROR_TEXTS[detail]) return DEAL_ERROR_TEXTS[detail];
  // 2. Ресурсы: бэк использует для них тот же код DEAL_ASSET_UNAVAILABLE,
  //    поэтому нехватку доступного ресурса проверяем ДО маппинга по коду
  if (typeof detail === "string" && detail.toLowerCase().includes("insufficient available resource")) return "Недостаточно ресурсов";
  // 3. Старый английский fallback для предметов (пока бэк не отдаёт русский detail)
  if (typeof detail === "string" && detail.toLowerCase().includes("inventory item")) return DEAL_ERROR_TEXTS.DEAL_ASSET_UNAVAILABLE;
  // 4. Русский detail от бэка — конкретная причина (эскроу-проверки AddDealInventoryItem
  //    и другие локализованные ошибки): показываем как есть, НЕ подменяя общим текстом по коду
  if (typeof detail === "string" && /[а-яё]/i.test(detail)) return detail;
  // 5. Общий маппинг по error_code (fallback: detail пустой или английский без маппинга)
  if (errorCode && DEAL_ERROR_TEXTS[errorCode]) return DEAL_ERROR_TEXTS[errorCode];
  return detail || fallback;
};

// ==========================================
// HOOK
// ==========================================

export function useDealsLogic(character, onRefresh) {
  // --- Redux & RTK Query --- 
  const dispatch = useDispatch();

  const [createDeal] = useCreateDealMutation();
  const [acceptDeal] = useAcceptDealMutation();
  const [confirmDeal] = useConfirmDealMutation();
  const [cancelDeal] = useCancelDealMutation();
  const [setDealDucats] = useSetDealDucatsMutation();
  const [setDealGold] = useSetDealGoldMutation();
  const [addDealResource] = useAddDealResourceMutation();
  const [removeDealResource] = useRemoveDealResourceMutation();
  const [addDealItem] = useAddDealItemMutation();
  const [removeDealItem] = useRemoveDealItemMutation();

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  const lastPartnersRef = useRef([]);
  const lastLicenseRef = useRef(null);
  const lastItemsRef = useRef([]);
  const lastEquipmentRef = useRef([]);
  const lastResourcesRef = useRef([]);
  const lastDealRef = useRef(null);

  // --- RTK Query: чтение данных ---
  const {
    data: nearbyPartnersData,
    isLoading: isPartnersLoading,    
  } = useGetNearbyPartnersQuery(character?.location_slug, {
    skip: !character?.location_slug,
    refetchOnFocus: true,    
  });

  const {
    data: tradeLicenseData,
    isLoading: isLicenseLoading,   
  } = useGetTradeLicenseStatusQuery({ characterId: character?.id }, {
    skip: !character?.id,
    refetchOnFocus: true,    
  });

  const {
    data: myItemsData,
    isLoading: isItemsLoading,
    refetch: refetchItems,
  } = useGetCharacterItemsQuery(undefined, {
    skip: !character?.id,
    refetchOnFocus: true,    
  });

  const {
    data: myEquipmentData,
    isLoading: isEquipmentLoading,    
  } = useGetMyEquipmentQuery(undefined, {
    skip: !character?.id,
    refetchOnFocus: true,    
  });

  const {
    data: myResourcesData,
    isLoading: isResourcesLoading,
    refetch: refetchResources,
  } = useGetMyResourcesQuery(undefined, {
    skip: !character?.id,
    refetchOnFocus: true,    
  });

  // --- State для активной сделки ---
  const [activeDealId, setActiveDealId] = useState(null);

  const {
    data: activeDealData,
    isLoading: isDealLoading,
    refetch: refetchDeal,
  } = useGetDealQuery(activeDealId, {
    skip: !activeDealId,
    refetchOnFocus: true,    
  });

  // ═══ lastDataRef обновление ═══
  if (nearbyPartnersData !== undefined) {
    lastPartnersRef.current = nearbyPartnersData || [];
  }
  if (tradeLicenseData !== undefined) {
    lastLicenseRef.current = tradeLicenseData;
  }
  if (myItemsData !== undefined) {
    lastItemsRef.current = myItemsData || [];
  }
  if (myEquipmentData !== undefined) {
    lastEquipmentRef.current = myEquipmentData || [];
  }
  if (myResourcesData !== undefined) {
    lastResourcesRef.current = myResourcesData || [];
  }
  if (activeDealData !== undefined) {
    lastDealRef.current = activeDealData;
  }


  // --- State ---
  const [activeDeal, setActiveDeal] = useState(null);
  const [nearbyPartners, setNearbyPartners] = useState([]);
  const [selectedPartnerId, setSelectedPartnerId] = useState("");
  const [cachedPartnerName, setCachedPartnerName] = useState("");
  const [myItems, setMyItems] = useState([]);
  const [myResources, setMyResources] = useState([]);
  const [moneyInput, setMoneyInput] = useState("");
  const [selectedCurrency, setSelectedCurrency] = useState('ducats');
  const [quantities, setQuantities] = useState({});
  const [taxRate, setTaxRate] = useState(null);
  const isLoading = isPartnersLoading || isLicenseLoading || isItemsLoading || 
                  isEquipmentLoading || isResourcesLoading || isDealLoading;
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);

  // --- Синхронизация RTK Query → state ---
  useEffect(() => {
    if (nearbyPartnersData !== undefined) {
      setNearbyPartners((nearbyPartnersData || []).filter(p => p.id !== character?.id));
    } else if (lastPartnersRef.current.length > 0) {
      setNearbyPartners(lastPartnersRef.current);
    }
  }, [nearbyPartnersData, character?.id]);

  useEffect(() => {
    if (tradeLicenseData !== undefined) {
      setTaxRate(tradeLicenseData);
    } else if (lastLicenseRef.current) {
      setTaxRate(lastLicenseRef.current);
    }
  }, [tradeLicenseData]);

  useEffect(() => {
    if (myItemsData !== undefined && myEquipmentData !== undefined) {
      const equippedIds = new Set((myEquipmentData || []).map(eq => eq.id));
      const allowedItems = (myItemsData || []).filter(it => {
        const loc = it.item?.location_slug;
        if (!loc || !DEAL_ALLOWED_LOCATIONS.has(loc)) return false;
        return !equippedIds.has(it.id);
      });
      
      setMyItems(prev => {
        if (prev.length !== allowedItems.length) return allowedItems;
        for (let i = 0; i < prev.length; i++) {
          if (prev[i].id !== allowedItems[i].id || prev[i].amount !== allowedItems[i].amount) return allowedItems;
        }
        return prev;
      });
    } else if (lastItemsRef.current.length > 0 && lastEquipmentRef.current.length > 0) {
      // Fallback на lastDataRef при протухании кэша
      const equippedIds = new Set((lastEquipmentRef.current || []).map(eq => eq.id));
      const allowedItems = (lastItemsRef.current || []).filter(it => {
        const loc = it.item?.location_slug;
        if (!loc || !DEAL_ALLOWED_LOCATIONS.has(loc)) return false;
        return !equippedIds.has(it.id);
      });
      setMyItems(allowedItems);
    }
  }, [myItemsData, myEquipmentData]);

  useEffect(() => {
    if (myResourcesData !== undefined) {
      setMyResources(prev => {
        if (prev.length !== myResourcesData.length) return myResourcesData || [];
        for (let i = 0; i < prev.length; i++) {
          const a = prev[i], b = myResourcesData[i];
          if (a.resource_slug !== b.resource_slug || a.amount !== b.amount || a.resource_name !== b.resource_name) return myResourcesData || [];
        }
        return prev;
      });
    } else if (lastResourcesRef.current.length > 0) {
      setMyResources(lastResourcesRef.current);
    }
  }, [myResourcesData]);

  useEffect(() => {
    if (activeDealData !== undefined) {
      setActiveDeal(activeDealData);
    } else if (lastDealRef.current) {
      setActiveDeal(lastDealRef.current);
    }
  }, [activeDealData]);

  // --- Refs ---
  const activeDealRef = useRef(null);
  activeDealRef.current = activeDeal;
  const selfCancelRef = useRef(false);
  const dealGenRef = useRef(0);
  const exitingRef = useRef(false);
  const onRefreshRef = useRef(onRefresh);
    
  const closeDealScreenRef = useRef(null);
  const stableOnRefreshRef = useRef(null);
  const fetchSeqRef = useRef(0);  

  // --- Derived State & Memos ---
  const myId = character?.id;
  const hasGold = parseFloat(character?.gold || 0) > 0;
  const round2 = (x) => Math.round(x * 100) / 100;

  const isInitiator = activeDeal?.initiator_character_id === myId;
  const myOffer = activeDeal?.offers?.find(o => o.character_id === myId);
  const partnerOffer = activeDeal?.offers?.find(o => o.character_id !== myId);
  
  const myDealItems = useMemo(
    () => activeDeal?.items?.filter(i => i.owner_character_id === myId) || [],
    [activeDeal, myId]
  );
  const partnerDealItems = useMemo(
    () => activeDeal?.items?.filter(i => i.owner_character_id !== myId) || [],
    [activeDeal, myId]
  );

  const partnerResources = useMemo(() => {
    if (!partnerDealItems || partnerDealItems.length === 0) return [];
    return partnerDealItems
      .filter(it => it.asset_type === "RESOURCE")
      .map(it => ({
        resource_slug: it.resource_slug,
        resource_name: it.item_snapshot?.name || it.resource_slug,
        price: it.item_snapshot?.price || 0,
        weight: it.item_snapshot?.weight || 0,
      }));
  }, [partnerDealItems]);

  const allCachedResources = useMemo(() => {
    return [...myResources, ...partnerResources];
  }, [myResources, partnerResources]);
  
  const { selectedResource, openResource, closeResource } = useResourceInfo(allCachedResources);

  const iConfirmed = !!myOffer && myOffer.confirmed_revision != null && myOffer.confirmed_revision === myOffer.revision;
  const partnerConfirmed = !!partnerOffer && partnerOffer.confirmed_revision != null && partnerOffer.confirmed_revision === partnerOffer.revision;
  
  // 🆕 Используем константы DEAL_STATUS
  const dealFinished = !!activeDeal && ![DEAL_STATUS.DRAFT, DEAL_STATUS.ACTIVE].includes(activeDeal.status);
  const isEditable = !!activeDeal && !dealFinished && !iConfirmed;
  const leftDisabled = !activeDeal || !isEditable || isProcessing;

  const partnerId = activeDeal ? (isInitiator ? activeDeal.partner_character_id : activeDeal.initiator_character_id) : null;
  const partnerName = cachedPartnerName || nearbyPartners.find(p => p.id === partnerId)?.name || "Партнёр";
  const incomingDucats = parseFloat(partnerOffer?.ducats_escrowed || 0);
  const myTax = taxRate ? incomingDucats * parseFloat(taxRate.deal_tax_rate || 0) : 0;

  // --- Core Functions ---
  const stableOnRefresh = useCallback(() => {
    onRefreshRef.current?.();
  }, []);

  const closeDealScreen = useCallback(() => {
    dealGenRef.current += 1;
    setActiveDeal(null);
    setActiveDealId(null);
  }, []);

 

  

  

  // --- Helpers ---
  const myDealResourceAmount = useCallback((slug) => {
    const it = myDealItems.find(i => i.asset_type === "RESOURCE" && i.resource_slug === slug);
    return it ? it.amount : 0;
  }, [myDealItems]);
 
  const resFree = useCallback((res) => {
    if (!res) return 0;
    const inDeal = myDealResourceAmount(res.resource_slug);
    return Math.max(0, (res.amount || 0) - inDeal);
  }, [myDealResourceAmount]);

  const resourceNameBySlug = useCallback((slug) => myResources.find(r => r.resource_slug === slug)?.resource_name || slug, [myResources]);

  const displayName = useCallback((it) => {
    if (it.asset_type === "RESOURCE") return it.item_snapshot?.name || resourceNameBySlug(it.resource_slug) || it.resource_slug;
    return it.item_snapshot?.name || "Предмет";
  }, [resourceNameBySlug]);

  const isItemAsset = useCallback((it) => it.asset_type === "ITEM" || it.asset_type === "INVENTORY_ITEM", []);

  const openDealItemCard = (it) => {
    const full = myItems.find(mi => mi.id === it.inventory_item_id);
    if (full) {
      setSelectedItem(adaptItemForCard(full));
      return;
    }
    setSelectedItem(adaptItemForCard({
      name: it.item_snapshot?.name || "Предмет",
      item_type: it.item_snapshot?.item_type,
      slug: it.item_snapshot?.item_slug,
      price: it.item_snapshot?.price,
      weight: it.item_snapshot?.weight,
      wear: it.item_snapshot?.wear,
      expired_date: it.item_snapshot?.expired_date,
      used_count: it.item_snapshot?.used_count,
      parameters: it.item_snapshot?.parameters || {},
      ability_parameters: it.item_snapshot?.ability_parameters || {},
      minimal_level: it.item_snapshot?.minimal_level,
      race: it.item_snapshot?.race,
    }));
  };

  const setQty = useCallback((key, value) => setQuantities(prev => ({ ...prev, [key]: value })), []);
  
  const getQty = useCallback((key, fallback) => {
    const v = parseInt(quantities[key], 10);
    return Number.isFinite(v) && v > 0 ? Math.min(v, fallback) : fallback;
  }, [quantities]);

  const refreshAfterChange = useCallback(async () => {
    await Promise.all([refetchDeal(), refetchItems(), refetchResources()]);
    stableOnRefresh();
  }, [refetchDeal, refetchItems, refetchResources, stableOnRefresh]);

  // --- Event Handlers ---
  const handleSelectPartner = async () => {
    if (!selectedPartnerId) return;
    setIsProcessing(true);
    setErrorMessage("");
    try {
      const partner = nearbyPartners.find(p => p.id === selectedPartnerId);
      setCachedPartnerName(partner?.name || "Партнёр");

      // Используем RTK Query для поиска существующей сделки
      const dealsRes = await dispatch(inventoryApi.endpoints.getDeals.initiate(undefined, { forceRefetch: true })).unwrap();
      const freshDeals = dealsRes?.objects || [];

      const existing = freshDeals
  .filter(d =>
    (d.status === DEAL_STATUS.DRAFT || d.status === DEAL_STATUS.ACTIVE) &&
    ((d.initiator_character_id === myId && d.partner_character_id === selectedPartnerId) ||
     (d.initiator_character_id === selectedPartnerId && d.partner_character_id === myId))
  )
  .sort((a, b) => new Date(b.updated_at || 0) - new Date(a.updated_at || 0))[0];

      if (existing) {
        if (existing.status === DEAL_STATUS.DRAFT && existing.partner_character_id === myId) {
          await acceptDeal(existing.id).unwrap();
        }
        // Принудительно рефетчим сделку перед установкой ID
        await dispatch(inventoryApi.endpoints.getDeal.initiate(existing.id, { forceRefetch: true })).unwrap();
        setActiveDealId(existing.id);
      } else {
        const deal = await createDeal({ partnerCharacterId: selectedPartnerId, locationSlug: character?.location_slug }).unwrap();
        // Принудительно рефетчим сделку перед установкой ID
        await dispatch(inventoryApi.endpoints.getDeal.initiate(deal.id, { forceRefetch: true })).unwrap();
        setActiveDealId(deal.id);
      }
      await refetchItems();
      await refetchResources();
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка создания сделки"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddMoney = async () => {
    if (!activeDeal) return;
    const amount = parseFloat(moneyInput);
    if (!(amount > 0)) return;    
    setIsProcessing(true);
    try {
      if (selectedCurrency === 'ducats') {
        const current = parseFloat(myOffer?.ducats_escrowed || 0);
        await setDealDucats({ dealId: activeDeal.id, amount: round2(current + amount) }).unwrap();
      } else {
        const current = parseFloat(myOffer?.gold_escrowed || 0);
        await setDealGold({ dealId: activeDeal.id, amount: round2(current + amount) }).unwrap();
      }
      setMoneyInput("");
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка добавления денег"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddResource = (resourceSlug) => async () => {
    if (!activeDeal) return;
    const res = myResources.find(r => r.resource_slug === resourceSlug);
    const delta = getQty(resourceSlug, resFree(res));
    if (!(delta > 0)) return;
    const newTotal = myDealResourceAmount(resourceSlug) + delta;
    setIsProcessing(true);
    try {
      await addDealResource({ dealId: activeDeal.id, resourceSlug, amount: newTotal }).unwrap();
      const newFree = Math.max((res?.amount || 0) - newTotal, 0);
      setQuantities(prev => ({ ...prev, [resourceSlug]: String(newFree) }));
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveResource = (resourceSlug) => async () => {
    if (!activeDeal) return;
    setIsProcessing(true);
    try {
      const res = myResources.find(r => r.resource_slug === resourceSlug);
      await removeDealResource({ dealId: activeDeal.id, resourceSlug }).unwrap();
      setQuantities(prev => ({ ...prev, [resourceSlug]: String(res?.amount || 0) }));
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddItem = (inv) => async () => {
    if (!activeDeal) return;
    const stackable = inv.item?.is_stackable && inv.amount > 1;
    const amount = stackable ? getQty(inv.id, inv.amount) : inv.amount;
    setIsProcessing(true);
    try {
      await addDealItem({ dealId: activeDeal.id, inventoryItemId: inv.id, amount }).unwrap();
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveItem = (dealItemId) => async () => {
    if (!activeDeal) return;
    setIsProcessing(true);
    try {
      await removeDealItem({ dealId: activeDeal.id, dealItemId }).unwrap();
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveDucats = async () => {
    if (!activeDeal) return;
    setIsProcessing(true);
    try {
      await setDealDucats({ dealId: activeDeal.id, amount: 0 }).unwrap();
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRemoveGold = async () => {
    if (!activeDeal) return;
    setIsProcessing(true);
    try {
      await setDealGold({ dealId: activeDeal.id, amount: 0 }).unwrap();
      await refreshAfterChange(activeDeal.id);
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirm = async () => {
    if (!activeDeal) return;
    const gen = dealGenRef.current;
    setIsProcessing(true);
    try {
      const deal = await confirmDeal(activeDeal.id).unwrap();
      if (gen !== dealGenRef.current) return;

      if (deal?.status === DEAL_STATUS.COMPLETED) {
        closeDealScreen();
        await refetchItems();
        await refetchResources();
        stableOnRefresh();
      } else {
        await refetchDeal();
        await refetchItems();
        await refetchResources();
        stableOnRefresh();
      }
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка подтверждения"));
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCancel = async () => {
    if (!activeDeal) return;
    const dealId = activeDeal.id;
    setIsProcessing(true);
    setErrorMessage("");
    closeDealScreen();
    try {
      selfCancelRef.current = true;
      await cancelDeal(dealId).unwrap();
      await refetchItems();
      await refetchResources();
      stableOnRefresh();
    } catch (e) {
      setErrorMessage(getDealError(e, "Ошибка отмены"));
      setActiveDealId(dealId);  // Загрузит сделку заново через RTK Query
    } finally {
      setIsProcessing(false);
      selfCancelRef.current = false;
    }
  };

  // --- Effects ---
  
  // 1. Sync onRefresh ref
  useEffect(() => { 
    onRefreshRef.current = onRefresh; 
  }, [onRefresh]);

  // 2. Sync callback refs (prevents WebSocket reconnects)
  useEffect(() => {    
    closeDealScreenRef.current = closeDealScreen;
    stableOnRefreshRef.current = stableOnRefresh;
  }, [closeDealScreen, stableOnRefresh]);

  // 3. Autosync currency if gold runs out
  useEffect(() => {
    if (!hasGold && selectedCurrency === 'gold') {
      setSelectedCurrency('ducats');
    }
  }, [hasGold, selectedCurrency]);

  // 4. Error timeout
  useEffect(() => { 
    if (errorMessage) { 
      const t = setTimeout(() => setErrorMessage(""), 5000); 
      return () => clearTimeout(t); 
    } 
  }, [errorMessage]);

  
  // 5. Initial Load
  useEffect(() => {
    closeDealScreen();
    setActiveDealId(null);
    setSelectedPartnerId("");
    setCachedPartnerName("");
    setMoneyInput("");
    setSelectedCurrency('ducats');
    setQuantities({});
    setErrorMessage("");
  }, [character?.id, character?.location_slug, closeDealScreen]);

  // 6. WebSocket
  useEffect(() => {
    if (!character?.id || !character?.location_slug) return;
    exitingRef.current = false;    
    
    const handleGameExiting = () => { exitingRef.current = true; };
    window.addEventListener('game-exiting', handleGameExiting);

  const refreshDealQuietly = async (dealId) => {
    if (selfCancelRef.current) return;
    if (activeDealRef.current?.id !== dealId) return;
    const gen = dealGenRef.current;
    const seq = ++fetchSeqRef.current;
    
    const deal = await dispatch(inventoryApi.endpoints.getDeal.initiate(dealId, { forceRefetch: true })).unwrap().catch(() => null);
    
    if (!deal || gen !== dealGenRef.current || seq !== fetchSeqRef.current) return;
    if (selfCancelRef.current) return;
    if (activeDealRef.current?.id !== dealId) return;
    if (FINAL_DEAL_STATUSES.has(deal.status)) {
      closeDealScreenRef.current();
      await refetchItems();
      await refetchResources();
      stableOnRefreshRef.current();
      return;
    }
    setActiveDealId(dealId);
  };

    const handleDealEvent = async (message) => {
      if (exitingRef.current) return;
      const eventData = message.data || message;
      const isInitiator = eventData.initiator_character_id === character?.id;
      const isPartner = eventData.partner_character_id === character?.id;
      if (!isInitiator && !isPartner) return;
      
      const eventType = message.event_type;
      const dealId = eventData.deal_id;
      const currentActiveDeal = activeDealRef.current;
      const isMyDeal = currentActiveDeal && currentActiveDeal.id === dealId;

      switch (eventType) {
        case 'deal_created':
          if (currentActiveDeal) {
            if (FINAL_DEAL_STATUSES.has(currentActiveDeal.status)) {
              closeDealScreenRef.current();
            }
            return;
          }
          break;
        case 'deal_accepted':
          if (isMyDeal) await refreshDealQuietly(dealId);
          break;
        case 'deal_updated':
        case 'deal_confirmed':
          if (isMyDeal) {
            await refreshDealQuietly(dealId);
            // Рюкзак перезагружаем только если экран реально остался открыт
            // на этой сделке — при закрытом экране это лишний запрос.
            if (activeDealRef.current?.id === dealId) {
              await refetchItems();
              await refetchResources();
            }
          }
          break;
        case 'deal_completed':
          if (isMyDeal) {
            closeDealScreenRef.current();
            await refetchItems();
            await refetchResources();
            stableOnRefreshRef.current();
          }
          break;
        case 'deal_cancelled':
          if (isMyDeal) {
            closeDealScreenRef.current();
            await refetchItems();
            await refetchResources();
            stableOnRefreshRef.current();
          }
          break;
        case 'deal_expired':
          if (isMyDeal) {
            closeDealScreenRef.current();
            await refetchItems();
            await refetchResources();
            stableOnRefreshRef.current();
          }
          break;
      }
    };

    const ws = new DealsWebSocket(
      character.location_slug,
      handleDealEvent,
      (error) => console.error('Deals WebSocket error:', error),
      () => { if (import.meta.env.DEV) console.log('Deals WebSocket closed'); },
      () => {
        // Ресинк после реконнекта: события, пропущенные во время обрыва
        if (activeDealRef.current) {
          refreshDealQuietly(activeDealRef.current.id);
        }
      }
    );
    ws.connect();
    
    return () => {
      window.removeEventListener('game-exiting', handleGameExiting);
      if (ws) ws.disconnect();
    };
  }, [character?.id, character?.location_slug, dispatch, refetchItems, refetchResources]);

  // 7. Presence Events
  useEffect(() => {
    if (!character?.id || !character?.location_slug) return;

    const handlePresenceEvent = (event) => {
      const message = event.detail;

      if (message.event_type === "character_online") {
        const { character_id, is_online, location_slug, name, level } = message;

        if (character_id === character?.id) return;  // ← себя не добавляем

        if (is_online && location_slug === character.location_slug) {
          setNearbyPartners(prev => {
            if (prev.find(p => p.id === character_id)) return prev;
            return [...prev, { id: character_id, name, level, location_slug }];
          });
        } else if (!is_online || location_slug !== character.location_slug) {
          setNearbyPartners(prev => prev.filter(p => p.id !== character_id));
        }
      } else if (message.event_type === "character_location") {
        const { character_id, old_location_slug, new_location_slug, name, level } = message;

        if (character_id === character?.id) return;  // ← и здесь

        if (new_location_slug === character.location_slug) {
          setNearbyPartners(prev => {
            if (prev.find(p => p.id === character_id)) return prev;
            return [...prev, { id: character_id, name, level, location_slug: new_location_slug }];
          });
        } else if (old_location_slug === character.location_slug) {
          setNearbyPartners(prev => prev.filter(p => p.id !== character_id));
        }
      }
    };

    // eslint-disable-next-line no-restricted-syntax -- фильтр своих событий есть в обеих ветках handlePresenceEvent: character_id === character?.id
    window.addEventListener('presence-event', handlePresenceEvent);
    return () => window.removeEventListener('presence-event', handlePresenceEvent);
  }, [character?.id, character?.location_slug]);

  
  // --- Return Public API for UI ---
  return {
    // States
    activeDeal, nearbyPartners, myItems, myResources,
    moneyInput, setMoneyInput, selectedCurrency, setSelectedCurrency,
    quantities, setQty, getQty,
    isLoading, isProcessing, errorMessage,
    selectedItem, setSelectedItem, selectedResource,
    selectedPartnerId, setSelectedPartnerId, cachedPartnerName,
    
    // Derived
    hasGold, isInitiator, myOffer, partnerOffer,
    myDealItems, partnerDealItems, iConfirmed, partnerConfirmed,
    dealFinished, isEditable, leftDisabled, partnerId, partnerName, myTax,
    
    // Handlers
    openResource, closeResource, openDealItemCard,
    handleSelectPartner, handleAddMoney, handleAddResource, handleRemoveResource,
    handleAddItem, handleRemoveItem, handleRemoveDucats, handleRemoveGold,
    handleConfirm, handleCancel, displayName, isItemAsset, resFree,
  };
}
