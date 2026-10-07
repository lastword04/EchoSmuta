// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                         ИМПОРТЫ                                   ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useErrorToast } from "../../../shared/hooks/ui/useErrorToast";
import ErrorToast from "../../../shared/ui/ErrorToast/ErrorToast";
import { getErrorMessage } from '../../../shared/lib/error/getErrorMessage';
import {
  useGetItemsFromLocationQuery,
  useListItemToShopMutation,
  useWithdrawItemFromShopMutation,
  usePutItemOnSaleMutation,
  useRemoveItemFromSaleMutation,
  useUpdateSalePriceMutation,
} from "../../../entities/items/api/inventoryApi";
import { getTradeLocationConfig } from "../../../shared/config/locations/tradeConfig";
import { getLocationTexts } from '../config/locationTextConfig';
import PriceModal from "./PriceModal";
import { getMinAllowedPrice } from '../../../shared/config/trade/priceConfig';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { adaptItemForCard } from '../../../entities/items/ui/ItemInfoCard/adaptItemForCard';
import { parseUtcDate } from '../../../shared/lib/utils/utcDate';
import styles from "./MyShopView.module.css";
import btn from '../../../shared/styles/buttons.module.css';
import { formatLicenseTime, formatWear } from '../utils/dateFormatter';

// ═══════════════════════════════════════════════════════════════════════
// ╔═══════════════════════════════════════════════════════════════════╗
// ║                        КОМПОНЕНТ                                  ║
// ╚═══════════════════════════════════════════════════════════════════╝
// ═══════════════════════════════════════════════════════════════════════

function MyShopView({ locationSlug, character }) {
  
  // ── Redux & hooks ──  
  const locationConfig = getTradeLocationConfig(locationSlug);
  const texts = getLocationTexts(locationSlug);
  const { currentError, showError, hideError } = useErrorToast();
  const lastDataRef = useRef(null);

  // ── State ──
  const [priceModal, setPriceModal] = useState({
    isOpen: false,
    mode: null, // 'sale' | 'edit'
    item: null,
    price: "",
    amount: 1,
  });
  const [selectedItem, setSelectedItem] = useState(null);
  const [busyItemId, setBusyItemId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  

    // ── Data fetching ──
  const { data: itemsData } = useGetItemsFromLocationQuery(locationSlug, {
    refetchOnFocus: true,    
  });
  const [listItemToShop] = useListItemToShopMutation();
  const [withdrawItemFromShop] = useWithdrawItemFromShopMutation();
  const [putItemOnSale] = usePutItemOnSaleMutation();
  const [removeItemFromSale] = useRemoveItemFromSaleMutation();
  const [updateSalePrice] = useUpdateSalePriceMutation();

  // ═══ lastDataRef паттерн (защита от мелькания) ═══
  if (itemsData !== undefined && itemsData !== null) {
    lastDataRef.current = itemsData;
  }
  const displayItemsData = itemsData !== undefined ? itemsData : lastDataRef.current;

  // ── Computed ──
  const isLicenseExpired = useMemo(() => {
    if (!displayItemsData) return true;
    
    if (!locationConfig?.isProduction) {
      const endLicense = displayItemsData.shop_end_license;
      return !endLicense || parseUtcDate(endLicense) < Date.now();
    }
    return displayItemsData.crafting_license_active !== true;
  }, [displayItemsData, locationConfig]);

  // ── Effects ──


  useEffect(() => {
    hideError();
    setPriceModal({ isOpen: false, mode: null, item: null, price: "", amount: 1 });
  }, [locationSlug, hideError]);

  

  // ── Handlers ──
  const formatSecondColumn = useCallback((item) => {
    if (texts.wearColumnLabel === 'Износ') return formatWear(item);
    return formatLicenseTime(item.expired_date);
  }, [texts.wearColumnLabel]);

  const assertMinPrice = useCallback((basePrice, price) => {
    const min = getMinAllowedPrice(basePrice);
    if (min > 0 && price < min) {
      showError(`Нельзя продать предмет ниже половины его базовой стоимости (мин. ${min.toFixed(2)} дт.)`);
      return false;
    }
    return true;
  }, [showError]);

  const handleMoveToShop = useCallback(async (itemId, amount = 1) => {
    if (busyItemId !== null) return;
    setBusyItemId(itemId);
    try {
      await listItemToShop({ itemId, amount }).unwrap();
      
    } catch (error) {
      const isNotFound = error?.status === 404 ||
        String(error?.data?.detail || "").includes("Unable to find the InventoryItem");
      if (isNotFound) {
        showError("Предмет уже перемещен");
        
      } else {
        showError(getErrorMessage(error, "Произошла ошибка при перемещении предмета"));
      }
    } finally {
      setBusyItemId(null);
    }
  }, [busyItemId, listItemToShop, showError]);

  const handleWithdrawFromShop = useCallback(async (itemId, amount = 1) => {
    if (busyItemId !== null) return;
    setBusyItemId(itemId);
    try {
      await withdrawItemFromShop({ itemId, amount }).unwrap();
      
    } catch (error) {
      const isNotFound = error?.status === 404 ||
        String(error?.data?.detail || "").includes("Unable to find the InventoryItem");
      if (isNotFound) {
        showError("Предмет уже изъят");
       
      } else {
        showError(getErrorMessage(error, "Произошла ошибка при изъятии предмета"));
      }
    } finally {
      setBusyItemId(null);
    }
  }, [busyItemId, withdrawItemFromShop, showError]);

  const handleRemoveFromSale = useCallback(async (inventoryItemId, amount = null) => {
    if (busyItemId !== null) return;
    setBusyItemId(inventoryItemId);
    try {
      await removeItemFromSale({ inventoryItemId, amount }).unwrap();
      
    } catch (error) {
      const isNotFound = error?.status === 404 ||
        String(error?.data?.detail || "").includes("Unable to find the InventoryItem");
      if (isNotFound) {
        showError("Предмет уже снят с продажи");
        
      } else {
        showError(getErrorMessage(error, "Произошла ошибка при снятии с продажи"));
      }
    } finally {
      setBusyItemId(null);
    }
  }, [busyItemId, removeItemFromSale, showError]);

  const handlePutOnSale = useCallback((item) => {
    setPriceModal({
      isOpen: true,
      mode: 'sale',
      item,
      price: "",
      amount: item.amount ?? 1,
    });
  }, []);

  const handleConfirmSale = useCallback(async () => {
    if (isSubmitting) return;
    const price = parseFloat(priceModal.price);
    if (!assertMinPrice(priceModal.item.item_price ?? priceModal.item.price ?? 0, price)) return;
    if (!priceModal.price || isNaN(price) || price <= 0) {
      showError("Введите корректную цену");
      return;
    }
    setIsSubmitting(true);
    try {
      await putItemOnSale({
        inventoryItemId: priceModal.item.id,
        price,
        amount: priceModal.amount,
      }).unwrap();
      setPriceModal({ isOpen: false, mode: null, item: null, price: "", amount: 1 });
    } catch (error) {
      showError(getErrorMessage(error, "Произошла ошибка при выставлении на продажу"));
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, priceModal, assertMinPrice, putItemOnSale, showError]);

  const handleCancelSale = useCallback(() => {
    setPriceModal({ isOpen: false, mode: null, item: null, price: "", amount: 1 });
  }, []);

  const handleEditPrice = useCallback((saleItem) => {
    setPriceModal({
      isOpen: true,
      mode: 'edit',
      item: saleItem,
      price: String(saleItem.price),
      amount: 1,
    });
  }, []);

  const handleConfirmEditPrice = useCallback(async () => {
    if (isSubmitting) return;
    const price = parseFloat(priceModal.price);
    if (!assertMinPrice(priceModal.item.item_price ?? priceModal.item.price ?? 0, price)) return;
    if (!priceModal.price || isNaN(price) || price <= 0) {
      showError("Введите корректную цену");
      return;
    }
    setIsSubmitting(true);
    try {
      await updateSalePrice({
        inventoryItemId: priceModal.item.inventory_item_id,
        price,
      }).unwrap();
      setPriceModal({ isOpen: false, mode: null, item: null, price: "", amount: 1 });
    } catch (error) {
      showError(getErrorMessage(error, "Произошла ошибка при изменении цены"));
    } finally {
      setIsSubmitting(false);
    }
  }, [isSubmitting, priceModal, assertMinPrice, updateSalePrice, showError]);

  const handleCancelEditPrice = useCallback(() => {
    setPriceModal({ isOpen: false, mode: null, item: null, price: "", amount: 1 });
  }, []);

  const handleItemClick = useCallback((item) => {
    setSelectedItem(adaptItemForCard(item));
  }, []);

  // ── Guards ──
  if (!displayItemsData) return null;

  const characterItems = displayItemsData.character_items || [];
  const shopItems = displayItemsData.shop_items || [];
  const saleItems = displayItemsData.sale_items || [];

  // ═══════════════════════════════════════════════════════════════════
  // ║                          РЕНДЕР                                   ║
  // ╚══════════════════════════════════════════════════════════════════╝

  return (
    <div className={styles.myShopContainer}>
      <ErrorToast message={currentError} />
      <div className={styles.tables}>
        {/* Левая таблица — Инвентарь персонажа */}
        <div className={styles.borderBox}>
          <table className={styles.shopTable}>
            <colgroup>
              <col className={styles.colLeftName} />
              <col className={styles.colLeftWear} />
              <col className={styles.colLeftAction} />
            </colgroup>
            <thead>
              <tr>
                <th>{locationConfig?.inventoryTitle || "Предметы в рюкзаке"}</th>
                <th className={styles.hideOnMobile}>{texts.wearColumnLabel}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {characterItems.length > 0 ? (
                characterItems.map(item => (
                  <tr key={item.id} className={styles.tableRow}>
                    <td>
                      <span className={btn.clickableItemName} onClick={() => handleItemClick(item)}>
                        {item.item_name}
                      </span>
                      {item.amount > 1 && (
                        <span className={styles.clickableAmount}
                          onClick={(e) => { e.stopPropagation(); handleMoveToShop(item.id, item.amount); }}
                          title={`Переместить все в ${texts.shopTypeName}`}>
                          {' '}{item.amount} шт.
                        </span>
                      )}
                      <div className={styles.mobileExtra}>
                        {formatSecondColumn(item)}
                      </div>
                    </td>
                    <td className={styles.hideOnMobile}>{formatSecondColumn(item)}</td>
                    <td>
                      <div className={styles.actionsCell}>
                        <button className={btn.textLinkDanger} disabled={busyItemId === item.id} onClick={() => handleMoveToShop(item.id, 1)}>
                          {texts.moveToShopButton}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="3" className={styles.noItems}>Нет предметов в рюкзаке</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Правая таблица — Лавка */}
        <div className={styles.borderBox}>
          <table className={styles.shopTable}>
            <colgroup>
              <col className={styles.colRightName} />
              <col className={styles.colRightWear} />
              <col className={styles.colRightAction} />
            </colgroup>
            <thead>
              <tr>
                <th>{locationConfig?.shopInventoryTitle || "Лавка"}</th>
                <th className={styles.hideOnMobile}>{texts.wearColumnLabel}</th>
                <th className={styles.columnHeader}>
                  {displayItemsData?.max_capacity > 0 ? `${displayItemsData.current_capacity} / ${displayItemsData.max_capacity}` : ''}
                </th>
              </tr>
            </thead>
            <tbody>
              {shopItems.length > 0 ? (
                shopItems.map(item => (
                  <tr key={item.id} className={styles.tableRow}>
                    <td>
                      <span className={btn.clickableItemName} onClick={() => handleItemClick(item)}>
                        {item.item_name}
                      </span>
                      {item.amount > 1 && (
                        <span className={styles.clickableAmount}
                          onClick={(e) => { e.stopPropagation(); handleWithdrawFromShop(item.id, item.amount); }}
                          title="Забрать все в рюкзак">
                          {' '}{item.amount} шт.
                        </span>
                      )}
                      <div className={styles.mobileExtra}>
                        {formatSecondColumn(item)}
                      </div>
                    </td>
                    <td className={styles.hideOnMobile}>{formatSecondColumn(item)}</td>
                    <td>
                      <div className={styles.actionsCell}>
                        <button 
                          className={btn.textLinkDanger} 
                          disabled={isLicenseExpired}
                          onClick={() => handlePutOnSale(item)}
                          title={isLicenseExpired ? "Продлите лицензию, чтобы выставлять товары" : ""}
                        >
                          {texts.sellButton}
                        </button>
                        <button className={`${btn.textLinkDanger} ${styles.hideOnMobile}`} disabled={busyItemId === item.id} onClick={() => handleWithdrawFromShop(item.id, 1)}>
                          {texts.withdrawButton}
                        </button>
                        <div className={styles.mobileWithdraw}>
                          <button className={btn.textLinkDanger} disabled={busyItemId === item.id} onClick={() => handleWithdrawFromShop(item.id, 1)}>
                            {texts.withdrawButton}
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan="3" className={styles.noItems}>{texts.emptyShopText}</td></tr>
              )}
            </tbody>
          </table>

          {saleItems.length > 0 && (
            <table className={`${styles.shopTable} ${styles.saleTable}`}>
              <colgroup>
                <col className={styles.colRightName} />
                <col className={styles.colRightWear} />
                <col className={styles.colRightAction} />
              </colgroup>
              <thead>
                <tr>
                  <th>{texts.onSaleTitle}</th>
                  <th className={styles.hideOnMobile}>{texts.wearColumnLabel}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {saleItems.map(item => (
                  <tr key={item.id} className={styles.tableRow}>
                    <td>
                      <span className={btn.clickableItemName} onClick={() => handleItemClick(item)}>
                        {item.item_name}
                      </span>
                      {item.amount > 1 && (
                        <span className={styles.clickableAmount}
                          onClick={(e) => { e.stopPropagation(); handleRemoveFromSale(item.inventory_item_id); }}
                          title="Снять все с продажи">
                          {' '}{item.amount} шт.
                        </span>
                      )}
                      <div className={styles.mobileExtra}>
                        {formatSecondColumn(item)}
                      </div>
                    </td>
                    <td className={styles.hideOnMobile}>{formatSecondColumn(item)}</td>
                    <td>
                      <div className={styles.actionsCell}>
                        <button 
                          className={`${btn.textLinkDanger} ${isLicenseExpired ? styles.disabledBtn : ''}`}
                          onClick={() => handleEditPrice(item)} 
                          title={isLicenseExpired ? "Продлите лицензию, чтобы изменять цены" : "Изменить цену"}
                          disabled={isLicenseExpired}                          
                        >
                          {Number(item.price).toFixed(2)} дт.
                        </button>
                        <button className={`${btn.textLinkDanger} ${styles.hideOnMobile}`} disabled={busyItemId === item.inventory_item_id} onClick={() => handleRemoveFromSale(item.inventory_item_id, 1)}>
                          {texts.withdrawButton}
                        </button>
                        <div className={styles.mobileWithdraw}>
                          <button className={btn.textLinkDanger} disabled={busyItemId === item.inventory_item_id} onClick={() => handleRemoveFromSale(item.inventory_item_id, 1)}>
                            {texts.withdrawButton}
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {priceModal.isOpen && priceModal.item && (
        <PriceModal
          mode={priceModal.mode}
          title={priceModal.mode === 'sale' ? "Продажа" : "Изменение цены"}
          item={priceModal.item}
          amount={priceModal.amount}
          onChangeAmount={(newAmount) => setPriceModal(prev => ({ ...prev, amount: newAmount }))}
          priceLabel={priceModal.mode === 'sale' ? "Цена за 1 шт." : "Новая цена за 1 шт."}
          confirmLabel={priceModal.mode === 'sale' ? texts.sellButton : "Изменить"}
          cancelLabel={texts.cancelButton || "Отмена"}
          price={priceModal.price}
          onChangePrice={(newPrice) => setPriceModal(prev => ({ ...prev, price: newPrice }))}
          onConfirm={priceModal.mode === 'sale' ? handleConfirmSale : handleConfirmEditPrice}
          onCancel={priceModal.mode === 'sale' ? handleCancelSale : handleCancelEditPrice}
          locationSlug={locationSlug}
          isSubmitting={isSubmitting}
        />
      )}

      {selectedItem && (
        <div
          className={styles.itemCardOverlay}
          onClick={(e) => {
            if (e.target === e.currentTarget) setSelectedItem(null);
          }}
        >
          <ItemInfoCard
            item={selectedItem}
            onClose={() => setSelectedItem(null)}
            character={character}
          />
        </div>
      )}
    </div>
  );
}

export default MyShopView;