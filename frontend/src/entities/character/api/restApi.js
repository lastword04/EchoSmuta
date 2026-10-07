import { createApi } from '@reduxjs/toolkit/query/react';
import { restApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const restApi = createApi({
  reducerPath: 'restApi',
  baseQuery: createAxiosBaseQuery(restApiInstance),
  tagTypes: ['Rest'],
  endpoints: (builder) => ({
    getRestStatus: builder.query({
      query: () => ({
        url: '/status',
        method: 'GET',
      }),
      providesTags: ['Rest'],
      keepUnusedDataFor: 60,
      refetchOnMountOrArgChange: true,
    }),

    rentRoom: builder.mutation({
      query: (days) => ({
        url: '/rent',
        method: 'POST',
        data: { days },
      }),
      
    }),

    exitRoom: builder.mutation({
      query: () => ({
        url: '/exit',
        method: 'POST',
      }),
      
    }),

    enterRoom: builder.mutation({
      query: () => ({
        url: '/enter',
        method: 'POST',
      }),
      
    }),

    syncExpiry: builder.mutation({
      query: () => ({
        url: '/sync-expiry',
        method: 'POST',
      }),
      invalidatesTags: ['Rest'],
    }),
  }),
});

export const {
  useGetRestStatusQuery,
  useRentRoomMutation,
  useExitRoomMutation,
  useEnterRoomMutation,
  useSyncExpiryMutation,
} = restApi;