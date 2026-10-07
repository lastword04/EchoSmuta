import { createApi } from '@reduxjs/toolkit/query/react';
import { authApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const authApi = createApi({
  reducerPath: 'authApi',
  baseQuery: createAxiosBaseQuery(authApiInstance),
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: '/login',
        method: 'POST',
        data: credentials,
      }),
    }),

    register: builder.mutation({
      query: (registrationForm) => ({
        url: '/register',
        method: 'POST',
        data: registrationForm,
      }),
    }),

    resetPassword: builder.mutation({
      query: (resetData) => ({
        url: '/reset-password',
        method: 'POST',
        data: resetData,
      }),
    }),

    confirmResetPassword: builder.mutation({
      query: (confirmResetData) => ({
        url: '/confirm-reset-password',
        method: 'POST',
        data: confirmResetData,
      }),
    }),

    loginToForum: builder.mutation({
      query: (credentials) => ({
        url: '/login-forum',
        method: 'POST',
        data: credentials,
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useResetPasswordMutation,
  useConfirmResetPasswordMutation,
  useLoginToForumMutation,
} = authApi;