import { useState, useEffect, useRef, useMemo } from 'react';
import { ItemInfoCard } from '../../../entities/items/ui/ItemInfoCard';
import {
  useGetCharacterItemsQuery,
  useGetMyEquipmentQuery,
  useEquipItemMutation,
  useUnequipItemMutation,
  useUnpackKitMutation,   
} from '../../../entities/items/api/inventoryApi';
import btn from '../../../shared/styles/buttons.module.css';
import styles from '../InventoryModal.module.css';

const EQUIPMENT_TYPES = [
  'weapon', 'shield', 'helmet', 'armor', 'gauntlets', 'gloves',
  'leggings', 'boots', 'cloak', 'amulet', 'pendant', 'ring',
  'kit',  
];

const extractErrorMessage = (err, fallback = 'Ошибка действия') => {
  const data = err?.data || err?.response?.data;
  return data?.extras?.message || data?.message || data?.detail || err?.message || fallback;
};

export const EquipmentTab = ({ character }) => {
  const [selectedItem, setSelectedItem] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const pendingClearRef = useRef(false);

  const { data: equippedItems = [], isLoading: eqLoading } = useGetMyEquipmentQuery();
  const { data: allItems = [], isLoading: itemsLoading } = useGetCharacterItemsQuery();
  const isLoading = eqLoading || itemsLoading;

  const [equipItem] = useEquipItemMutation();
  const [unequipItem] = useUnequipItemMutation();
  const [unpackKit] = useUnpackKitMutation(); 

  const backpackItems = useMemo(() => {
    const equippedIds = new Set((equippedItems || []).map(i => i.id));
    return (allItems || []).filter(
      item => EQUIPMENT_TYPES.includes(String(item.item?.item_type).toLowerCase())
        && !equippedIds.has(item.id)
    );
  }, [equippedItems, allItems]);

  useEffect(() => {
    if (!errorMessage) return;
    const timer = setTimeout(() => setErrorMessage(null), 8000);
    return () => clearTimeout(timer);
  }, [errorMessage]);

  useEffect(() => {
    if (!pendingClearRef.current) return;
    pendingClearRef.current = false;
    setErrorMessage(null);
  }, [equippedItems, allItems]);

  const handleEquip = async (id) => {
    try {
      setActionInProgress(id);
      await equipItem(id).unwrap();
      pendingClearRef.current = true;
      setSelectedItem(null);      
    } catch (err) {
      pendingClearRef.current = false;
      setErrorMessage(extractErrorMessage(err, 'Ошибка надевания'));
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUnequip = async (id) => {
    try {
      setActionInProgress(id);
      await unequipItem(id).unwrap();
      pendingClearRef.current = true;
      setSelectedItem(null);      
    } catch (err) {
      pendingClearRef.current = false;
      setErrorMessage(extractErrorMessage(err, 'Ошибка снятия'));
    } finally {
      setActionInProgress(null);
    }
  };

  const handleUnpackKit = async (id) => {
    try {
      setActionInProgress(id);
      await unpackKit(id).unwrap();
      pendingClearRef.current = true;
      setSelectedItem(null);
    } catch (err) {
      pendingClearRef.current = false;
      setErrorMessage(extractErrorMessage(err, 'Ошибка распаковки'));
    } finally {
      setActionInProgress(null);
    }
  };

  const renderItemRow = (item, isEquipped) => {
    const wear = item.wear ?? 0;
    const maxWear = item.item?.parameters?.max_wear ?? null;
    const isWearCritical = maxWear ? wear > maxWear * 0.75 : wear > 0;

    const isKit = String(item.item?.item_type).toLowerCase() === 'kit';

    // Определяем кнопку и действие
    let actionLabel = 'Надеть';
    let actionHandler = () => handleEquip(item.id);
    if (isEquipped) {
      actionLabel = 'Снять';
      actionHandler = () => handleUnequip(item.id);
    } else if (isKit) {
      actionLabel = 'Распаковать';
      actionHandler = () => handleUnpackKit(item.id);
    }

    return (
      <div key={item.id} className={styles.resourceRow}>
        <div className={styles.resourceName}>
          <span
            className={styles.resourceNameText}
            onClick={() => setSelectedItem(item)}
          >
            {item.item.name}
          </span>
          {!isKit && maxWear != null && (
            <span className={isWearCritical ? styles.itemWearInlineRed : styles.itemWearInline}>
              {' '}[{wear}/{maxWear}]
            </span>
          )}
          <button
            className={btn.textLinkAction}
            onClick={actionHandler}
            disabled={actionInProgress === item.id}
          >
            {actionLabel}
          </button>
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
        {errorMessage && (
          <div className={styles.errorMessage}>{errorMessage}</div>
        )}

        {!isLoading && (
          <>
            {equippedItems.length > 0 && (
              <>
                {equippedItems.map(item => renderItemRow(item, true))}
                <div className={styles.listDivider} />
              </>
            )}

            {backpackItems.length === 0 ? (
              <div className={styles.placeholder}>Нет предметов для экипировки</div>
            ) : (
              backpackItems.map(item => renderItemRow(item, false))
            )}
          </>
        )}
      </div>
    </div>
  );
};