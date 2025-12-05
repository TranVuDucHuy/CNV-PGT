// viewHandle.ts
"use client";

import React, { createContext, useContext, useState } from "react";

export type ViewChecked = {
  bin: boolean;
  segment: boolean;
  chart: boolean;
  report: boolean;
  cycleReport: boolean;
};

export interface ViewContextValue {
  checked: ViewChecked;
  setChecked: (c: ViewChecked | ((prev: ViewChecked) => ViewChecked)) => void;
  toggle: (key: keyof ViewChecked) => void;
}

// const defaultChecked: ViewChecked = {
//   bin: false,
//   segment: false,
//   chart: false,
//   report: false,
//   cycleReport: false,
// };

// // export explicitly in case other files reference ViewContext directly
// export const ViewContext = createContext<ViewContextValue | undefined>(
//   undefined
// );

// export function ViewProvider(props: { children?: React.ReactNode }) {
//   const [checked, setChecked] = useState<ViewChecked>(defaultChecked);

//   const toggle = (key: keyof ViewChecked) =>
//     setChecked((prev) => ({ ...prev, [key]: !prev[key] }));

//   // NOTE: no JSX here — use React.createElement to avoid needing .tsx
//   return React.createElement(
//     ViewContext.Provider,
//     { value: { checked, setChecked, toggle } },
//     props.children ?? null
//   );
// }

export function useViewHandle() {
  // const ctx = useContext(ViewContext);
  // if (!ctx) {
  //   throw new Error("useViewHandle must be used within a ViewProvider");
  // }
  // return ctx;
}
