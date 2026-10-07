import React, { useState, useEffect, useRef, useMemo } from 'react';
import { ItemInfoCard } from '../../../../entities/items/ui/ItemInfoCard';
import { sortInventoryItems } from '../../../../entities/items/config/recipeOrderConfig';
import {
  useGetCharacterItemsQuery,
  useUseItemMutation,
} from '../../../../entities/items/api/inventoryApi';
import styles from '../MagicModal.module.css';
import btn from '../../../../shared/styles/buttons.module.css';

const humanizeError = (message) => {
  const buffKeys = ['strength_boost', 'agility_boost', 'luck_boost'];
  for (const key of buffKeys) {
    if (message.includes(key)) return 'Вы уже употребили эликсир подобного свойства';
  }
  return message;
};

export const ElixirsTab = ({ character }) => {
  const [usingId, setUsingId] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const pendingClearRef = useRef(false);

  const { data: allItems = [], isLoading: loading } = useGetCharacterItemsQuery();
  const [applyItem] = useUseItemMutation();

  const elixirs = useMemo(
    () => sortInventoryItems(
      (allItems || []).filter(
        item => String(item.item?.item_type).toLowerCase() === 'elixir'
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

  const handleUse = async (inventoryItemId) => {
    try {
      setUsingId(inventoryItemId);
      await applyItem(inventoryItemId).unwrap();
      pendingClearRef.current = true;
      setSelectedItem(null);
    } catch (err) {
      console.error('Ошибка применения эликсира:', err);
      pendingClearRef.current = false;
      const data = err?.data || err?.response?.data;
      const rawMessage =
        data?.extras?.message || data?.message || data?.detail ||
        err?.message || 'Ошибка применения';
      setErrorMessage(humanizeError(rawMessage));
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

      <div className={styles.list}>
        {errorMessage && <div className={styles.errorMessage}>{errorMessage}</div>}

        {!loading && elixirs.length === 0 ? (
          <div className={styles.placeholder}>У вас нет эликсиров</div>
        ) : (
          elixirs.map(item => (
            <div key={item.id} className={styles.elixirRow}>
              <div className={styles.elixirName}>
                <span className={styles.elixirNameText} onClick={() => setSelectedItem(item)}>
                  {item.item.name}
                </span>
                <span className={styles.elixirAmount}> {item.amount} шт.</span>
                <button
                  className={btn.textLinkAction}
                  onClick={() => handleUse(item.id)}
                  disabled={usingId === item.id}
                >
                  Выпить
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};