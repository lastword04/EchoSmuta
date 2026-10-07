import { createApi } from '@reduxjs/toolkit/query/react';
import { characterApiInstance } from '../../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../../shared/api/baseQuery';

export const characterAdminApi = createApi({
  reducerPath: 'characterAdminApi',
  baseQuery: createAxiosBaseQuery(characterApiInstance),
  tagTypes: ['AdminCharacter', 'AdminLedger', 'AdminTradePrivileges'],
  endpoints: (builder) => ({
    searchCharacters: builder.query({
      query: (params) => ({ url: '/admin/characters/search', params }),
      providesTags: ['AdminCharacter'],
    }),
    getCharacter: builder.query({
      query: (characterId) => `/admin/characters/${characterId}`,
      providesTags: ['AdminCharacter'],
    }),
    getCurrencyOperations: builder.query({
      query: (filters) => {
        const params = {};
        Object.entries(filters || {}).forEach(([key, value]) => {
          if (value !== '' && value !== null && value !== undefined) params[key] = value;
        });
        return { url: '/admin/characters/currency-operations', params };
      },
      providesTags: ['AdminLedger'],
    }),
    changeDucats: builder.mutation({
      query: ({ characterId, amount, reason }) => ({
        url: `/admin/characters/${characterId}/ducats`,
        method: 'POST',
        body: { amount, reason },
      }),
      invalidatesTags: ['AdminLedger', 'AdminCharacter'],
    }),
    getTradePrivileges: builder.query({
      query: (characterId) => `/admin/characters/${characterId}/trade-privileges`,
      providesTags: ['AdminTradePrivileges'],
    }),
    updateTradePrivileges: builder.mutation({
      query: ({ characterId, enabled }) => ({
        url: `/admin/characters/${characterId}/trade-privileges`,
        method: 'PATCH',
        body: { gold_trade_enabled: enabled },
      }),
      invalidatesTags: ['AdminTradePrivileges'],
    }),
    banCharacter: builder.mutation({
      query: ({ characterId, reason }) => ({
        url: `/admin/characters/${characterId}/ban`,
        method: 'POST',
        body: { reason },
      }),
      invalidatesTags: ['AdminCharacter'],
    }),
    unbanCharacter: builder.mutation({
      query: (characterId) => ({
        url: `/admin/characters/${characterId}/unban`,
        method: 'POST',
      }),
      invalidatesTags: ['AdminCharacter'],
    }),
  }),
});

export const {
  useSearchCharactersQuery,
  useGetCharacterQuery,
  useGetCurrencyOperationsQuery,
  useChangeDucatsMutation,
  useGetTradePrivilegesQuery,
  useUpdateTradePrivilegesMutation,
  useBanCharacterMutation,
  useUnbanCharacterMutation,
} = characterAdminApi;