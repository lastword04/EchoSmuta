// 🔥 ГЛОБАЛЬНЫЙ КЭШ НА ВСЁ ПРИЛОЖЕНИЕ
let globalBellMapCache = null;
let bellMapCachePromise = null;
let globalBellSizesCache = null;
let bellSizesCachePromise = null;

export const fetchBellMapCached = async () => {
  if (globalBellMapCache) return globalBellMapCache;
  if (bellMapCachePromise) return bellMapCachePromise;

  bellMapCachePromise = fetch('/bells-map.json')
    .then(res => res.json())
    .then(data => {
      globalBellMapCache = data;
      bellMapCachePromise = null;
      return data;
    })
    .catch(error => {
      bellMapCachePromise = null;
      throw error;
    });

  return bellMapCachePromise;
};

export const fetchBellSizesCached = async () => {
  if (globalBellSizesCache) return globalBellSizesCache;
  if (bellSizesCachePromise) return bellSizesCachePromise;

  bellSizesCachePromise = fetch('/bells-sizes.json')
    .then(res => res.json())
    .then(data => {
      globalBellSizesCache = data;
      bellSizesCachePromise = null;
      return data;
    })
    .catch(error => {
      bellSizesCachePromise = null;
      throw error;
    });

  return bellSizesCachePromise;
};

export const getBellMapSync = () => globalBellMapCache || {};
export const getBellSizesSync = () => globalBellSizesCache || {};