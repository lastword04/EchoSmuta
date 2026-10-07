import React, { useState, useMemo } from 'react';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import { sortInventoryItems } from '../../../entities/items/config/recipeOrderConfig';
import { useGetCharacterItemsQuery } from '../../../entities/items/api/inventoryApi';
import { useGetMyFurnitureQuery } from '../../../entities/character/api/housesApi';
import styles from '../InventoryModal.module.css';

export const FurnitureTab = ({ character }) => {
  const [selectedItem, setSelectedItem] = useState(null);

  const { data: allItems } = useGetCharacterItemsQuery();
  const { data: myFurniture } = useGetMyFurnitureQuery();

  // Готово, когда пришли ОБА ответа
  const isReady = allItems !== undefined && myFurniture !== undefined;

  const availableIds = useMemo(
    () => new Set((myFurniture || []).map(f => f.inventory_item_id)),
    [myFurniture]
  );

  const items = useMemo(
    () => isReady
      ? sortInventoryItems(
          (allItems || []).filter(
            i => String(i.item?.item_type).toLowerCase() === 'furniture'
                 && availableIds.has(i.id)
          )
        )
      : [],
    [allItems, availableIds, isReady]
  );

  const renderItemRow = (item) => {
    const wear = item.wear ?? 0;
    const maxWear = item.item?.parameters?.max_wear ?? null;
    const isWearCritical = maxWear ? wear > maxWear * 0.75 : wear > 0;

  return (
      <div key={item.id} className={styles.resourceRow}>
        <div className={styles.resourceName}>
          <span
            className={styles.resourceNameText}
            onClick={() => setSelectedItem(item)}
          >
            {item.item.name}
          </span>
          {maxWear != null && (
            <span className={isWearCritical ? styles.itemWearInlineRed : styles.itemWearInline}>
              {' '}[{Math.round(wear)}/{Math.round(maxWear)}]
            </span>
          )}
        </div>
      </div>
    );
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
        {isReady && items.length === 0 && (
          <div className={styles.placeholder}>Нет мебели</div>
        )}
        {isReady && items.map(item => renderItemRow(item))}
      </div>
    </div>
  );
};
