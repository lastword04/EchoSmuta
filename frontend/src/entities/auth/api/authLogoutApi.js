import { createApi } from '@reduxjs/toolkit/query/react';
import { authProtectedApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const authLogoutApi = createApi({
  reducerPath: 'authLogoutApi',
  baseQuery: createAxiosBaseQuery(authProtectedApiInstance),
  endpoints: (builder) => ({
    logout: builder.mutation({
      query: (data) => ({
        url: '/logout',
        method: 'POST',
        data,
      }),
    }),
  }),
});

export const { useLogoutMutation } = authLogoutApi;