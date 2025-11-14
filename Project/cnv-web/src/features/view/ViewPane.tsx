// ViewPane.tsx
"use client";

import React from "react";
import { useViewHandle } from "./viewHandle";

export default function ViewPane() {
  const { checked, toggle } = useViewHandle();

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer">
        View
      </summary>
      <div className="p-3 space-y-2">
        {(
          Object.keys(checked) as Array<keyof typeof checked>
        ).map((key) => (
          <label key={key} className="block">
            <input
              type="checkbox"
              checked={checked[key]}
              onChange={() => toggle(key)}
              className="mr-2"
            />
            {key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase())}
          </label>
        ))}
      </div>
    </details>
  );
}
