import { createSlice } from '@reduxjs/toolkit';

/**
 * UI-состояние дома для текущего персонажа.
 *
 * houseOverride — оптимистичный payload дома, временно перекрывающий
 * server-base из getHousesStatus. Ставится при enter / guest_accepted /
 * install / uninstall / wallpaper. Сбрасывается при выходе из дома
 * и при WS-событиях, которые инициировал не я (см. useEconomyWebSocket).
 */
const initialState = { houseOverride: null };

const houseUiSlice = createSlice({
  name: 'houseUi',
  initialState,
  reducers: {
    setHouseOverride: (state, action) => {
      state.houseOverride = action.payload;
    },
    patchHouseOverride: (state, action) => {
      if (!state.houseOverride) return;
      state.houseOverride = { ...state.houseOverride, ...action.payload };
    },
    clearHouseOverride: (state) => {
      state.houseOverride = null;
    },
  },
});

export const { setHouseOverride, patchHouseOverride, clearHouseOverride } = houseUiSlice.actions;
export default houseUiSlice.reducer;