import { invalidateCharacter, invalidateCharacterAndResources } from './helpers';

export const dealsEndpoints = (builder) => ({
  // ═══ СДЕЛКИ (чтение) ═══
  getNearbyPartners: builder.query({
    query: (locationSlug) => ({
      url: '/deals/partners/nearby',
      method: 'GET',
      params: { location_slug: locationSlug },
    }),
    providesTags: (result, error, locationSlug) => [
      { type: 'DealPartners', id: locationSlug || 'ALL' }
    ],
    keepUnusedDataFor: 5 * 60, 
  }),

  getDeals: builder.query({
    query: () => ({ url: '/deals', method: 'GET' }),
    providesTags: ['Deals'],
    keepUnusedDataFor: 5 * 60, 
  }),

  getDeal: builder.query({
    query: (dealId) => ({ url: `/deals/${dealId}`, method: 'GET' }),
    providesTags: (result, error, dealId) => [{ type: 'Deal', id: dealId }],      
  }),

  // ═══ СДЕЛКИ (изменения) ═══
  createDeal: builder.mutation({
    query: ({ partnerCharacterId, locationSlug }) => ({
      url: '/deals',
      method: 'POST',
      data: { partner_character_id: partnerCharacterId, location_slug: locationSlug },
    }),
    invalidatesTags: (result) => [
      'Inventory', 'Deals', result?.id ? { type: 'Deal', id: result.id } : 'Deal',
    ],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  acceptDeal: builder.mutation({
    query: (dealId) => ({ url: `/deals/${dealId}/accept`, method: 'POST' }),
    invalidatesTags: (result, error, dealId) => ['Inventory', 'Deals', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  confirmDeal: builder.mutation({
    query: (dealId) => ({ url: `/deals/${dealId}/confirm`, method: 'POST' }),
    invalidatesTags: (result, error, dealId) => ['Inventory', 'Deals', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndResources(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  cancelDeal: builder.mutation({
    query: (dealId) => ({ url: `/deals/${dealId}/cancel`, method: 'POST' }),
    invalidatesTags: (result, error, dealId) => ['Inventory', 'Deals', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndResources(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  setDealDucats: builder.mutation({
    query: ({ dealId, amount }) => ({
      url: `/deals/${dealId}/offer/ducats`,
      method: 'PUT',
      data: { amount, operation_id: crypto.randomUUID() },
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  setDealGold: builder.mutation({
    query: ({ dealId, amount }) => ({
      url: `/deals/${dealId}/offer/gold`,
      method: 'PUT',
      data: { amount, operation_id: crypto.randomUUID() },
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  addDealResource: builder.mutation({
    query: ({ dealId, resourceSlug, amount }) => ({
      url: `/deals/${dealId}/offer/resources/${resourceSlug}`,
      method: 'PUT',
      data: { amount },
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndResources(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  removeDealResource: builder.mutation({
    query: ({ dealId, resourceSlug }) => ({
      url: `/deals/${dealId}/offer/resources/${resourceSlug}`,
      method: 'DELETE',
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndResources(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  addDealItem: builder.mutation({
    query: ({ dealId, inventoryItemId, amount }) => ({
      url: `/deals/${dealId}/offer/items`,
      method: 'POST',
      data: { inventory_item_id: inventoryItemId, amount },
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  removeDealItem: builder.mutation({
    query: ({ dealId, dealItemId }) => ({
      url: `/deals/${dealId}/offer/items/${dealItemId}`,
      method: 'DELETE',
    }),
    invalidatesTags: (result, error, { dealId }) => ['Inventory', { type: 'Deal', id: dealId }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),
});