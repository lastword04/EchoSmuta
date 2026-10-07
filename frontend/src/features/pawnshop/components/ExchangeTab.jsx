import { useState, useMemo, useCallback } from 'react';
import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';
import ErrorToast from '../../../shared/ui/ErrorToast/ErrorToast';
import { 
  useCreateLotMutation, 
  useDealLotMutation, 
  useCancelLotMutation,  
} from '../../../entities/economy/api/economyApi';
import { CATEGORY_LABELS, sortCategories } from '../config';
import { getErrorMessage } from '../../../shared/lib/error/getErrorMessage';
import styles from './ExchangeTab.module.css';
import btn from '../../../shared/styles/buttons.module.css';
import { intInputHandler, decimalInputHandler } from '../../../shared/lib/validation/numberInput';

const MAX_LOT_ITEMS = 5;

const ExchangeTab = ({ onRefresh, onShopDataRefresh, characterId, resources, lots }) => { 
  const [activeTab, setActiveTab] = useState('market');
  const [isRefreshingTab, setIsRefreshingTab] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [lotType, setLotType] = useState('SELL');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedResourceId, setSelectedResourceId] = useState('');
  const [basket, setBasket] = useState([]);
  const [bundlePrice, setBundlePrice] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [busyLotId, setBusyLotId] = useState(null);
  const { currentError, showError } = useErrorToast();
  const [createLot] = useCreateLotMutation();
  const [dealLot] = useDealLotMutation();
  const [cancelLot] = useCancelLotMutation();

  const resourceMap = useMemo(() => resources.reduce((acc, r) => { acc[r.id] = r; return acc; }, {}), [resources]);

  const categories = useMemo(() => {
    const present = [...new Set(resources.map(r => r.category).filter(Boolean))];
    return sortCategories(present);
  }, [resources]);

  const categoryResources = useMemo(() => resources.filter(r => r.category === selectedCategory), [resources, selectedCategory]);
  
  const filteredLots = useMemo(() => {
    if (filterType === 'all') return lots;
    return lots.filter(lot => lot.lot_type === filterType);
  }, [lots, filterType]);

  const sellLots = useMemo(() => filteredLots.filter(l => l.lot_type === 'SELL'), [filteredLots]);
  const buyLots = useMemo(() => filteredLots.filter(l => l.lot_type === 'BUY'), [filteredLots]);

  // Живое вычисление минимальной цены лота
  const minLotPrice = useMemo(() => {
    const validItems = basket.filter(i => Number(i.quantity) > 0);
    if (validItems.length === 0) return 0;
    const total = validItems.reduce((sum, item) => {
      const res = resources.find(r => r.id === item.id);
      return sum + Number(item.quantity) * (res?.price ?? 1);
    }, 0);
    return total * 0.5;
  }, [basket, resources]);

  const handleAddToBasket = () => {
    if (isCreating) return;
    const resource = resources.find(r => r.id === selectedResourceId);
    if (!resource) return;
    if (basket.length >= MAX_LOT_ITEMS) { showError(`Максимум ${MAX_LOT_ITEMS} ресурсов в одном лоте`); return; }
    if (basket.some(item => item.id === resource.id)) { showError('Этот ресурс уже добавлен в корзину'); return; }
    setBasket(prev => [...prev, { id: resource.id, name: resource.name, icon_url: resource.icon_url, quantity: '1' }]);
    setSelectedResourceId('');
  };

  const updateBasketItem = (id, field, value) => setBasket(prev => prev.map(item => item.id === id ? { ...item, [field]: value } : item));
  const removeBasketItem = id => { if (isCreating) return; setBasket(prev => prev.filter(item => item.id !== id)); };

  const canSubmit = !isCreating && basket.length > 0 && basket.some(item => Number(item.quantity) > 0) && Number(bundlePrice) > 0;

  const handleTabClick = useCallback((newTab) => {
    if (newTab === activeTab) {
      // Клик на активную вкладку → рефетч с троттлингом
      if (isRefreshingTab) return;
      setIsRefreshingTab(true);
      if (newTab === 'market') {
        onShopDataRefresh?.();
      }
      setTimeout(() => setIsRefreshingTab(false), 300);
      return;
    }
    if (newTab === 'create') {
      setActiveTab('create');
      resetCreateForm();
    } else {
      setActiveTab(newTab);
    }
  }, [activeTab, isRefreshingTab, onShopDataRefresh]);

  const handleCreate = async (e) => {
    e.preventDefault();
    const emptyItems = basket.filter(item => item.quantity === '' || Number(item.quantity) <= 0);
    if (emptyItems.length > 0) {
      showError('Заполните количество всех ресурсов в корзине');
      return;
    }
    if (isCreating) return;
    const validItems = basket.filter(item => Number(item.quantity) > 0);
    if (validItems.length === 0) { showError('Заполни количество хотя бы у одного ресурса'); return; }
    if (validItems.length > MAX_LOT_ITEMS) { showError(`Максимум ${MAX_LOT_ITEMS} ресурсов в одном лоте`); return; }
    if (Number(bundlePrice) <= 0) { showError('Введи цену лота'); return; }

    if (lotType === 'SELL') {
      const insufficient = validItems.filter(item => {
        const resource = resources.find(r => r.id === item.id);
        return !resource || resource.player_quantity < Number(item.quantity);
      });
      if (insufficient.length > 0) {
        const names = insufficient.map(item => {
          const resource = resources.find(r => r.id === item.id);
          return resource ? resource.name : '?';
        }).join(', ');
        showError(`Недостаточно ресурсов: ${names}`);
        return;
      }
    }

    if (Number(bundlePrice) < minLotPrice) {
      showError(`Цена лота слишком низкая. Минимум: ${minLotPrice.toFixed(2)} дт.`);
      return;
    }

    setIsCreating(true);
    try {
      await createLot({
        lot_type: lotType,
        price: Number(bundlePrice),
        items: validItems.map(item => ({ resource_id: item.id, quantity: Number(item.quantity) })),
      }).unwrap();
      setBasket([]);
      setBundlePrice('');      
      if (onRefresh) await onRefresh();
    } catch (error) {
      showError(getErrorMessage(error, 'Не удалось создать лот'));
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeal = async (lot) => {
    if (busyLotId !== null) return;
    setBusyLotId(lot.id);
    try {
      await dealLot({ lotId: lot.id }).unwrap();      
      if (onRefresh) await onRefresh();
    } catch (error) {
      const detail = error?.data?.detail || error?.message || '';
      const status = error?.status;
      
      if (detail.includes('already closed') || detail.includes('closed') || detail.includes('заверш')) {
        showError('Лот уже завершён. Обновите список.');
      } else if (detail.includes('пересоздать лот') || detail.includes('устаревш')) {
        showError(detail);
      } else if (detail.includes('слишком низкая') || detail.includes('Минимум')) {
        showError(detail);
      } else if (detail.includes('Недостаточно') || detail.includes('Insufficient') || detail.includes('insufficient')) {
        showError(detail);
      } else if (status === 404 || detail.includes('not found')) {
        showError('Лот больше не существует.');
      } else if (status === 403) {
        showError('У вас нет прав на эту операцию.');
      } else {
        showError(getErrorMessage(error, 'Не удалось совершить сделку'));
      }
      
      if (status === 409 || status === 404) {
        if (onShopDataRefresh) await onShopDataRefresh();
      }
    } finally {
      setBusyLotId(null);
    }
  };

  const handleCancel = async (lotId) => {
    if (busyLotId !== null) return;
    setBusyLotId(lotId);
    try {
      await cancelLot(lotId).unwrap();      
      if (onRefresh) await onRefresh();
    } catch (error) {
      const detail = error?.data?.detail || error?.message || '';
      const status = error?.status;
      
      if (detail.includes('already closed') || detail.includes('closed') || detail.includes('заверш')) {
        showError('Лот уже завершён или отменён. Обновите список.');
      } else if (detail.includes('Not found') || detail.includes('not found') || status === 404) {
        showError('Лот больше не существует.');
      } else if (detail.includes('Only owner') || status === 403) {
        showError('У вас нет прав отменить этот лот.');
      } else {
        showError(getErrorMessage(error, 'Не удалось отменить лот'));
      }
      
      if (status === 409 || status === 404) {
        if (onShopDataRefresh) await onShopDataRefresh();
      }
    } finally {
      setBusyLotId(null);
    }
  };

  const resetCreateForm = () => {
    setBasket([]);
    setBundlePrice('');
    setSelectedCategory('');
    setSelectedResourceId('');
    setLotType('SELL');
  };

  

  return (
    <div className={styles.container}>
      <ErrorToast message={currentError} />

      {/* ОСНОВНЫЕ ТАБЫ */}
      <div className={styles.mainTabs}>
        <button
          className={`${btn.gameButton} ${btn.sizeLarge} ${activeTab === 'market' ? btn.gameButtonActive : ''}`}
          onClick={() => handleTabClick('market')}
          disabled={isRefreshingTab}
        >
          Биржа
        </button>
        <button
          className={`${btn.gameButton} ${btn.sizeLarge} ${activeTab === 'create' ? btn.gameButtonActive : ''}`}
          onClick={() => handleTabClick('create')}
          disabled={isRefreshingTab}
        >
          Создать лот
        </button>
      </div>

      {/* ТАБ: БИРЖА */}
      {activeTab === 'market' && (
        <>
          {/* Фильтры-чипсы */}
          <div className={styles.filterPills}>
            <button
              className={`${styles.filterChip} ${filterType === 'all' ? styles.filterChipActive : ''}`}
              onClick={() => setFilterType('all')}
            >
              Все лоты
            </button>
            <button
              className={`${styles.filterChip} ${filterType === 'SELL' ? styles.filterChipActive : ''}`}
              onClick={() => setFilterType('SELL')}
            >
              Продажа
            </button>
            <button
              className={`${styles.filterChip} ${filterType === 'BUY' ? styles.filterChipActive : ''}`}
              onClick={() => setFilterType('BUY')}
            >
              Покупка
            </button>
          </div>

          {/* Лоты */}
          {filteredLots.length === 0 ? (
            <div className={styles.emptyState}>
              <p className={styles.emptyMessage}>
                {filterType === 'all' 
                  ? 'На бирже пока нет активных лотов'
                  : filterType === 'SELL' 
                    ? 'Нет лотов на продажу'
                    : 'Нет лотов на покупку'
                }
              </p>
            </div>
          ) : (
            <div className={styles.lotsContainer}>
              {(filterType === 'all' || filterType === 'SELL') && sellLots.length > 0 && (
                <div className={styles.lotSection}>
                  <div className={styles.sectionHeader}>
                    <h3 className={styles.sectionTitle}>Лоты на продажу</h3>
                    <span className={styles.sectionCount}>{sellLots.length}</span>
                  </div>
                  <div className={styles.lotsGrid}>
                    {sellLots.map(lot => (
                      <LotCard
                        key={lot.id}
                        lot={lot}
                        isMyLot={lot.owner_character_id === characterId}
                        resourceMap={resourceMap}
                        busyLotId={busyLotId}
                        onDeal={handleDeal}
                        onCancel={handleCancel}
                        mode="sell"
                      />
                    ))}
                  </div>
                </div>
              )}

              {(filterType === 'all' || filterType === 'BUY') && buyLots.length > 0 && (
                <div className={styles.lotSection}>
                  <div className={styles.sectionHeader}>
                    <h3 className={styles.sectionTitle}>Лоты на покупку</h3>
                    <span className={styles.sectionCount}>{buyLots.length}</span>
                  </div>
                  <div className={styles.lotsGrid}>
                    {buyLots.map(lot => (
                      <LotCard
                        key={lot.id}
                        lot={lot}
                        isMyLot={lot.owner_character_id === characterId}
                        resourceMap={resourceMap}
                        busyLotId={busyLotId}
                        onDeal={handleDeal}
                        onCancel={handleCancel}
                        mode="buy"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ТАБ: СОЗДАТЬ ЛОТ */}
      {activeTab === 'create' && (
        <div className={styles.createLotCard}>
          <form className={styles.createForm} onSubmit={handleCreate}>
            <div className={styles.formGroup}>              
              <div className={styles.typeToggle}>
                <button
                  type="button"
                  className={`${btn.gameButton} ${lotType === 'SELL' ? `${btn.gameButtonActive} ${btn.colorDanger}` : ''}`}
                  onClick={() => setLotType('SELL')}
                  disabled={isCreating}
                >
                  Продать
                </button>
                <button
                  type="button"
                  className={`${btn.gameButton} ${lotType === 'BUY' ? `${btn.gameButtonActive} ${btn.colorSuccess}` : ''}`}
                  onClick={() => setLotType('BUY')}
                  disabled={isCreating}
                >
                  Купить
                </button>
              </div>
            </div>

            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Категория</label>
                <select
                  value={selectedCategory}
                  onChange={e => { setSelectedCategory(e.target.value); setSelectedResourceId(''); }}
                  disabled={isCreating}
                >
                  <option value="">Выберите категорию...</option>
                  {categories.map(cat => <option key={cat} value={cat}>{CATEGORY_LABELS[cat] || cat}</option>)}
                </select>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Ресурс</label>
                <select
                  value={selectedResourceId}
                  onChange={e => setSelectedResourceId(e.target.value)}
                  disabled={!selectedCategory || isCreating}
                >
                  <option value="">Выберите ресурс...</option>
                  {categoryResources.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
                </select>
              </div>
              <button
                type="button"
                className={`${btn.gameButton} ${btn.sizeLarge} ${styles.addButton}`}
                onClick={handleAddToBasket}
                disabled={!selectedResourceId || isCreating || basket.length >= MAX_LOT_ITEMS}
              >
                + Добавить
              </button>
            </div>

            {basket.length > 0 && (
              <>
                <table className={styles.basketTable}>
                  <colgroup>
                    <col className={styles.colResource} />
                    <col className={styles.colQty} />
                    <col className={styles.colRemove} />
                  </colgroup>
                  <thead>
                    <tr><th>Ресурс</th><th>Кол-во</th><th></th></tr>
                  </thead>
                  <tbody>
                    {basket.map((item) => (
                      <tr key={item.id}>
                        <td>
                          <div className={styles.basketResource}>
                            <div className={styles.basketImageBox}>
                              <img
                                src={item.icon_url || '/icons/default.png'}
                                alt={item.name}
                                className={styles.basketIcon}
                                onError={e => { e.target.onerror = null; e.target.src = '/icons/default.png'; }}
                              />
                            </div>
                            <span>{item.name}</span>
                          </div>
                        </td>
                        <td>
                          <input
                            type="text"
                            inputMode="numeric"
                            pattern="[0-9]*"
                            placeholder="1"
                            value={item.quantity}
                            onChange={intInputHandler(v => updateBasketItem(item.id, 'quantity', v), 7, { strip: true })}
                          />
                        </td>
                        <td>
                          <button type="button" className={styles.btnRemove} onClick={() => removeBasketItem(item.id)} title="Убрать из корзины" disabled={isCreating}>
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                <div className={styles.bundlePriceContainer}>
                  <label className={styles.bundlePriceLabel}>Цена лота:</label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0.00"
                    value={bundlePrice}
                    onChange={decimalInputHandler(setBundlePrice, 7, 2, { strip: true })}
                    className={styles.bundlePriceInput}
                    disabled={isCreating}
                  />
                </div>

                {minLotPrice > 0 && (
                  <div className={styles.bundlePriceHint}>
                    Минимум: {minLotPrice.toFixed(2)} дт.
                  </div>
                )}
              </>
            )}            

            <button
              className={`${btn.simpleButton} ${btn.simpleButtonGold} ${btn.sizeFull} ${styles.submitButton}`}
              type="submit"
              disabled={!canSubmit}
            >
              Разместить лот
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

const LotCard = ({ lot, isMyLot, resourceMap, busyLotId, onDeal, onCancel, mode }) => {
  return (
    <div className={styles.lotCard}>
      <table className={styles.lotsTable}>
        <thead>
          <tr>
            {mode === 'sell' ? (
              <>
                <th className={styles.tableHeader}>Ресурсы</th>
                <th className={styles.tableHeader}>Цена</th>
              </>
            ) : (
              <>
                <th className={styles.tableHeader}>Цена</th>
                <th className={styles.tableHeader}>Ресурсы</th>
              </>
            )}
          </tr>
        </thead>
        <tbody>
          {lot.items.map((item, idx) => {
            const resource = resourceMap[item.resource_id] || {};

            const resourceCell = (
              <td className={styles.lotCell}>
                <div className={styles.resourceRow}>
                  <span className={styles.lotItemName}>{resource.name || '?'}</span>
                  <span className={styles.lotItemQty}>{item.quantity} шт.</span>
                </div>
              </td>
            );

            const priceCell = idx === 0 ? (
              <td rowSpan={lot.items.length} className={styles.priceCell}>
                {lot.price} дт.
              </td>
            ) : null;

            return (
              <tr key={item.id} className={styles.lotRow}>
                {mode === 'sell' ? (<>{resourceCell}{priceCell}</>) : (<>{priceCell}{resourceCell}</>)}
              </tr>
            );
          })}
        </tbody>
      </table>

      {lot.status === 'ACTIVE' && (
        <div className={styles.lotActions}>
          {isMyLot ? (
            <button
              className={styles.cancelButton}
              onClick={() => onCancel(lot.id)}
              disabled={busyLotId !== null}
            >
              Отменить
            </button>
          ) : (
            <button
              className={`${btn.simpleButton} ${btn.simpleButtonGold} ${styles.lotActionButton}`}
              onClick={() => onDeal(lot)}
              disabled={busyLotId !== null}
            >
              {mode === 'sell' ? 'Купить' : 'Продать'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default ExchangeTab;