import { invalidateCharacterAndBuffs } from './helpers';



export const craftingEndpoints = (builder) => ({
  // ═══ МАСТЕРСКАЯ (чтение данных) ═══
  getStartedCrafting: builder.query({
    query: (locationSlug) => ({
      url: '/creating',
      method: 'GET',
      params: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    providesTags: (result, error, locationSlug) => [
      { type: 'StartedCrafting', id: locationSlug || 'ALL' },
    ],
    keepUnusedDataFor: 5 * 60, 
  }),

  getStockRecipes: builder.query({
    query: (locationSlug) => ({
      url: '/recipes/me/stock',
      method: 'GET',
      params: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    providesTags: (result, error, locationSlug) => [
      { type: 'WorkshopRecipes', id: locationSlug || 'ALL' },
    ],
    keepUnusedDataFor: 5 * 60, 
  }),

  getCityShopStats: builder.query({
    query: (locationSlug) => ({
      url: '/city-shop/stats',
      method: 'GET',
      params: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    providesTags: (result, error, locationSlug) => [
      { type: 'WorkshopStats', id: locationSlug || 'ALL' },
    ],
    keepUnusedDataFor: 5 * 60, 
  }),

  getCraftingStatus: builder.query({
    query: () => ({ url: '/crafting/status', method: 'GET' }),
    providesTags: ['CraftingStatus'],
  }),

  getCraftingAction: builder.query({
    query: (craftingId) => ({
      url: `/crafting/action/${craftingId}`,
      method: 'GET',
    }),
    providesTags: (result, error, craftingId) => [
      { type: 'CraftingAction', id: craftingId },
    ],
  }),

  getCraftingLicenseStatus: builder.query({
    query: (args) => {
      const locationSlug = typeof args === 'string' ? args : args?.locationSlug;
      const characterId = typeof args === 'object' ? args?.characterId : undefined;
      return {
        url: '/crafting-license/status',
        method: 'GET',
        params: {
          ...(locationSlug ? { location_slug: locationSlug } : {}),
          ...(characterId ? { character_id: characterId } : {}),
        },
      };
    },
    providesTags: (result, error, args) => {
      const locationSlug = typeof args === 'string' ? args : args?.locationSlug;
      return [{ type: 'CraftingLicense', id: locationSlug || 'LIST' }];
    },
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ КРАФТ (ресурсы + дукаты → Character) ═══
  startNewCrafting: builder.mutation({
    query: ({ recipeId, captchaId, userInput }) => ({
      url: `/crafting/${recipeId}/new`,
      method: 'POST',
      data: { captcha_id: captchaId, user_input: userInput },
    }),
    invalidatesTags: (result, error, { locationSlug }) => [
      'Inventory',
      'CraftingStatus',
      { type: 'StartedCrafting', id: locationSlug },
      { type: 'WorkshopStats', id: locationSlug },
    ],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch (e) {
        console.error('[startNewCrafting] Error invalidating data:', e);
      }
    },
  }),

  continueCrafting: builder.mutation({
    query: ({ recipeId, captchaId, userInput }) => ({
      url: `/crafting/${recipeId}/continue`,
      method: 'POST',
      data: { captcha_id: captchaId, user_input: userInput },
    }),
    invalidatesTags: (result, error, { locationSlug }) => [
      'Inventory',
      'CraftingStatus',
      { type: 'StartedCrafting', id: locationSlug },
      { type: 'WorkshopStats', id: locationSlug },
    ],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch (e) {
        console.error('[continueCrafting] Error invalidating data:', e);
        if (e?.error?.status === 404) {
          console.error('❌ [continueCrafting] 404 ошибка. Детали:', e.error.data);
        }
      }
    },
  }),

  cancelExpiredCrafting: builder.mutation({
    query: () => ({ url: '/crafting/cancel-expired', method: 'POST' }),
    invalidatesTags: [
      'Inventory', 
      'CraftingStatus', 
      'StartedCrafting', 
      { type: 'WorkshopStats', id: 'ALL' }
    ],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch (e) {
        console.error('[cancelExpiredCrafting] Error invalidating data:', e);
      }
    },
  }),

  // ═══ РЕЦЕПТЫ И ЛИЦЕНЗИИ (дукаты → Character) ═══
  buyRecipe: builder.mutation({
    query: ({ itemSlug, quantity }) => ({
      url: '/recipes',
      method: 'POST',
      data: { item_slug: itemSlug, quantity },
    }),
    invalidatesTags: ['Recipes', 'MyRecipes', { type: 'WorkshopRecipes' }],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  buyCraftingLicense: builder.mutation({
    query: (locationSlug) => ({
      url: '/crafting-license/buy',
      method: 'POST',
      data: { location_slug: locationSlug },
    }),
    invalidatesTags: (result, error, locationSlug) => 
      locationSlug ? [{ type: 'CraftingLicense', id: locationSlug }] : ['CraftingLicense'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacterAndBuffs(dispatch, getState);
      } catch {
        // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  renewCraftingLicense: builder.mutation({
    query: (locationSlug) => ({
      url: '/crafting-license/renew',
      method: 'POST',
      data: { location_slug: locationSlug },
    }),
    invalidatesTags: (result, error, locationSlug) => 
      locationSlug ? [{ type: 'CraftingLicense', id: locationSlug }] : ['CraftingLicense'],
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