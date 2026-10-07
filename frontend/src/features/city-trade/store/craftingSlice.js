// craftingSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  lastCraftingId: null,
  locationSlug: null,
  workshopLocationSlug: null,
  shouldReset: false,
};
const craftingSlice = createSlice({
  name: 'crafting',
  initialState,
  reducers: {
    setLastCrafting: (state, action) => {
      const { lastCraftingId = null, locationSlug = null, workshopLocationSlug = null } = action.payload || {};
      state.lastCraftingId = lastCraftingId;
      state.locationSlug = locationSlug;
      state.workshopLocationSlug = workshopLocationSlug;
      state.shouldReset = false;
    },
    clearLastCrafting: (state) => {
      state.lastCraftingId = null;
      state.locationSlug = null;
      state.workshopLocationSlug = null;
      state.shouldReset = true;
    },
    resetCraftingFlag: (state) => {
      state.shouldReset = false;
    },
  },
});

export const { setLastCrafting, clearLastCrafting, resetCraftingFlag } = craftingSlice.actions;
export default craftingSlice.reducer;