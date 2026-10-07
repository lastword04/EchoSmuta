import { createApi } from '@reduxjs/toolkit/query/react';
import { characterApiInstance } from '../../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../../shared/api/baseQuery';

export const usersAdminApi = createApi({
  reducerPath: 'usersAdminApi',
  baseQuery: createAxiosBaseQuery(characterApiInstance),
  tagTypes: ['AdminUser', 'AdminCharacter'],
  endpoints: (builder) => ({
    getCharactersByUser: builder.query({
      query: (userId) => `/admin/users/${userId}/characters`,
      providesTags: ['AdminUser'],
    }),
    banAllByUser: builder.mutation({
      query: (userId) => ({
        url: `/admin/users/${userId}/ban-all`,
        method: 'POST',
      }),
      invalidatesTags: ['AdminUser', 'AdminCharacter'],
    }),
    unbanAllByUser: builder.mutation({
      query: (userId) => ({
        url: `/admin/users/${userId}/unban-all`,
        method: 'POST',
      }),
      invalidatesTags: ['AdminUser', 'AdminCharacter'],
    }),
  }),
});

export const {
  useGetCharactersByUserQuery,
  useBanAllByUserMutation,
  useUnbanAllByUserMutation,
} = usersAdminApi;