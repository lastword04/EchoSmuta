import { useState } from "react";
import { config } from "../../../shared/config/env/env";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import { 
  useGetCityShopByIdQuery, 
  useLazyGetItemBySlugQuery, 
  usePurchaseItemMutation 
} from "../../../entities/items/api/inventoryApi"; 
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import { formatRecipeDescription } from "../../../shared/lib/formatting/abilityParametersFormatter";
import { getLocationTexts } from '../config/locationTextConfig';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { formatLicenseTime } from '../utils/dateFormatter';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from "./ShopDetailView.module.css";
import btn from '../../../shared/styles/buttons.module.css';

const getRaceForElixir = (itemName) => {
  if (!itemName) return null;
  const orcElixirs = ['Эликсир Нечистая сила', 'Эликсир Укус Печелы', 'Эликсир Медвежья песня', 'Эликсир Трезвость', 'Эликсир Полная Луна', 'Эликсир Сила Действия', 'Эликсир Скорость Тигра', 'Эликсир Шепот Фортуны'];
  const elfElixirs = ['Эликсир Плач Неразумных', 'Эликсир Живая Вода', 'Эликсир Розовый Свет', 'Эликсир Легкий Путь', 'Эликсир Второе Дыхание', 'Эликсир Сила Духа', 'Эликсир Скорость Ястреба', 'Эликсир Танец Фортуны'];
  const humanElixirs = ['Эликсир Свирепый Воин', 'Эликсир Преследование', 'Эликсир Момент Истины', 'Эликсир Белый День', 'Эликсир Энергия', 'Эликсир Сила Разума', 'Эликсир Скорость Звука', 'Эликсир Улыбка Фортуны'];
  
  if (orcElixirs.includes(itemName)) return 'Орк';
  if (elfElixirs.includes(itemName)) return 'Эльф';
  if (humanElixirs.includes(itemName)) return 'Человек';
  return null;
};

function ShopDetailView({ shopId, locationSlug, character, onBack, initialShopData }) {  
  const locationConfig = getTradeLocationConfig(locationSlug);
  const texts = getLocationTexts(locationSlug);
  const showRaceColumn = locationSlug === '1.9.pharmacy';
  const { currentError, showError } = useErrorToast();   
  
  const [purchaseItem] = usePurchaseItemMutation();
  
  // ═══ RTK QUERY ═══
  // 1. Загрузка магазина
  const { 
    data: shopData, 
    isLoading, 
    error,     
  } = useGetCityShopByIdQuery(shopId, { 
    skip: !shopId && !initialShopData,
    refetchOnFocus: true,    
  });  

  // 2. Ленивая загрузка предмета (только по клику)
  const [triggerGetItemBySlug] = useLazyGetItemBySlugQuery();

  const [buyingId, setBuyingId] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);  
  

  // ═══ HANDLERS ═══
  const handleItemClick = async (saleItem) => {
    try {
      // Вызываем триггер и ждем результат
      const fullItem = await triggerGetItemBySlug(saleItem.item_slug).unwrap();
      setSelectedItem(adaptItemForCard({ ...fullItem, ...saleItem }));
    } catch (error) {
      console.error('Ошибка загрузки данных предмета:', error);
      setSelectedItem(adaptItemForCard(saleItem));
    }
  };

  const handlePurchase = async (item) => {
    if (buyingId) return;
    setBuyingId(item.inventory_item_id);
    try {
      await purchaseItem({ inventoryItemId: item.inventory_item_id, amount: 1, locationSlug }).unwrap();
      // refetch() НЕ НУЖЕН! Мутация purchaseItem теперь сама инвалидирует тег 'CityShop'
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = "Произошла ошибка при покупке";
      if (errorData?.error_code === "INSUFFICIENT_DUCATS_TO_BUY" || errorData?.error_code === "INSUFFICIENT_CHARACTER_DUCATS_FOR_CITY_TRADE_SHOP") {
        errorMessage = `Недостаточно средств. Требуется: ${errorData.extras?.required_ducats || '?'} дт.`;
      } else if (errorData?.error_code === "ITEM_NOT_FOR_SALE") {
        errorMessage = "Этот предмет больше не продаётся";
      } else if (errorData?.error_code === "CITY_TRADING_SHOP_LICENSE_EXPIRED") {
        errorMessage = "Лицензия магазина истекла";
      } else if (errorData?.error_code === "CHARACTER_NOT_IN_ITEM_LOCATION") {
        errorMessage = "Вы находитесь не в той локации";
      } else if (errorData?.error_code === "SHOP_CAPACITY_EXCEEDED") {
        errorMessage = "Превышена вместимость вашей лавки";
      } else if (errorData?.detail) {
        errorMessage = errorData.detail;
      }
      showError(errorMessage);
    } finally {
      setBuyingId(null);
    }
  };

  // ═══ GUARDS & COMPUTED ═══
  if (isLoading && !initialShopData) return null;
  if (error || (!shopData && !initialShopData)) {
    return <div className={styles.errorContainer}><div className={styles.errorText}>Магазин не найден</div></div>;
  }

  // initialShopData из списка — плоский объект (без обёртки shop), нормализуем
  // к форме ответа detail, пока запрос в полёте. sale_items списка содержат
  // те же поля, что detail — кадр из них полноценный.
  const currentShopData = shopData
    || (initialShopData?.shop ? initialShopData : {
        shop: initialShopData || {},
        sale_items: initialShopData?.sale_items || [],
        photo: initialShopData?.photo || null,
      });
  const shop = currentShopData.shop || {};
  const shopTypeName = locationConfig?.shopType || 'Лавка';
  const endLicense = shop.end_license ? parseUtcDate(shop.end_license) : null;
  const isOpen = !!endLicense && endLicense.getTime() > Date.now();
  const saleItems = isOpen ? (currentShopData.sale_items || []) : [];
  const shopPhotoUrl = currentShopData?.photo?.id
    ? `${config.FILE_API_BASE_URL}/${currentShopData.photo.id}/content?v=${currentShopData.photo.updated_at || currentShopData.shop?.updated_at || Date.now()}`
    : null;

  // ═══ RENDER ═══
  return (
    <div className={styles.shopDetailContainer}>
      <ErrorToast message={currentError} />
      <div className={styles.borderBox}>
        <div className={styles.topSection}>
          <div className={styles.photoContainer}>
            <img
              src={shopPhotoUrl || '/images/city-trade/no-image.png'}
              alt={shop.name}
              className={styles.shopPhoto}
              onError={(e) => { e.currentTarget.onerror = null; e.currentTarget.src = '/images/city-trade/no-image.png'; }}
            />
          </div>
          <div className={styles.infoWrap}>
            <div className={styles.nameBlock}>
              <div className={styles.shopName}>{shop.name}</div>
              {shop.description && <div className={styles.shopDescription}>{shop.description}</div>}
            </div>
            <div className={styles.metaBlock}>
              <div className={styles.metaRow}>Владелец <b>{shop.character_name}</b></div>
              <div className={styles.metaRow}>
                {shopTypeName} {isOpen ? <span className={styles.statusOpen}>Открыта</span> : <span className={styles.statusClosed}>Закрыта</span>}
              </div>
              <div className={styles.metaRow}>Номер {locationConfig?.shopTypeGenitive || 'лавки'} <b>{shop.number}</b></div>
              {onBack && <button className={`${btn.gameButton} ${btn.sizeSmall}`} onClick={onBack}>Выйти</button>}
            </div>
          </div>
        </div>
        
        {isOpen && saleItems.length > 0 && (
          <table className={`${styles.shopTable} ${styles.shopDetailTable} ${showRaceColumn ? styles.withRace : ''}`}>
            <colgroup><col />{showRaceColumn && <col />}<col /><col /><col /><col /></colgroup>
            <thead>
              <tr>
                <th>{texts.workshopNameColumn || 'Товар'}</th>
                {showRaceColumn && <th className={`${styles.colRace} ${styles.hideOnMobile}`}>Раса</th>}
                <th className={styles.hideOnMobile}>{texts.wearColumnLabel}</th>
                <th>Описание</th>
                <th>Цена</th>
                <th className={styles.hideOnMobile}></th>
              </tr>
            </thead>
            <tbody>
              {saleItems.map((item) => (
                <tr key={item.sale_id}>
                  <td>
                    <span className={btn.clickableItemName} onClick={() => handleItemClick(item)}>
                      {item.item_name}
                    </span>
                    {item.amount > 1 ? ` ${item.amount} шт.` : ''}
                    <div className={styles.mobileExtra}>
                      {(item.max_wear ?? item.parameters?.max_wear) != null
                        ? `Износ: ${item.wear ?? 0}/${item.max_wear ?? item.parameters?.max_wear}`
                        : `Срок: ${formatLicenseTime(item.expired_date)}`}
                    </div>
                    {showRaceColumn && <div className={styles.mobileExtra}>{getRaceForElixir(item.item_name)}</div>}
                  </td>
                  {showRaceColumn && <td className={`${styles.colRace} ${styles.hideOnMobile}`}>{getRaceForElixir(item.item_name) || '—'}</td>}
                  <td className={styles.hideOnMobile}>
                    {(item.max_wear ?? item.parameters?.max_wear) != null
                      ? `${item.wear ?? 0}/${item.max_wear ?? item.parameters?.max_wear}`
                      : formatLicenseTime(item.expired_date)}
                  </td>
                  <td>{formatRecipeDescription(item) || '—'}</td>
                  <td>
                    {Number(item.price).toFixed(2)} дт.
                    <div className={styles.mobileBuy}>
                      <button className={btn.textLinkDanger} disabled={buyingId === item.inventory_item_id} onClick={() => handlePurchase(item)}>Купить</button>
                    </div>
                  </td>
                  <td className={styles.hideOnMobile}>
                    <button className={btn.textLinkDanger} disabled={buyingId === item.inventory_item_id} onClick={() => handlePurchase(item)}>Купить</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}    
      </div>
      
      {selectedItem && (
        <div className={styles.itemCardOverlay} onClick={(e) => { if (e.target === e.currentTarget) setSelectedItem(null); }}>
          <ItemInfoCard item={selectedItem} onClose={() => setSelectedItem(null)} character={character} />
        </div>
      )}
    </div>
  );
}

export default ShopDetailView;