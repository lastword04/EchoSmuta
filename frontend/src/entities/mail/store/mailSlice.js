import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { mailApi } from '../api/mailApi';

export const checkUnreadMail = createAsyncThunk(
  'mail/checkUnreadMail',
  async (_, { dispatch, rejectWithValue }) => {
    try {
      const response = await dispatch(mailApi.endpoints.getAllIsRead.initiate(undefined, { forceRefetch: true })).unwrap();
      return !response?.all_is_read; // true если есть непрочитанные
    } catch (error) {
      console.error('Ошибка при проверке писем:', error);
      return rejectWithValue(error.message || 'Ошибка проверки писем');
    }
  }
);

const mailSlice = createSlice({
  name: 'mail',
  initialState: {
    hasUnreadMessages: false,
    loading: false,
    error: null
  },
  reducers: {
    clearMailError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(checkUnreadMail.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(checkUnreadMail.fulfilled, (state, action) => {
        state.loading = false;
        state.hasUnreadMessages = action.payload;
      })
      .addCase(checkUnreadMail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { clearMailError } = mailSlice.actions;

export const selectHasUnreadMessages = (state) => state.mail?.hasUnreadMessages ?? false;
export const selectMailLoading = (state) => state.mail?.loading ?? false;
export const selectMailError = (state) => state.mail?.error ?? null;

export default mailSlice.reducer;