// entities/forum/store/pendingCommentSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  commentText: ''
};

const pendingCommentSlice = createSlice({
  name: 'pendingComment',
  initialState,
  reducers: {
    setPendingCommentText: (state, action) => {
      state.commentText = action.payload;
    },
    clearPendingCommentText: (state) => {
      state.commentText = '';
    }
  }
});

export const { setPendingCommentText, clearPendingCommentText } = pendingCommentSlice.actions;
export default pendingCommentSlice.reducer;