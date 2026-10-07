import { useEffect, useState, useMemo, useRef } from "react";
import { useGetShopsListQuery } from "../../../entities/items/api/inventoryApi"; 
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import { getLocationTexts } from '../config/locationTextConfig';
import styles from "../CityTradeLocation.module.css";
import shopStyles from "./ShopsListView.module.css";
import detailStyles from "./ShopDetailView.module.css";
import btn from '../../../shared/styles/buttons.module.css';
import { formatLicenseTime } from '../utils/dateFormatter';

function ItemSearchView({ locationSlug, itemName, itemKind, itemLabel, onShopClick }) {  
  const texts = getLocationTexts(locationSlug);
  const locationConfig = getTradeLocationConfig(locationSlug);
  const rawType = locationConfig?.shopType || 'Лавка';
  const shopTypeLabel = rawType.toLowerCase().includes('лавка') ? 'Лавка' : rawType;
  
  const [page, setPage] = useState(1);  

  // ═══ RTK QUERY ═══
  const { 
    data, 
    error, 
    isFetching, 
    refetch 
  } = useGetShopsListQuery({
    locationSlug,
    page,
    pageSize: 20,
    itemName: itemName || undefined,
    itemKind: itemKind || undefined,
  }, {
    skip: !locationSlug,
    refetchOnFocus: true,    
  });

  // 🆕 ЗАЩИТА ОТ МЕЛЬКАНИЯ: сохраняем последние данные
  const lastDataRef = useRef(null);
  const prevArgsRef = useRef({ itemName, itemKind, locationSlug });
  // Синхронный сброс при смене поиска — старая таблица не мелькнёт
  if (
    prevArgsRef.current.itemName !== itemName ||
    prevArgsRef.current.itemKind !== itemKind ||
    prevArgsRef.current.locationSlug !== locationSlug
  ) {
    lastDataRef.current = null;
    prevArgsRef.current = { itemName, itemKind, locationSlug };
  }
  if (data) lastDataRef.current = data;
  const displayData = data ?? lastDataRef.current;

  // Сброс страницы при изменении поиска или локации
  useEffect(() => { 
    setPage(1);     
  }, [itemName, itemKind, locationSlug]);  

  

  // ═══ COMPUTED ═══
  const allOffers = useMemo(() => {
    if (!displayData?.items) return [];
    return displayData.items.flatMap(shop =>
      shop.sale_items?.map(item => ({
        ...item,
        shop_id: shop.id,
        shop_number: shop.number,
        owner_name: shop.character_name,
      })) || []
    ).sort((a, b) => Number(a.price) - Number(b.price));
  }, [displayData]);

  // Заголовок из ПРОПСОВ напрямую (не из зеркального state): state через
  // useEffect отставал на рендер — заголовок показывал прошлый фильтр,
  // пока таблица уже показывала новый.
  const title = itemName
    ? (itemLabel && itemLabel !== itemName ? `${itemName} (${itemLabel})` : itemLabel)
    : (itemLabel || "");
    

  // ═══ RENDER ═══
  return (
    <div className={styles.searchWrap}>
      {/* Заголовок поиска — всегда, если есть данные или ошибка */}
      {(displayData || error) && (
        <div className={styles.searchHeader}>
          <span>{title}</span>
          <span className={styles.dot}>•</span>
          <span className={shopStyles.pagination}>
            <button
              className={`${shopStyles.pageArrow} ${shopStyles.pageArrowPrev}`}
              disabled={page <= 1 || isFetching}
              onClick={() => setPage(p => p - 1)}
              title="Предыдущая страница"
            />
            <span className={shopStyles.pageNumber}>{page}</span>
            <button
              className={`${shopStyles.pageArrow} ${shopStyles.pageArrowNext}`}
              disabled={page >= (displayData?.total_pages || 1) || isFetching}
              onClick={() => setPage(p => p + 1)}
              title="Следующая страница"
            />
          </span>
        </div>
      )}

      {/* Ошибка */}
      {error && (
        <div className={detailStyles.borderBox}>
          <div style={{ padding: '20px', textAlign: 'center' }}>
            Не удалось выполнить поиск
            <button 
              className={`${btn.gameButton} ${btn.sizeSmall}`}
              onClick={refetch}
              style={{ marginLeft: '10px' }}
            >
              Повторить
            </button>
          </div>
        </div>
      )}

      {/* Таблица — ТОЛЬКО когда есть данные */}
      {displayData && allOffers.length > 0 && (
        <div className={detailStyles.borderBox}>
          <table className={`${detailStyles.shopTable} ${detailStyles.searchTable}`}>
            <colgroup>
              <col /><col /><col /><col /><col />
            </colgroup>
            <thead>
              <tr>
                <th>{texts.wearColumnLabel}</th>
                <th className={detailStyles.hideOnMobile}>Кол-во</th>
                <th>Цена</th>
                <th className={detailStyles.hideOnMobile}>{shopTypeLabel}</th>
                <th>Владелец</th>
              </tr>
            </thead>
            <tbody>
              {allOffers.map(offer => (
                <tr key={offer.sale_id}>
                  <td>
                    {(offer.max_wear ?? offer.parameters?.max_wear) != null
                      ? `${offer.wear ?? 0}/${offer.max_wear ?? offer.parameters?.max_wear}`
                      : formatLicenseTime(offer.expired_date)}
                  </td>
                  <td className={detailStyles.hideOnMobile}>{offer.amount}</td>
                  <td>
                    {Number(offer.price).toFixed(2)}
                    <div className={detailStyles.mobileExtra}>Кол-во: {offer.amount}</div>
                  </td>
                  <td className={detailStyles.hideOnMobile}>
                    <span className={styles.searchShopLink} onClick={() => onShopClick?.(offer.shop_id)}>
                      № {offer.shop_number}
                    </span>
                  </td>
                  <td>
                    {offer.owner_name}
                    <div className={detailStyles.mobileExtra}>
                      {shopTypeLabel}{' '}
                      <span className={styles.searchShopLink} onClick={() => onShopClick?.(offer.shop_id)}>
                        № {offer.shop_number}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* "Предложений не найдено" — когда данные загружены, но пустые */}
      {displayData && allOffers.length === 0 && !isFetching && !error && (
        <div className={styles.searchItems}>
          Предложений не найдено
        </div>
      )}
    </div>
  );
}

export default ItemSearchView;