import { Result } from "@/types/result";
import { ViewChecked } from "@/features/view/viewHandle";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface AppState {
  results: Result[];
  viewChecked: ViewChecked;
  selectedResults: string[];
}

// Giá trị mặc định ban đầu
const initialState: AppState = {
  results: [],
  viewChecked: {
    bin: false,
    segment: false,
    report: false,
    table: false,
    cycleReport: false,
  },
  selectedResults: [],
};

const appSlice = createSlice({
  name: "app",
  initialState,
  reducers: {
    // 1. Action để cập nhật toàn bộ danh sách Results
    setResults: (state, action: PayloadAction<Result[]>) => {
      state.results = action.payload;
    },

    // 2. Action để thêm một Result vào danh sách
    addResult: (state, action: PayloadAction<Result>) => {
      state.results.push(action.payload);
    },

    // 3. Action để bật/tắt một tùy chọn cụ thể trong ViewChecked
    toggleViewOption: (state, action: PayloadAction<keyof ViewChecked>) => {
      const key = action.payload;
      state.viewChecked[key] = !state.viewChecked[key];
    },

    // 4. Action để set giá trị cụ thể cho một key trong ViewChecked (nếu không muốn toggle)
    setViewOption: (
      state,
      action: PayloadAction<{ key: keyof ViewChecked; value: boolean }>
    ) => {
      const { key, value } = action.payload;
      state.viewChecked[key] = value;
    },

    // 5. Action để reset toàn bộ viewChecked về false (nếu cần)
    resetViewChecked: (state) => {
      state.viewChecked = initialState.viewChecked;
    },

    toggleResultSelection: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      const index = state.selectedResults.indexOf(id);

      if (index !== -1) {
        // Nếu đã có ID trong danh sách -> Xóa đi (Bỏ chọn)
        state.selectedResults.splice(index, 1);
      } else {
        // Nếu chưa có -> Thêm vào (Chọn)
        state.selectedResults.push(id);
      }
    },

    // 2. Set cứng danh sách chọn (dùng cho tính năng "Select All" hoặc "Clear All")
    setSelectedResults: (state, action: PayloadAction<string[]>) => {
      state.selectedResults = action.payload;
    },

    // 3. Clear toàn bộ selection (tiện ích nhanh)
    clearSelection: (state) => {
      state.selectedResults = [];
    },
  },
});

export const {
  setResults,
  addResult,
  toggleViewOption,
  setViewOption,
  resetViewChecked,
  toggleResultSelection,
  setSelectedResults,
  clearSelection,
} = appSlice.actions;
export default appSlice.reducer;
