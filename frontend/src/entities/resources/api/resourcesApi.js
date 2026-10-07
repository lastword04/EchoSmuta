import { createApi } from '@reduxjs/toolkit/query/react';
import { resourceApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const resourcesApi = createApi({
  reducerPath: 'resourcesApi',
  baseQuery: createAxiosBaseQuery(resourceApiInstance),
  tagTypes: ['Resources', 'MiningStatus', 'MiningAction'],
  endpoints: (builder) => ({
    getResources: builder.query({
      query: (locationSlug) => ({
        url: '/',
        method: 'GET',
        params: locationSlug ? { location_slug: locationSlug } : undefined
      }),
      providesTags: (result, error, locationSlug) =>
        locationSlug
          ? [{ type: 'Resources', id: locationSlug }]
          : ['Resources'],
    }),

    getMyResources: builder.query({
      query: () => ({ url: '/my', method: 'GET' }),
      providesTags: ['Resources'],
    }),

    getResourceBySlug: builder.query({
      query: (resourceSlug) => ({
        url: `/${resourceSlug}`,
        method: 'GET',
      }),
      providesTags: (result, error, resourceSlug) => [{ type: 'Resources', id: resourceSlug }],
    }),

    getMiningStatus: builder.query({
      query: () => ({ url: '/mining/status', method: 'GET' }),
      providesTags: ['MiningStatus'],
    }),

    getMiningResource: builder.query({
      query: (resourceId) => ({
        url: `/mining/actions/${resourceId}`,
        method: 'GET',
      }),
      providesTags: (result, error, resourceId) => [{ type: 'MiningAction', id: resourceId }],
    }),

    mineResource: builder.mutation({
      query: (data) => ({
        url: '/mining/actions',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Resources', 'MiningStatus'],
    }),
  }),
});

export const {
  useGetResourcesQuery,
  useGetMyResourcesQuery,
  useGetResourceBySlugQuery,
  useGetMiningStatusQuery,
  useGetMiningResourceQuery,
  useMineResourceMutation,
} = resourcesApi;