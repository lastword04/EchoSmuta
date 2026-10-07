import { useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { refreshAllData } from '../store/refreshSlice';
import { characterApi } from '../../../entities/character/api/characterApi';
import { characterStatsApi } from '../../../entities/character/api/characterStatsApi';
import { inventoryApi } from '../../../entities/items/api/inventoryApi';
import { housesApi } from '../../../entities/character/api/housesApi';
import { useErrorToast } from '../../../shared/hooks/ui/useErrorToast';

export const useBaseRefresh = () => {
  const dispatch = useDispatch();
  const { showError } = useErrorToast();

  const handleRefresh = useCallback(async () => {
    try {
      await dispatch(refreshAllData()).unwrap();
      dispatch(characterApi.util.invalidateTags(['Character']));
      dispatch(characterStatsApi.util.invalidateTags(['Buffs']));
      dispatch(inventoryApi.util.invalidateTags(['Inventory']));    
      dispatch(housesApi.util.invalidateTags(['Houses', 'HouseFurniture', 'HousesGuests']));
    } catch {
      showError('Ошибка обновления данных');
    }
  }, [dispatch, showError]);

  return { handleRefresh };
};