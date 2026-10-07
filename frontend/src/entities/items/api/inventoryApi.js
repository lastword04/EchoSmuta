import { createApi } from '@reduxjs/toolkit/query/react';
import { itemApiInstance } from '../../../shared/api/axiosInstance';
import { createAxiosBaseQuery } from '../../../shared/api/baseQuery';

import { craftingEndpoints } from './endpoints/crafting';
import { shopEndpoints } from './endpoints/shop';
import { dealsEndpoints } from './endpoints/deals';
import { inventoryEndpoints } from './endpoints/inventory';

export const inventoryApi = createApi({
  reducerPath: 'inventoryApi',
  baseQuery: createAxiosBaseQuery(itemApiInstance),
  tagTypes: [
    'Inventory', 'ShopItems', 'ShopsList', 'StartedCrafting', 'WorkshopRecipes',
    'WorkshopStats', 'CraftingStatus', 'CraftingAction', 'CraftingLicense',
    'CityShop', 'TradeLicense', 'DealPartners', 'Deals', 'Deal', 'SalesHistory',
    'Recipes', 'MyRecipes', 'Item',
  ],
  endpoints: (builder) => ({
    // Собираем всё в один объект
    ...craftingEndpoints(builder),
    ...shopEndpoints(builder),
    ...dealsEndpoints(builder),
    ...inventoryEndpoints(builder),
  }),
});


export const {
  // Inventory & Items
  useGetCharacterItemsQuery,
  useGetMyEquipmentQuery,
  useGetItemBySlugQuery,
  useLazyGetItemBySlugQuery,
  useGetItemsFromLocationQuery,
  useUseItemMutation,
  useEquipItemMutation,
  useUnequipItemMutation,
  useUnpackKitMutation,

  // Crafting
  useGetStartedCraftingQuery,
  useGetStockRecipesQuery,
  useGetCityShopStatsQuery,
  useGetCraftingStatusQuery,
  useGetCraftingActionQuery,
  useLazyGetCraftingActionQuery,
  useGetCraftingLicenseStatusQuery,
  useStartNewCraftingMutation,
  useContinueCraftingMutation,
  useCancelExpiredCraftingMutation,
  useBuyRecipeMutation,
  useBuyCraftingLicenseMutation,
  useRenewCraftingLicenseMutation,
  
  // Shop
  useGetShopsListQuery,
  useGetSalesHistoryQuery,
  useGetRecipesQuery,
  useGetMyRecipesQuery,
  useGetCityShopByIdQuery,
  useGetCityShopByNumberQuery,
  useLazyGetCityShopByNumberQuery,
  useGetCityShopQuery,
  useGetTradeLicenseStatusQuery,
  useListItemToShopMutation,
  useWithdrawItemFromShopMutation,
  usePurchaseItemMutation,
  usePutItemOnSaleMutation,
  useRemoveItemFromSaleMutation,
  useUpdateSalePriceMutation,
  useCreateCityShopMutation,
  useRenewCityShopLicenseMutation,
  useLevelUpCityShopMutation,
  useUpdateCityShopInfoMutation,
  useUpdateCityShopPhotoMutation,
  useRenewTradeLicenseMutation,

  // Deals (добавлено)
  useGetNearbyPartnersQuery, useGetDealsQuery, useGetDealQuery,
  useCreateDealMutation, useAcceptDealMutation, useConfirmDealMutation,
  useCancelDealMutation, useSetDealDucatsMutation, useSetDealGoldMutation,
  useAddDealResourceMutation, useRemoveDealResourceMutation,
  useAddDealItemMutation, useRemoveDealItemMutation,
} = inventoryApi;

