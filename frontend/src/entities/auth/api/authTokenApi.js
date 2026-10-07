import { createApi } from '@reduxjs/toolkit/query/react';
import { authProtectedApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const authTokenApi = createApi({
  reducerPath: 'authTokenApi',
  baseQuery: createAxiosBaseQuery(authProtectedApiInstance),
  endpoints: (builder) => ({
    getToken: builder.query({
      query: () => ({
        url: '/token',
        method: 'GET',
      }),
    }),
  }),
});

export const { useGetTokenQuery } = authTokenApi;