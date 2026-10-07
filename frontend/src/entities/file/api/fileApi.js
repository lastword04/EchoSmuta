import { createApi } from '@reduxjs/toolkit/query/react';
import { fileApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

// Утилита для генерации template_name (не API-вызов)
export const generateTemplateName = (race, gender) => {
  if (!race || !gender) return null;
  return `${race}_${gender}`;
};

export const fileApi = createApi({
  reducerPath: 'fileApi',
  baseQuery: createAxiosBaseQuery(fileApiInstance),
  endpoints: (builder) => ({
    getFileByTemplateName: builder.query({
      query: (templateName) => ({
        url: `/template_name/${templateName}`,
        method: 'GET',
      }),
    }),

    uploadFile: builder.mutation({
      query: ({ file, subdir = 'forum' }) => {
        const formData = new FormData();
        formData.append('data', JSON.stringify({ subdir, filename: file.name }));
        formData.append('file', file);
        
        return {
          url: '/',
          method: 'POST',
          data: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        };
      },
    }),

    uploadFilesBatch: builder.mutation({
      query: ({ files, subdir = 'forum' }) => {
        const formData = new FormData();
        
        files.forEach((file) => {
          formData.append('files', file);
        });
        
        const requestData = {
          files: files.map(file => ({
            subdir,
            filename: file.name
          }))
        };
        
        formData.append('data', JSON.stringify(requestData));
        
        return {
          url: '/batch/',
          method: 'POST',
          data: formData,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        };
      },
      transformResponse: (response) => response.files,
    }),

    deleteFile: builder.mutation({
      query: (fileId) => ({
        url: `/${fileId}`,
        method: 'DELETE',
      }),
      transformResponse: () => true,
    }),
  }),
});

export const {
  useGetFileByTemplateNameQuery,
  useUploadFileMutation,
  useUploadFilesBatchMutation,
  useDeleteFileMutation,
} = fileApi;