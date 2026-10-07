// app/providers/store/refreshSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { panelApi } from '../../../entities/character/api/panelApi';
import { checkUnreadMail } from '../../../entities/mail/store/mailSlice';

// Thunk для обновления всех данных
export const refreshAllData = createAsyncThunk(
  'refresh/refreshAllData',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      dispatch(panelApi.util.invalidateTags(['Panel']));

      // Проверяем почту
      await dispatch(checkUnreadMail()).unwrap();

      return {};
    } catch (error) {
      return rejectWithValue(error.response?.data || 'Ошибка обновления данных');
    }
  }
);

const initialState = {
  refreshing: false,
  error: null,
  lastRefresh: null
};

const refreshSlice = createSlice({
  name: 'refresh',
  initialState,
  reducers: {
    clearRefreshError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(refreshAllData.pending, (state) => {
        state.refreshing = true;
        state.error = null;
      })
      .addCase(refreshAllData.fulfilled, (state) => {
        state.refreshing = false;
        state.lastRefresh = Date.now();
      })
      .addCase(refreshAllData.rejected, (state, action) => {
        state.refreshing = false;
        state.error = action.payload;
      });
  }
});

export const { clearRefreshError } = refreshSlice.actions;

export const selectRefreshing = (state) => {
  if (!state || !state.refresh) {
    return false;
  }
  return state.refresh.refreshing === true;
};

export const selectRefreshError = (state) => {
  if (!state || !state.refresh) {
    return null;
  }
  return state.refresh.error || null;
};

export const selectLastRefresh = (state) => {
  if (!state || !state.refresh) {
    return null;
  }
  return state.refresh.lastRefresh || null;
};

export default refreshSlice.reducer;