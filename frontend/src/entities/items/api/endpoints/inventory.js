import { invalidateCharacterAndBuffs } from './helpers';

export const inventoryEndpoints = (builder) => ({
  // ═══ ИНВЕНТАРЬ И ЭКИПИРОВКА (чтение) ═══
  getCharacterItems: builder.query({
    query: () => ({ url: '/me', method: 'GET' }),
    providesTags: ['Inventory'],
    keepUnusedDataFor: 3 * 60, 
  }),

  getMyEquipment: builder.query({
    query: () => ({ url: '/equipment/me', method: 'GET' }),
    providesTags: ['Inventory'],
    keepUnusedDataFor: 3 * 60, 
  }),

  // ═══ ПРЕДМЕТ ПО СЛАГУ ═══
  getItemBySlug: builder.query({
    query: (slug) => ({
      url: `/item/${slug}`,
      method: 'GET',
    }),
    providesTags: (result, error, slug) => [{ type: 'Item', id: slug }],
    keepUnusedDataFor: 60 * 5,
  }),

  // ═══ ЧТЕНИЕ ЛАВКИ (из оригинала, забыл в shop.js, добавляем сюда или в shop, пусть будет тут) ═══
  getItemsFromLocation: builder.query({
    query: (locationSlug) => ({
      url: '/from-location',
      method: 'GET',
      params: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    providesTags: (result, error, locationSlug) => [
      { type: 'ShopItems', id: locationSlug || 'ALL' }
    ],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ ДЕЙСТВИЯ С ИНВЕНТАРЕМ (влияют на Character и Buffs) ═══
  useItem: builder.mutation({
    query: (inventoryItemId) => ({
      url: `/${inventoryItemId}/use`,
      method: 'POST',
    }),
    invalidatesTags: ['Inventory'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  equipItem: builder.mutation({
    query: (inventoryItemId) => ({
      url: `/equip/${inventoryItemId}`,
      method: 'POST',
    }),
    invalidatesTags: ['Inventory'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  unequipItem: builder.mutation({
    query: (inventoryItemId) => ({
      url: `/unequip/${inventoryItemId}`,
      method: 'POST',
    }),
    invalidatesTags: ['Inventory'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  unpackKit: builder.mutation({
    query: (inventoryItemId) => ({
      url: `/unpack/${inventoryItemId}`,
      method: 'POST',
    }),
    invalidatesTags: ['Inventory'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),
});