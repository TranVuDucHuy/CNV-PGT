/**
 * ResultPane Component
 * Tất cả UI và logic của Result section
 */

"use client";

import React, { useState } from 'react';
import { Plus, Minus, Download } from 'lucide-react';

export default function ResultPane() {
  const [results, setResults] = useState<string[]>([]);

  const handleAdd = () => {
    const newResult = `Result ${results.length + 1}`;
    setResults([...results, newResult]);
  };

  const handleRemove = () => {
    if (results.length > 0) {
      setResults(results.slice(0, -1));
    }
  };

  const handleExport = () => {
    if (results.length > 0) {
      alert('Export feature coming soon!');
    }
  };

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Result</span>
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
            onClick={handleExport}
            title="Export"
            className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
          >
            <Download size={16} />
          </button>
        </div>
      </summary>

      <div className="p-3 space-y-2">
        {results.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-4">
            No results yet.
          </div>
        ) : (
          results.map((r, i) => (
            <div key={i} className="border p-2 rounded bg-white shadow-sm">
              {r}
            </div>
          ))
        )}
      </div>
    </details>
  );
}
