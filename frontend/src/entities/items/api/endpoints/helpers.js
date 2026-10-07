// entities/items/api/endpoints/helpers.js
import { characterApi } from '../../../character/api/characterApi';
import { characterStatsApi } from '../../../character/api/characterStatsApi';
import { resourcesApi } from '../../../resources/api/resourcesApi';

// Обновление персонажа и баффов (для крафта)
export const invalidateCharacterAndBuffs = async (dispatch, getState) => {
  dispatch(characterApi.util.invalidateTags(['Character']));
  dispatch(characterStatsApi.util.invalidateTags(['Buffs']));
  
  const state = getState();
  const onlyMeQuery = characterApi.endpoints.getOnlyMe.select()(state);
  if (onlyMeQuery?.data) {
    await dispatch(characterApi.endpoints.getOnlyMe.initiate(undefined, {
      forceRefetch: true,
      subscribe: false
    })).unwrap();
  }
  
  const activeCharacterId = state.local?.activeCharacterId;
  if (activeCharacterId) {
    await dispatch(characterStatsApi.endpoints.getCharacterBuffs.initiate(activeCharacterId, {
      forceRefetch: true,
      subscribe: false
    })).unwrap();
  }
};

// Обновление только персонажа (для лавки, сделок)
export const invalidateCharacter = async (dispatch, getState) => {
  dispatch(characterApi.util.invalidateTags(['Character']));
  
  const state = getState();
  const onlyMeQuery = characterApi.endpoints.getOnlyMe.select()(state);
  if (onlyMeQuery?.data) {
    await dispatch(characterApi.endpoints.getOnlyMe.initiate(undefined, {
      forceRefetch: true,
      subscribe: false
    })).unwrap();
  }
};

// Для сделок, которые затрагивают ресурсы
export const invalidateCharacterAndResources = async (dispatch, getState) => {
  dispatch(characterApi.util.invalidateTags(['Character']));
  dispatch(resourcesApi.util.invalidateTags(['Resources']));
  
  const state = getState();
  const onlyMeQuery = characterApi.endpoints.getOnlyMe.select()(state);
  if (onlyMeQuery?.data) {
    await dispatch(characterApi.endpoints.getOnlyMe.initiate(undefined, { forceRefetch: true, subscribe: false })).unwrap();
  }
};