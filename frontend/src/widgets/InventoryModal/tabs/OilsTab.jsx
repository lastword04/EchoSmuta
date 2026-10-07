import React, { useState, useMemo } from 'react';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { sortInventoryItems } from '../../../entities/items/config/recipeOrderConfig';
import { useGetCharacterItemsQuery } from '../../../entities/items/api/inventoryApi';
import styles from '../InventoryModal.module.css';

export const OilsTab = ({ character }) => {
  const [selectedItem, setSelectedItem] = useState(null);

  const { data: allItems = [], isLoading } = useGetCharacterItemsQuery();

  const items = useMemo(
    () => sortInventoryItems(
      (allItems || []).filter(
        i => String(i.item?.item_type).toLowerCase() === 'oil'
      )
    ),
    [allItems]
  );

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
        {!isLoading && items.length === 0 && (
          <div className={styles.placeholder}>Нет масел</div>
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};