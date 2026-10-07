import { createApi } from '@reduxjs/toolkit/query/react';
import { authProtectedApiInstance } from '../../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../../shared/api/baseQuery';

export const authAdminApi = createApi({
  reducerPath: 'authAdminApi',
  baseQuery: createAxiosBaseQuery(authProtectedApiInstance),
  tagTypes: ['AdminAuthLog'],
  endpoints: (builder) => ({
    getAuthLogs: builder.query({
      query: (params) => ({ url: '/admin/auth-logs', params }),
      providesTags: ['AdminAuthLog'],
    }),
  }),
});

export const {
  useGetAuthLogsQuery,
} = authAdminApi;