import { createApi } from '@reduxjs/toolkit/query/react';
import { housesApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

export const housesApi = createApi({
  reducerPath: 'housesApi',
  baseQuery: createAxiosBaseQuery(housesApiInstance),
  tagTypes: ['Houses', 'HouseFurniture', 'HousesGuests'],
  endpoints: (builder) => ({
    getHousesStatus: builder.query({
      query: (_characterId) => ({ url: '/status', method: 'GET' }),
      providesTags: ['Houses'],
      keepUnusedDataFor: 60,
      refetchOnMountOrArgChange: true,
      refetchOnFocus: true,
      keepPreviousData: true,
    }),

    buyHouse: builder.mutation({
      query: () => ({ url: '/buy', method: 'POST' }),
      invalidatesTags: ['Houses'],
    }),

    enterHouse: builder.mutation({
      query: (houseId) => ({ url: '/enter', method: 'POST', data: { house_id: houseId } }),
      invalidatesTags: ['Houses'],
    }),

    exitHouse: builder.mutation({
      query: () => ({ url: '/exit', method: 'POST' }),
      invalidatesTags: ['Houses'],
    }),

    getMyFurniture: builder.query({
      query: (_characterId) => ({ url: '/furniture', method: 'GET' }),
      providesTags: ['HouseFurniture'],
      refetchOnFocus: true,
    }),

    getHouseFurniture: builder.query({
      query: (houseId) => ({ url: `/${houseId}/furniture`, method: 'GET' }),
      providesTags: ['HouseFurniture'],
    }),

    installFurniture: builder.mutation({
      query: ({ houseId, inventoryItemId }) => ({
        url: '/install-furniture',
        method: 'POST',
        data: { house_id: houseId, inventory_item_id: inventoryItemId },
      }),
      invalidatesTags: ['Houses', 'HouseFurniture'],
    }),

    uninstallFurniture: builder.mutation({
      query: ({ inventoryItemId }) => ({
        url: '/uninstall-furniture',
        method: 'POST',
        data: { inventory_item_id: inventoryItemId },
      }),
      invalidatesTags: ['Houses', 'HouseFurniture'],
    }),

    updateHouseWallpaper: builder.mutation({
      query: ({ houseId, wallpaperPhotoId }) => ({
        url: `/${houseId}/wallpaper`,
        method: 'PATCH',
        data: { wallpaper_photo_id: wallpaperPhotoId },
      }),
      invalidatesTags: ['Houses'],
    }),

    knockHouse: builder.mutation({
      query: ({ houseNumber }) => ({
        url: '/knock',
        method: 'POST',
        data: { house_number: houseNumber },
      }),
      invalidatesTags: ['Houses'],
    }),

    getHouseGuests: builder.query({
      query: (houseId) => ({ url: `/${houseId}/guests`, method: 'GET' }),
      providesTags: ['HousesGuests'],
    }),

    acceptGuestRequest: builder.mutation({
      query: (requestId) => ({ url: `/guest-requests/${requestId}/accept`, method: 'POST' }),
      invalidatesTags: ['Houses', 'HousesGuests', 'Character'],
    }),

    rejectGuestRequest: builder.mutation({
      query: (requestId) => ({ url: `/guest-requests/${requestId}/reject`, method: 'POST' }),
      invalidatesTags: ['HousesGuests'],
    }),

    kickHouseGuest: builder.mutation({
      query: (characterId) => ({ url: `/guests/${characterId}/kick`, method: 'POST' }),
      invalidatesTags: ['Houses', 'HousesGuests', 'Character'],
    }),
  }),
});

export const {
  useGetHousesStatusQuery,
  useBuyHouseMutation,
  useEnterHouseMutation,
  useExitHouseMutation,
  useGetMyFurnitureQuery,
  useGetHouseFurnitureQuery,
  useInstallFurnitureMutation,
  useUninstallFurnitureMutation,
  useUpdateHouseWallpaperMutation,
  useKnockHouseMutation,
  useGetHouseGuestsQuery,
  useAcceptGuestRequestMutation,
  useRejectGuestRequestMutation,
  useKickHouseGuestMutation,
} = housesApi;