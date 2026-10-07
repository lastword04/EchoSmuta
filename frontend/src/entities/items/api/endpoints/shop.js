import { invalidateCharacter } from './helpers';


export const shopEndpoints = (builder) => ({
  // ═══ СПИСОК ЛАВОК ═══
  getShopsList: builder.query({
    query: ({ locationSlug, page = 1, pageSize = 5, minimalLevel, itemKind, number, itemName }) => {
      const params = { page, page_size: pageSize };
      if (locationSlug) params.location_slug = locationSlug;
      if (minimalLevel != null) params.minimal_level = minimalLevel;
      if (itemKind) params.item_kind = itemKind;
      if (number) params.number = number;
      if (itemName) params.item_name = itemName;
      return { url: '/city-shop/paginate', method: 'GET', params };
    },
    providesTags: (result, error, arg) => [
      { type: 'ShopsList', id: arg?.locationSlug || 'ALL' },
    ],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ ИСТОРИЯ ПРОДАЖ ═══
  getSalesHistory: builder.query({
    query: ({ limit = 30, locationSlug }) => ({
      url: '/city-shop/sales-history',
      method: 'GET',
      params: { limit, ...(locationSlug ? { location_slug: locationSlug } : {}) },
    }),
    providesTags: (result, error, arg) => [
      { type: 'SalesHistory', id: arg?.locationSlug || 'ALL' }
    ],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ РЕЦЕПТЫ (публичный список) ═══
  getRecipes: builder.query({
    query: ({ quantity = 50, locationSlug }) => ({
      url: '/recipes',
      method: 'GET',
      params: { quantity, ...(locationSlug ? { location_slug: locationSlug } : {}) },
    }),
    providesTags: (result, error, arg) => [
      { type: 'Recipes', id: arg?.locationSlug || 'ALL' }
    ],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ МОИ РЕЦЕПТЫ ═══
  getMyRecipes: builder.query({
    query: ({ locationSlug }) => ({
      url: '/recipes/me',
      method: 'GET',
      params: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    providesTags: (result, error, arg) => [
      { type: 'MyRecipes', id: arg?.locationSlug || 'ALL' }
    ],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ ЛАВКА ПО ID ═══
  getCityShopById: builder.query({
    query: (shopId) => ({
      url: `/city-shop/${shopId}`,
      method: 'GET',
    }),
    providesTags: (result, error, shopId) => [{ type: 'CityShop', id: shopId }],
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ ЛАВКА ПО НОМЕРУ ═══
  getCityShopByNumber: builder.query({
    query: (number) => ({
      url: `/city-shop/number/${number}`,
      method: 'GET',
    }),
  }),

  // ═══ ЛАВКА (основная) ═══
  getCityShop: builder.query({
    query: (args) => {
      const locationSlug = typeof args === 'string' ? args : args?.locationSlug;
      const characterId = typeof args === 'object' ? args?.characterId : undefined;
      return {
        url: '/city-shop',
        method: 'GET',
        params: {
          ...(locationSlug ? { location_slug: locationSlug } : {}),
          ...(characterId ? { character_id: characterId } : {}),
        },
      };
    },
    providesTags: (result, error, args) => {
      const locationSlug = typeof args === 'string' ? args : args?.locationSlug;
      return [{ type: 'CityShop', id: locationSlug || 'LIST' }];
    },
    keepUnusedDataFor: 5 * 60,
  }),

  // ═══ ТОРГОВАЯ ЛИЦЕНЗИЯ ═══
  getTradeLicenseStatus: builder.query({
    query: (args) => {
      const characterId = typeof args === 'object' ? args?.characterId : undefined;
      return {
        url: '/trade-license/status',
        method: 'GET',
        params: characterId ? { character_id: characterId } : undefined,
      };
    },
    providesTags: (result, error, args) => {
      const characterId = typeof args === 'object' ? args?.characterId : undefined;
      return [{ type: 'TradeLicense', id: characterId || 'ALL' }];
    },
  }),

  // ═══ ЛАВКА (влияет на вес) ═══
  listItemToShop: builder.mutation({
    query: ({ itemId, amount }) => ({
      url: `/shops/inventory/${itemId}/list`,
      method: 'POST',
      data: { amount },
    }),
    invalidatesTags: ['Inventory', 'ShopItems'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  withdrawItemFromShop: builder.mutation({
    query: ({ itemId, amount }) => ({
      url: `/shops/inventory/${itemId}/withdraw`,
      method: 'POST',
      data: { amount },
    }),
    invalidatesTags: ['Inventory', 'ShopItems'],
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  purchaseItem: builder.mutation({
    query: ({ inventoryItemId, amount }) => ({
      url: `/purchase/inventory/${inventoryItemId}`,
      method: 'POST',
      data: amount != null ? { amount } : undefined,
    }),
    invalidatesTags: (result, error, { locationSlug }) => [
      'Inventory',
      'ShopItems',
      'CityShop',
      'ShopsList',
      { type: 'StartedCrafting', id: locationSlug || 'ALL' },
      { type: 'WorkshopRecipes', id: locationSlug || 'ALL' },
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

  putItemOnSale: builder.mutation({
    query: ({ inventoryItemId, price, amount }) => ({
      url: `/sale/inventory/${inventoryItemId}`,
      method: 'POST',
      data: { price, amount },
    }),
    invalidatesTags: ['ShopItems', 'ShopsList'],
  }),

  removeItemFromSale: builder.mutation({
    query: ({ inventoryItemId, amount }) => ({
      url: `/sale/inventory/${inventoryItemId}${amount != null ? `?amount=${amount}` : ''}`,
      method: 'DELETE',
    }),
    invalidatesTags: ['ShopItems', 'ShopsList'],
  }),

  updateSalePrice: builder.mutation({
    query: ({ inventoryItemId, price }) => ({
      url: `/sale/inventory/${inventoryItemId}/price`,
      method: 'PATCH',
      data: { price },
    }),
    invalidatesTags: (result, error, { locationSlug }) => [
      'ShopItems',
      { type: 'ShopsList', id: locationSlug || 'ALL' }
    ],
  }),

  // ═══ СОЗДАНИЕ/ОБНОВЛЕНИЕ ЛАВКИ ═══
  createCityShop: builder.mutation({
    query: ({ locationSlug } = {}) => ({
      url: '/city-shop/',
      method: 'POST',
      data: locationSlug ? { location_slug: locationSlug } : undefined,
    }),
    invalidatesTags: (result, error, args) => {
      const locationSlug = args?.locationSlug;
      return locationSlug
          ? [
              { type: 'CityShop', id: locationSlug },
              { type: 'ShopsList', id: locationSlug },
            ]
          : ['CityShop', 'ShopsList'];
    },
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  renewCityShopLicense: builder.mutation({
    query: ({ shopId } = {}) => ({
      url: `/city-shop/${shopId}/renewal`,
      method: 'POST',
    }),
    invalidatesTags: (result, error, args) => {
      const locationSlug = args?.locationSlug;
      return locationSlug
          ? [
              { type: 'CityShop', id: locationSlug },
              { type: 'ShopsList', id: locationSlug },
            ]
          : ['CityShop', 'ShopsList'];
    },
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  levelUpCityShop: builder.mutation({
    query: () => ({
      url: '/city-shop/level-up',
      method: 'POST',
    }),
    invalidatesTags: (result, error, args) => {
      const locationSlug = args?.locationSlug;
      return locationSlug
          ? [
              { type: 'CityShop', id: locationSlug },
              { type: 'ShopItems', id: locationSlug },
            ]
          : ['CityShop', 'ShopItems'];
    },
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  updateCityShopInfo: builder.mutation({
    query: ({ shopId, data }) => ({
      url: `/city-shop/${shopId}/info`,
      method: 'PATCH',
      data,
    }),
    invalidatesTags: (result, error, args) => {
      const tags = [
        'ShopsList',
        { type: 'CityShop', id: args?.locationSlug || 'LIST' },
        { type: 'CityShop', id: args?.shopId },
        { type: 'ShopsList', id: args?.locationSlug || 'ALL' },
      ];
      return tags;
    },
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  updateCityShopPhoto: builder.mutation({
    query: ({ shopId, photoId }) => ({
      url: `/city-shop/${shopId}/photo`,
      method: 'PATCH',
      data: { photo_id: photoId },
    }),
    invalidatesTags: (result, error, args) => {
      const tags = [
        'ShopsList',
        { type: 'CityShop', id: args?.locationSlug || 'LIST' },
        { type: 'CityShop', id: args?.shopId },
        { type: 'ShopsList', id: args?.locationSlug || 'ALL' },
      ];
      return tags;
    },
    async onQueryStarted(arg, { queryFulfilled, dispatch, getState }) {
      try {
        await queryFulfilled;
        await invalidateCharacter(dispatch, getState);
      } catch {
      // ошибку мутации показывает компонент через unwrap(); здесь только пост-успешная инвалидация
      }
    },
  }),

  renewTradeLicense: builder.mutation({
    query: () => ({
      url: '/trade-license/renew',
      method: 'POST',
    }),
    invalidatesTags: ['TradeLicense'],
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