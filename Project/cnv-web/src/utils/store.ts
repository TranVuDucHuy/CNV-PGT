// store.ts
import { configureStore } from '@reduxjs/toolkit';
import appReducer from './appSlice'

export const store = configureStore({
  reducer: {
    app: appReducer, // Tên state sẽ là state.app
  },
});

// Xuất các type helper để dùng trong Component cho tiện
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;