import { useState, useEffect, useMemo, useCallback } from 'react';
import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';
import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { useSellResourcesBulkMutation, useBuyResourcesBulkMutation } from '../../../entities/economy/api/economyApi';
import { resourceIcon, DEFAULT_RESOURCE_ICON } from '../../../shared/config/ui/resourceIcons';
import { CATEGORY_LABELS, sortCategories } from '../config';
import styles from './BuyoutTab.module.css';
import btn from '../../../shared/styles/buttons.module.css';
import { intInputHandler } from '../../../shared/lib/validation/numberInput';

const BuyoutTab = ({ resources, onRefresh, onShopDataRefresh }) => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [mode, setMode] = useState('sell');
  const [quantities, setQuantities] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshingMode, setIsRefreshingMode] = useState(false); 
  const { currentError, showError } = useErrorToast();  
  const [sellBulk] = useSellResourcesBulkMutation();
  const [buyBulk] = useBuyResourcesBulkMutation();   

  const categories = useMemo(() => {
    const present = [...new Set(resources.map(r => r.category).filter(Boolean))];
    return sortCategories(present);
  }, [resources]);

  const handleModeClick = useCallback((newMode) => {
    if (newMode === mode) {
      // Клик на активную вкладку → рефетч с троттлингом
      if (isRefreshingMode) return;
      setIsRefreshingMode(true);
      onShopDataRefresh?.();
      setTimeout(() => setIsRefreshingMode(false), 300);
      return;
    }
    setMode(newMode);
  }, [mode, isRefreshingMode, onShopDataRefresh]);

  const activeCategory =
    selectedCategory && categories.includes(selectedCategory)
      ? selectedCategory
      : categories[0] || '';

  useEffect(() => { setQuantities({}); }, [activeCategory, mode]);

  const filteredResources = useMemo(() => resources.filter(r => r.category === activeCategory), [resources, activeCategory]);  

  const executeAction = async () => {
    if (isLoading) return;
    
    const items = Object.entries(quantities)
      .map(([id, qty]) => ({ resource_id: id, quantity: Number(qty) }))
      .filter(item => item.quantity > 0);
    
    if (items.length === 0) { 
      showError('Введите количество хотя бы для одного ресурса'); 
      return; 
    }
    
    setIsLoading(true);
    try {
      // ОДИН bulk-запрос для обоих режимов
      if (mode === 'buy') {
        await buyBulk(items).unwrap();
      } else {
        await sellBulk(items).unwrap();
      }
      
      setQuantities({});      
      if (onRefresh) await onRefresh();
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = 'Произошла ошибка';
      if (errorData?.detail) {
        errorMessage = errorData.detail;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const executeAll = async () => {
    if (isLoading || mode !== 'sell') return;
    
    const items = filteredResources
      .map(resource => {
        const qty = resource.player_quantity;
        if (!qty || qty <= 0) return null;
        return { resource_id: resource.id, quantity: qty };
      })
      .filter(Boolean);
    
    if (items.length === 0) {
      showError('Нечего продавать');
      return;
    }
    
    setIsLoading(true);
    try {
      await sellBulk(items).unwrap();
      setQuantities({});      
      if (onRefresh) await onRefresh();
    } catch (error) {
      const errorData = error?.data;
      let errorMessage = 'Произошла ошибка';
      if (errorData?.detail) {
        errorMessage = errorData.detail;
      } else if (error?.message) {
        errorMessage = error.message;
      }
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const changeQuantity = (id, value) => setQuantities(prev => ({ ...prev, [id]: value }));


  // Определяем, является ли текущая категория "Озером" (рыбой)
  const isLakeCategory = activeCategory === 'lake';
  const resourceColClass = isLakeCategory ? styles.colResourceWide : styles.colResource;

  return (
    <div className={styles.mainContainer}>
      {/* ГЛАВНЫЕ ТАБЫ — Режим (Продажа/Покупка) */}
      <div className={styles.modeTabs}>
        <button 
          className={`${btn.gameButton} ${btn.sizeLarge} ${mode === 'sell' ? btn.gameButtonActive : ''}`}
          onClick={() => handleModeClick('sell')}
          disabled={isRefreshingMode}
        >
          Продажа
        </button>
        <button 
          className={`${btn.gameButton} ${btn.sizeLarge} ${mode === 'buy' ? btn.gameButtonActive : ''}`}
          onClick={() => handleModeClick('buy')}
          disabled={isRefreshingMode}
        >
          Покупка
        </button>
      </div>

      {/* ПОДЧИНЕННЫЕ ТАБЫ — Категории (в плашке) */}
      <div className={styles.categoryTabs}>
        {categories.map((category) => (
          <button
            key={category}
            className={`${styles.categoryChip} ${activeCategory === category ? styles.categoryChipActive : ''}`}
            onClick={() => setSelectedCategory(category)}
          >
            {CATEGORY_LABELS[category] || category}
          </button>
        ))}
      </div>

      {/* КОНТЕНТ */}
      <div className={styles.container}>
        <ErrorToast message={currentError} />
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={resourceColClass}>Ресурс</th>
              <th className={styles.colShopAmount}>В скупке</th>
              <th className={`${styles.colPlayerAmount} ${styles.hideOnMobile}`}>У вас</th>
              <th className={styles.colPrice}>Цена</th>
              <th className={`${styles.colQty} ${styles.hideOnMobile}`}>Кол-во</th>
            </tr>
          </thead>
          <tbody>
            {filteredResources.map(resource => {
              const qtyInput = (
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  className={styles.inputQty}
                  value={quantities[resource.id] || ''}
                  onChange={intInputHandler(v => changeQuantity(resource.id, v), 7, { strip: true })}             
                />
              );

              return (
                <tr key={resource.id}>
                  {/* td — обычная ячейка, flex теперь внутри */}
                  <td className={resourceColClass}>
                    <div className={styles.resourceCell}>
                      <img
                        src={resourceIcon(resource.code)}
                        alt={resource.name}
                        className={`${styles.resourceIcon} ${isLakeCategory ? styles.resourceIconWide : ''}`}
                        onError={e => { e.target.onerror = null; e.target.src = DEFAULT_RESOURCE_ICON; }}
                      />
                      <span>{resource.name}</span>
                    </div>
                  </td>

                  <td className={styles.stock}>
                    {resource.buyout_stock_quantity}
                    <div className={styles.mobileExtra}>У вас: {resource.player_quantity || 0}</div>
                  </td>

                  <td className={`${styles.playerQty} ${styles.hideOnMobile}`}>{resource.player_quantity || 0}</td>

                  <td className={styles.price}>
                    {mode === 'buy' ? resource.sell_price : resource.buy_price}
                    <div className={styles.mobileQty}>{qtyInput}</div>
                  </td>

                  <td className={styles.hideOnMobile}>{qtyInput}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
       
      </div>
      <div className={styles.actionButtons}>
        <button 
          className={`${btn.simpleButton} ${btn.simpleButtonGold}`}
          onClick={executeAction}
          disabled={isLoading}
        >
          {mode === 'buy' ? 'Купить' : 'Продать'}
        </button>
        {mode === 'sell' && (
          <button 
            className={`${btn.simpleButton} ${btn.simpleButtonGold}`}
            onClick={executeAll}
            disabled={isLoading}
          >
            Продать всё
          </button>
        )}
      </div>
    </div>
  );
};

export default BuyoutTab;