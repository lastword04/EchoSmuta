import { createApi } from '@reduxjs/toolkit/query/react';
import { mailApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const mailApi = createApi({
  reducerPath: 'mailApi',
  baseQuery: createAxiosBaseQuery(mailApiInstance),
  tagTypes: ['Mail', 'MailSettings'],
  endpoints: (builder) => ({
    // ═══ QUERIES ═══
    getInbox: builder.query({
      query: ({ limit = 10, offset = 0 } = {}) => ({
        url: '/',
        method: 'GET',
        params: { limit, offset },
      }),
      providesTags: ['Mail'],
      keepUnusedDataFor: 5 * 60,
    }),

    getSent: builder.query({
      query: ({ limit = 10, offset = 0 } = {}) => ({
        url: '/my',
        method: 'GET',
        params: { limit, offset },
      }),
      providesTags: ['Mail'],
      keepUnusedDataFor: 5 * 60,
    }),

    getMailSettings: builder.query({
      query: () => ({
        url: '/settings',
        method: 'GET',
      }),
      providesTags: ['MailSettings'],
    }),

    getAllIsRead: builder.query({
      query: () => ({
        url: '/read',
        method: 'GET',
      }),
      keepUnusedDataFor: 60,
    }),

    // ═══ MUTATIONS ═══
    sendMail: builder.mutation({
      query: (data) => ({
        url: '/',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Mail'],
    }),

    deleteInboxMail: builder.mutation({
      query: (mailId) => ({
        url: `/${mailId}/recipient`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Mail'],
    }),

    deleteSentMail: builder.mutation({
      query: (mailId) => ({
        url: `/${mailId}/sender`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Mail'],
    }),

    blockSendMessage: builder.mutation({
      query: () => ({
        url: '/settings',
        method: 'POST',
      }),
      invalidatesTags: ['MailSettings'],
    }),

    unblockSendMessage: builder.mutation({
      query: () => ({
        url: '/settings',
        method: 'DELETE',
      }),
      invalidatesTags: ['MailSettings'],
    }),
  }),
});

export const {
  useGetInboxQuery,
  useGetSentQuery,
  useGetMailSettingsQuery,
  useGetAllIsReadQuery,
  useSendMailMutation,
  useDeleteInboxMailMutation,
  useDeleteSentMailMutation,
  useBlockSendMessageMutation,
  useUnblockSendMessageMutation,
} = mailApi;