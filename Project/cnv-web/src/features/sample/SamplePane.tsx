/**
 * SamplePane Component
 * Tất cả UI và logic của Sample section
 */

"use client";

import React, { useState } from 'react';
import { Plus, Minus, Edit3 } from 'lucide-react';

export default function SamplePane() {
  const [samples, setSamples] = useState<string[]>([]);

  const handleAdd = () => {
    const newSample = `Sample ${samples.length + 1}`;
    setSamples([...samples, newSample]);
  };

  const handleRemove = () => {
    if (samples.length > 0) {
      setSamples(samples.slice(0, -1));
    }
  };

  const handleEdit = () => {
    if (samples.length > 0) {
      const newSamples = [...samples];
      newSamples[newSamples.length - 1] += " (edited)";
      setSamples(newSamples);
    }
  };

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Sample</span>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAdd}
            title="Add"
            className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={handleRemove}
            title="Remove"
            className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
          >
            <Minus size={16} />
          </button>
          <button
            onClick={handleEdit}
            title="Edit"
            className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
          >
            <Edit3 size={16} />
          </button>
        </div>
      </summary>

      <div className="p-3 space-y-2">
        {samples.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-4">
            No samples yet. Click + to add one.
          </div>
        ) : (
          samples.map((s, i) => (
            <div key={i} className="border p-2 rounded bg-white shadow-sm">
              {s}
            </div>
          ))
        )}
      </div>
    </details>
  );
}
