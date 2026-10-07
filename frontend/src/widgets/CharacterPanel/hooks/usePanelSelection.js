import { useCallback, useState, useEffect } from 'react';
import { useGetMyPanelsQuery, useUpdatePanelMutation } from '../../../entities/character/api/panelApi';

export const usePanelSelection = () => {
  // 1. Получаем данные и статус загрузки из RTK Query
  const { data: panelData } = useGetMyPanelsQuery();
  const [updatePanel] = useUpdatePanelMutation();

  // 2. Локальный стейт для мгновенного отклика UI
  const [selectedItems, setSelectedItems] = useState({ first_item: null, second_item: null });

  // 3. Синхронизируем локальный стейт с данными сервера при загрузке
  useEffect(() => {
    if (panelData) {
      setSelectedItems({
        first_item: panelData.first_item,
        second_item: panelData.second_item
      });
    }
  }, [panelData]);

  const handleCheckboxChange = useCallback(async (itemId, isChecked) => {
    if (!panelData) return;

    // Рассчитываем новое состояние (твоя старая логика сдвига)
    let newSelectedItems = { ...selectedItems };
    if (isChecked) {
      if (!newSelectedItems.first_item) newSelectedItems.first_item = itemId;
      else if (!newSelectedItems.second_item) newSelectedItems.second_item = itemId;
      else {
        newSelectedItems.first_item = newSelectedItems.second_item;
        newSelectedItems.second_item = itemId;
      }
    } else {
      if (newSelectedItems.first_item === itemId) {
        newSelectedItems.first_item = newSelectedItems.second_item;
        newSelectedItems.second_item = null;
      } else if (newSelectedItems.second_item === itemId) {
        newSelectedItems.second_item = null;
      }
    }

    // МГНОВЕННО обновляем UI
    setSelectedItems(newSelectedItems);

    // Отправляем на сервер
    try {
      await updatePanel({ panelId: panelData.id, data: newSelectedItems }).unwrap();
    } catch (err) {
      // В случае ошибки откатываем UI назад
      setSelectedItems({
        first_item: panelData.first_item,
        second_item: panelData.second_item
      });
      console.error("Ошибка обновления панели:", err);
    }
  }, [panelData, selectedItems, updatePanel]);

  const isItemChecked = useCallback((itemId) => {
    return selectedItems.first_item === itemId || selectedItems.second_item === itemId;
  }, [selectedItems]);

  return { 
    handleCheckboxChange, 
    isItemChecked,     
  };
};