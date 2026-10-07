import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useDispatch } from "react-redux";
import { config } from "../../../shared/config/env/env";
import { 
  useGetShopsListQuery, 
  useLazyGetCityShopByNumberQuery,
  inventoryApi,
} from '../../../entities/items/api/inventoryApi';
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import { getTradeFilters } from "../config/tradeFiltersConfig";
import ItemSearchView from "./ItemSearchView";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import { intInputHandler } from '../../../shared/lib/validation/numberInput';
import styles from "./ShopsListView.module.css";
import btn from '../../../shared/styles/buttons.module.css';
import { DataState } from '../../../shared/ui/DataState/DataState';

// ... (ShopRowItem оставляем БЕЗ ИЗМЕНЕНИЙ, он идеален) ...
const ShopRowItem = ({ shop, typeName, onShopClick }) => {  
  const uniqueItems = useMemo(() => {
    if (!shop.sale_items?.length) return [];
    const priceMap = new Map();
    shop.sale_items.forEach(item => {
      const price = Number(item.price);
      const existing = priceMap.get(item.item_name);
      if (!existing || price < existing.price) {
        priceMap.set(item.item_name, { item_name: item.item_name, price });
      }
    });    
    return Array.from(priceMap.values());
  }, [shop.sale_items]); 

  // Версионирование URL для обхода браузерного кэша картинок
  const photoSrc = shop.photo?.id 
    ? `${config.FILE_API_BASE_URL}/${shop.photo.id}/content?v=${shop.photo.updated_at || shop.updated_at || Date.now()}` 
    : '/images/city-trade/no-image.png';

  return (
    <div className={styles.shopRow}>
      <div className={styles.leftPart}>
        <div className={styles.imageCell} onClick={() => onShopClick(shop.id, shop)} style={{ cursor: 'pointer' }}>
          <img 
            src={photoSrc} 
            alt={shop.name} 
            className={styles.shopImage} 
            fetchPriority="high"   /* <-- ДОБАВИТЬ: заставляет браузер качать это в первую очередь */
            loading="eager"        /* <-- ДОБАВИТЬ: отменяет ленивую загрузку для этих картинок */
            onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/images/city-trade/no-image.png'; }} 
          />
        </div>
        <div className={styles.infoCell}>
          <span className={styles.shopTitle} onClick={() => onShopClick(shop.id, shop)} style={{ cursor: 'pointer' }}>{typeName} № {shop.number}</span>
          <span className={styles.shopSubtitle}>{shop.name}</span>
          {shop.description && <div className={styles.shopDescription}>{shop.description}</div>}
        </div>
      </div>
      <div className={styles.itemsCell}>
        {uniqueItems.length > 0 ? (
          <div className={styles.saleItems}>
            {uniqueItems.map((item, index) => (
              <React.Fragment key={item.item_name}>
                <span className={styles.itemName}>{item.item_name} </span>
                <span className={styles.itemPrice}>{Number(item.price).toFixed(2)} дт</span>
                {index < uniqueItems.length - 1 && <span>, </span>}
              </React.Fragment>
            ))}
          </div>          
        ) : <div className={styles.noItems}>Нет товаров</div>}
      </div>
    </div>
  );
};

function ShopsListView({ parentLocationSlug, onShopClick, emptyMessage = "Магазины не найдены" }) { 

  const [currentPage, setCurrentPage] = useState(1);
  const [shopNumberInput, setShopNumberInput] = useState("");
  const [searchItem, setSearchItem] = useState(null);
  const [selectedKind, setSelectedKind] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("");
  const [activeRaceTabs, setActiveRaceTabs] = useState({});
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const pageSize = 5;
  const { currentError, showError } = useErrorToast();

  const filtersConfig = getTradeFilters(parentLocationSlug);
  const showAdvancedFilters = !!filtersConfig.advancedFilters;

  const dispatch = useDispatch();
  // Маркер последнего выбора: ответ более раннего прогрева не должен
  // перезаписывать более поздний выбор пользователя (гонка await'ов).
  const latestSelectionRef = useRef(0);

  const SEARCH_GATE_TIMEOUT_MS = 3000;

  // Прогрев запроса поиска ДО подмены списка: ItemSearchView монтируется
  // с тёплым кэшем → полный кадр с первого рендера. 3 сек — предохранитель,
  // как в useViewEntryPrefetches: при зависшем запросе подменяем и даём ему грузиться.
  const openSearch = useCallback(async (searchArgs) => {
    await Promise.race([
      dispatch(inventoryApi.endpoints.getShopsList.initiate(searchArgs, { subscribe: false })).catch(() => null),
      new Promise((res) => setTimeout(res, SEARCH_GATE_TIMEOUT_MS)),
    ]);
  }, [dispatch]);

  // Клик на лавку ИЗ РЕЗУЛЬТАТОВ ПОИСКА: данных лавки в строке нет —
  // греем detail-запрос и переходим. Из СПИСКА клик идёт напрямую
  // (данные строки = initialShopData, кадр мгновенный).
  const handleShopClickFromSearch = useCallback(async (shopId) => {
    const token = ++latestSelectionRef.current;
    await Promise.race([
      dispatch(inventoryApi.endpoints.getCityShopById.initiate(shopId, { subscribe: false })).catch(() => null),
      new Promise((res) => setTimeout(res, SEARCH_GATE_TIMEOUT_MS)),
    ]);
    if (token !== latestSelectionRef.current) return; // кликнули в другую лавку — устарели
    onShopClick(shopId);
  }, [dispatch, onShopClick]);

  // ═══ RTK QUERY: Список лавок ═══
  const queryArgs = useMemo(() => {
    const args = { locationSlug: parentLocationSlug, page: currentPage, pageSize };
    if (selectedLevel !== "") args.minimalLevel = Number(selectedLevel);
    if (selectedKind !== "") args.itemKind = selectedKind;
    return args;
  }, [parentLocationSlug, currentPage, selectedLevel, selectedKind]);

  const {
    data: shopsData,
    isError: shopsError,
    refetch: refetchShops,    
  } = useGetShopsListQuery(queryArgs, {
    skip: !parentLocationSlug,
    refetchOnFocus: true,    
    refetchOnMountOrArgChange: 5,
  });

  

  const lastDataRef = useRef(null);
  if (shopsData) lastDataRef.current = shopsData;
  const displayData = shopsData ?? lastDataRef.current;

  // ═══ RTK QUERY: Ленивый поиск по номеру ═══
  const [getShopByNumber] = useLazyGetCityShopByNumberQuery();

  // Сброс при смене локации
  useEffect(() => {
    latestSelectionRef.current += 1; // сброс: ожидающие прогревы неактуальны
    lastDataRef.current = null;
    setCurrentPage(1);
    setSearchItem(null);
    setSelectedKind("");
    setSelectedLevel("");
    setShopNumberInput("");
    setIsFilterOpen(false);
  }, [parentLocationSlug]);

  

  // ═══ HANDLERS ═══
  const handleNumberChange = intInputHandler(setShopNumberInput, 7, { strip: true });

  const handleGoToShop = async () => {
    const num = parseInt(shopNumberInput, 10);
    if (!num) return;
    try {
      const shop = await getShopByNumber(num).unwrap();
      if (shop) {
        const shopId = shop.id || shop.shop?.id;
        onShopClick(shopId, shop);
        setShopNumberInput("");
      }
    } catch {
      // ПОКАЗЫВАЕМ ОШИБКУ ПОЛЬЗОВАТЕЛЮ
      showError(`Номер ${num} не найден`);
    }
  };

  const handleGroupChange = async (group, value) => {
    const token = ++latestSelectionRef.current;
    if (showAdvancedFilters) {
      if (!value) {
        setSelectedKind(value);
        setCurrentPage(1);
        return;
      }
      // Сначала греем кэш, потом подменяем список — без пустого кадра
      await openSearch({ locationSlug: parentLocationSlug, page: 1, pageSize: 20, itemKind: value });
      if (token !== latestSelectionRef.current) return; // выбор уже устарел
      setSelectedKind(value);
      setCurrentPage(1);
      return;
    }
    if (value) {
      const activeTab = group.tabs ? activeRaceTabs[group.id] || group.defaultTab : null;
      const opt = group.options.find((o) => o.value === value && (!o.tab || o.tab === activeTab));
      await openSearch({ locationSlug: parentLocationSlug, page: 1, pageSize: 20, itemName: value });
      if (token !== latestSelectionRef.current) return; // выбор уже устарел
      setSearchItem({ groupId: group.id, value, label: opt ? opt.label : value });
    } else {
      setSearchItem(null);
    }
  };

  const handleRaceTabClick = (groupId, tabId) => {
    latestSelectionRef.current += 1; // сброс: ожидающие прогревы неактуальны
    setActiveRaceTabs((prev) => ({ ...prev, [groupId]: tabId }));
    setSearchItem((prev) => {
      if (prev && prev.groupId === groupId) return null;
      return prev;
    });
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (displayData && currentPage < displayData.total_pages) setCurrentPage(currentPage + 1);
  };

  const getShopTypeName = (slug) => getTradeLocationConfig(slug)?.shopType || 'Лавка';

  const filterBar = (
    <>
      <ErrorToast message={currentError} />
      <div className={styles.filterBar}>
        <div className={styles.filterRow}>
          <button type="button" className={styles.filterToggle} onClick={() => {
            setIsFilterOpen((v) => {
              const next = !v;
              if (!next && searchItem) {
                latestSelectionRef.current += 1;
                setSearchItem(null);
              }
              return next;
            });
          }}>
            
            <span>Фильтр</span>
          </button>
          <span className={styles.dot}>•</span>
          <input className={styles.filterInput} placeholder={filtersConfig.numberLabel} value={shopNumberInput} onChange={handleNumberChange} onKeyDown={(e) => e.key === "Enter" && handleGoToShop()} />
          <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={handleGoToShop}>Зайти</button>
          <span className={styles.dot}>•</span>
          <span className={styles.pagination}>
            <button className={`${styles.pageArrow} ${styles.pageArrowPrev}`} onClick={handlePrevPage} disabled={currentPage <= 1} title="Предыдущая страница" />
            <span className={styles.pageNumber}>{currentPage}</span>
            <button className={`${styles.pageArrow} ${styles.pageArrowNext}`} onClick={handleNextPage} disabled={!displayData || currentPage >= displayData.total_pages} title="Следующая страница" />
          </span>
        </div>
        {isFilterOpen && (filtersConfig.groups.length > 0 || filtersConfig.levels) && (
          <div className={styles.filterColumns}>
            {filtersConfig.levels && (
              <div className={styles.filterColumn}>
                <div className={styles.filterLabel}>Уровень</div>
                <select className={styles.filterSelect} value={selectedLevel} onChange={(e) => { setSelectedLevel(e.target.value); setCurrentPage(1); }}>
                  <option value="">- Все уровни -</option>
                  {filtersConfig.levels.map((lvl) => (<option key={lvl} value={lvl}>{lvl}</option>))}
                </select>
              </div>
            )}
            {filtersConfig.groups.map((group) => {
              const activeTab = group.tabs ? (activeRaceTabs[group.id] || group.defaultTab) : null;
              const visibleOptions = group.tabs ? group.options.filter((opt) => opt.tab === activeTab) : group.options;
              const selectValue = showAdvancedFilters
                ? (group.options.some((o) => o.value === selectedKind) ? selectedKind : "")
                : (searchItem?.groupId === group.id && (!group.tabs || group.options.find((o) => o.value === searchItem.value)?.tab === activeTab) ? searchItem.value : "");
              return (
                <div key={group.id} className={styles.filterColumn}>
                  {group.label && <div className={styles.filterLabel}>{group.label}</div>}
                  {group.tabs && (
                    <div className={styles.raceTabs}>
                      {group.tabs.map((tab) => (
                        <button key={tab.id} type="button" className={`${btn.textTab} ${btn.textTabLight} ${btn.textTabSmall} ${activeTab === tab.id ? btn.textTabActive : ''}`} onClick={() => handleRaceTabClick(group.id, tab.id)}>{tab.label}</button>
                      ))}
                    </div>
                  )}
                  <select className={styles.filterSelect} value={selectValue} onChange={(e) => handleGroupChange(group, e.target.value)}>
                    <option value="">- {group.placeholder} -</option>
                    {visibleOptions.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                  </select>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </>
  );

  // ═══ RENDER ═══
  if (!displayData && !shopsError) return null;

  if (showAdvancedFilters && selectedKind) {
    const kindLabel = filtersConfig.groups.flatMap((g) => g.options).find((o) => o.value === selectedKind)?.label || selectedKind;
    return (
      <>
        {filterBar}
        <ItemSearchView locationSlug={parentLocationSlug} itemKind={selectedKind} itemLabel={kindLabel} onShopClick={handleShopClickFromSearch} />
      </>
    );
  }

  if (!showAdvancedFilters && searchItem) {
    return (
      <>
        {filterBar}
        <ItemSearchView locationSlug={parentLocationSlug} itemName={searchItem.value} itemLabel={searchItem.label} onShopClick={handleShopClickFromSearch} />
      </>
    );
  }

  return (
    <>
      {filterBar}
      <DataState
        error={shopsError}
        errorMessage="Не удалось загрузить список магазинов"
        onRetry={refetchShops}
        isEmpty={!displayData?.items?.length}
        emptyMessage={emptyMessage}
      >
        <div className={styles.shopsContainer}>
          {(displayData?.items ?? []).map((shop) => (
            <ShopRowItem key={shop.id} shop={shop} typeName={getShopTypeName(shop.location_slug)} onShopClick={onShopClick} />
          ))}
        </div>
      </DataState>
    </>
  );
}

export default ShopsListView;