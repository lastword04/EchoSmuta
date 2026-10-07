import { createApi } from '@reduxjs/toolkit/query/react';
import { economyApiInstance } from '../../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../../shared/api/baseQuery'; 

export const economyAdminApi = createApi({
  reducerPath: 'economyAdminApi',
  baseQuery: createAxiosBaseQuery(economyApiInstance),
  tagTypes: ['AdminResource', 'AdminTransaction', 'AdminStatistic'],
  endpoints: (builder) => ({
    getResources: builder.query({
      query: () => '/admin/resources',
      providesTags: ['AdminResource'],
    }),
    getTransactions: builder.query({
      query: (filters) => {
        const cleanParams = {};
        if (filters) {
          Object.entries(filters).forEach(([key, value]) => {
            if (value !== '' && value !== null && value !== undefined) {
              cleanParams[key] = value;
            }
          });
        }
        return { url: '/admin/transactions', params: cleanParams };
      },
      providesTags: ['AdminTransaction'],
    }),
    getStatistics: builder.query({
      query: ({ startDate, endDate } = {}) => {
        const cleanParams = {};
        if (startDate) cleanParams.start_date = startDate;
        if (endDate) cleanParams.end_date = endDate;
        return { url: '/admin/statistics', params: cleanParams };
      },
      providesTags: ['AdminStatistic'],
    }),
    setStock: builder.mutation({
      query: ({ resourceId, body }) => ({
        url: `/admin/resources/${resourceId}/stock`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['AdminResource', 'AdminTransaction'],
    }),
    setPrices: builder.mutation({
      query: ({ resourceId, body }) => ({
        url: `/admin/resources/${resourceId}/prices`,
        method: 'POST',
        body,
      }),
      invalidatesTags: ['AdminResource', 'AdminTransaction'],
    }),
    recalculatePrices: builder.mutation({
      query: (force = true) => ({
        url: '/admin/prices/recalculate',
        method: 'POST',
        body: { force },
      }),
      invalidatesTags: ['AdminResource'],
    }),    
  }),
});

export const {
  useGetResourcesQuery,
  useGetTransactionsQuery,
  useGetStatisticsQuery,  
  useSetStockMutation,
  useSetPricesMutation,
  useRecalculatePricesMutation,
} = economyAdminApi;