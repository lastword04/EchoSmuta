import { createApi } from '@reduxjs/toolkit/query/react';
import { miningApiInstance } from '../../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../../shared/api/baseQuery';

export const miningAdminApi = createApi({
  reducerPath: 'miningAdminApi',
  baseQuery: createAxiosBaseQuery(miningApiInstance),
  tagTypes: ['MiningItem', 'MiningResource', 'MiningCharacter', 'MiningInventory', 'MiningLog', 'MiningDeal'],
  endpoints: (builder) => ({
    // ─────────── ITEMS ───────────
    listAdminItems: builder.query({
      query: (params) => ({ url: '/items', params }),
      providesTags: ['MiningItem'],
    }),
    getAdminItemTypes: builder.query({
      query: () => '/item-types',
    }),
    giveItem: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/items/give`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['MiningItem', 'MiningInventory'],
    }),
    takeItem: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/items/take`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['MiningItem', 'MiningInventory'],
    }),
  
    getCompletingDeals: builder.query({
      query: (limit = 50) => ({
        url: '/deals/completing',
        params: { limit },
      }),
      providesTags: ['MiningDeal'],
    }),

    // ─────────── RESOURCES ───────────
    listAdminResources: builder.query({
      query: (params) => ({ url: '/resources', params }),
      providesTags: ['MiningResource'],
    }),
    getAdminResourceCategories: builder.query({
      query: () => '/resource-categories',
    }),
    giveResource: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/resources/give`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['MiningResource', 'MiningInventory'],
    }),
    takeResource: builder.mutation({
      query: ({ characterId, data }) => ({
        url: `/characters/${characterId}/resources/take`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['MiningResource', 'MiningInventory'],
    }),

    // ─────────── CHARACTERS / INVENTORY / MONEY / LOGS ───────────
    listAdminCharacters: builder.query({
      query: (params) => ({ url: '/characters', params }),
      providesTags: ['MiningCharacter'],
    }),
    getAdminCharacter: builder.query({
      query: (characterId) => `/characters/${characterId}`,
      providesTags: ['MiningCharacter'],
    }),
    getAdminInventory: builder.query({
      query: (characterId) => `/characters/${characterId}/inventory`,
      providesTags: ['MiningInventory'],
    }),
    getAdminCharacterResources: builder.query({
      query: (characterId) => `/characters/${characterId}/resources`,
      providesTags: ['MiningInventory'],
    }),
    getAdminLogs: builder.query({
      query: (params) => ({ url: '/logs', params }),
      providesTags: ['MiningLog'],
    }),
    addMoney: builder.mutation({
      queryFn: async ({ characterId, amounts, reason }) => {
        const entries = ['ducats', 'gold'].filter((currency) => amounts[currency] !== '' && amounts[currency] != null);
        const results = await Promise.allSettled(
          entries.map(async (currency) => {
            const res = await miningApiInstance.post(`/characters/${characterId}/money/add`, {
              currency,
              amount: Number(amounts[currency]),
              reason: reason || undefined,
            });
            return { currency, data: res.data };
          })
        );
        return { data: results.map((r, i) => ({ currency: entries[i], status: r.status, value: r.value?.data, error: r.reason })) };
      },
      invalidatesTags: ['MiningCharacter'],
    }),
    setMoney: builder.mutation({
      queryFn: async ({ characterId, amounts, reason }) => {
        const entries = ['ducats', 'gold'].filter((currency) => amounts[currency] !== '' && amounts[currency] != null);
        const results = await Promise.allSettled(
          entries.map(async (currency) => {
            const res = await miningApiInstance.post(`/characters/${characterId}/money/set`, {
              currency,
              amount: Number(amounts[currency]),
              reason: reason || undefined, // ← добавляем reason
            });
            return { currency, data: res.data };
          })
        );
        return { data: results.map((r, i) => ({ currency: entries[i], status: r.status, value: r.value?.data, error: r.reason })) };
      },
      invalidatesTags: ['MiningCharacter'],
    }),
  }),
});

export const {
  useListAdminItemsQuery,
  useGetAdminItemTypesQuery,
  useGiveItemMutation,
  useTakeItemMutation,
  useGetCompletingDealsQuery,
  useListAdminResourcesQuery,
  useGetAdminResourceCategoriesQuery,
  useGiveResourceMutation,
  useTakeResourceMutation,
  useListAdminCharactersQuery,
  useGetAdminCharacterQuery,
  useGetAdminInventoryQuery,
  useGetAdminCharacterResourcesQuery,
  useGetAdminLogsQuery,
  useAddMoneyMutation,
  useSetMoneyMutation,
} = miningAdminApi;