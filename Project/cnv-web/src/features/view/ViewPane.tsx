/**
 * ViewPane Component
 * Checkbox options cho việc hiển thị views
 */

"use client";

import React, { useState } from 'react';

export default function ViewPane() {
  const [checked, setChecked] = useState({
    bin: false,
    segment: false,
    aberration: false,
    trash: false,
    report: false,
  });

  const toggleCheck = (key: keyof typeof checked) => {
    setChecked({ ...checked, [key]: !checked[key] });
    console.log(`Toggled ${key}:`, !checked[key]);
  };

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer">
        View
      </summary>
      <div className="p-3 space-y-2">
        {Object.keys(checked).map((key) => (
          <label key={key} className="block">
            <input
              type="checkbox"
              checked={checked[key as keyof typeof checked]}
              onChange={() => toggleCheck(key as keyof typeof checked)}
              className="mr-2"
            />
            {key
              .replace(/([A-Z])/g, " $1")
              .replace(/^./, (c) => c.toUpperCase())}
          </label>
        ))}
      </div>
    </details>
  );
}
