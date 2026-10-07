import React, { useState, useEffect, useRef } from 'react';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { sortInventoryItems } from '../../../entities/items/config/recipeOrderConfig';
import { useGetCharacterItemsQuery, useUseItemMutation } from '../../../entities/items/api/inventoryApi';
import styles from '../InventoryModal.module.css';
import btn from '../../../shared/styles/buttons.module.css';

const extractErrorMessage = (err, fallback = 'Ошибка действия') => {
  const data = err?.data || err?.response?.data;
  return data?.extras?.message || data?.message || data?.detail || err?.message || fallback;
};

export const ProductsTab = ({ character }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [usingId, setUsingId] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const pendingClearRef = useRef(false);

  const { data: allItems = [], isLoading } = useGetCharacterItemsQuery();
  const [applyItem] = useUseItemMutation();

  const items = React.useMemo(
    () => sortInventoryItems(
      (allItems || []).filter(
        i => String(i.item?.item_type).toLowerCase() === 'fish'
      )
    ),
    [allItems]
  );

  useEffect(() => {
    if (!errorMessage) return;
    const timer = setTimeout(() => setErrorMessage(null), 8000);
    return () => clearTimeout(timer);
  }, [errorMessage]);

  useEffect(() => {
    if (!pendingClearRef.current) return;
    pendingClearRef.current = false;
    setErrorMessage(null);
  }, [allItems]);

  const handleUse = async (id) => {
    try {
      setUsingId(id);
      await applyItem(id).unwrap();
      pendingClearRef.current = true;
      setSelectedItem(null);      
    } catch (err) {
      pendingClearRef.current = false;
      setErrorMessage(extractErrorMessage(err, 'Ошибка применения'));
    } finally {
      setUsingId(null);
    }
  };

  return (
    <div className={styles.resourceWrapper}>
      {selectedItem && (
        <ItemInfoCard
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          character={character}
        />
      )}

      <div className={styles.resourceList}>
        {errorMessage && (
          <div className={styles.errorMessage}>{errorMessage}</div>
        )}

        {!isLoading && items.length === 0 && (
          <div className={styles.placeholder}>Нет продуктов</div>
        )}
        {items.map(item => (
          <div key={item.id} className={styles.resourceRow}>
            <div className={styles.resourceName}>
              <span
                className={styles.resourceNameText}
                onClick={() => setSelectedItem(item)}
              >
                {item.item.name}
              </span>
              <span className={styles.resourceAmount}> {item.amount} шт.</span>
              <button
                className={btn.textLinkAction}
                onClick={() => handleUse(item.id)}
                disabled={usingId === item.id}
              >
                Съесть
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};