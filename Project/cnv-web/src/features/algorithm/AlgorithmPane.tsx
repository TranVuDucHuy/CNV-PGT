/**
 * AlgorithmPane Component
 * Tất cả UI và logic của Algorithm section
 */

"use client";

import React, { useState } from 'react';
import { Plus, Minus, StepForward } from 'lucide-react';
import { useAlgorithms } from './useAlgorithms';
import AlgorithmDetail from '@/components/AlgorithmDetail';

export default function AlgorithmPane() {
  const { algorithms, loading, deleteAlgorithm, loadAlgorithms } = useAlgorithms();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());

  const handleAdd = () => {
    setDialogOpen(true);
  };

  const handleDelete = async () => {
    if (selectedIds.size === 0) return;
    const idsToDelete = Array.from(selectedIds);
    await Promise.all(
      idsToDelete
        .filter((id) => id !== undefined && id !== null)
        .map(async (id) => {
          // delete one by one to let hook/state stay in sync
          await deleteAlgorithm(id as any);
        })
    );
    setSelectedIds(new Set());
    // Ensure list is fresh
    await loadAlgorithms();
  };

  const toggleSelect = (id: string | number | undefined) => {
    if (id === undefined || id === null) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleRun = () => {
    if (algorithms.length > 0) {
      console.log('Running algorithm:', algorithms[algorithms.length - 1]);
      alert('Algorithm execution feature coming soon!');
    }
  };

  return (
    <>
      <details open className="border rounded-md">
        <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
          <span>Algorithm</span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleAdd}
              title="Add Algorithm"
              className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
            >
              <Plus size={16} />
            </button>
            <button
              onClick={handleDelete}
              title="Delete Selected"
              className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
            >
              <Minus size={16} />
            </button>
            {/* Edit is not supported by backend currently */}
            <button
              onClick={handleRun}
              title="Run Algorithm"
              className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
            >
              <StepForward size={16} />
            </button>
          </div>
        </summary>

        <div className="p-3 space-y-2">
          {loading ? (
            <div className="text-gray-500 text-sm text-center py-4">
              Loading algorithms...
            </div>
          ) : algorithms.length === 0 ? (
            <div className="text-gray-500 text-sm text-center py-4">
              No algorithms yet. Click + to add one.
            </div>
          ) : (
            algorithms.map((algo) => {
              const isSelected = algo.id !== undefined && selectedIds.has(algo.id);
              return (
              <div
                key={algo.id}
                role="button"
                onClick={() => toggleSelect(algo.id)}
                aria-pressed={isSelected}
                className={`border p-2 rounded shadow-sm cursor-pointer transition-colors ${
                  isSelected ? 'bg-blue-100 border-blue-500' : 'bg-white hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {algo.name} <span className="text-xs text-gray-500">v{algo.version}</span>
                    {isSelected && <span className="ml-2 text-xs text-blue-700">(selected)</span>}
                  </span>
                </div>
                {algo.description && (
                  <p className="text-xs text-gray-600 mt-1">{algo.description}</p>
                )}
                <div className="text-xs text-gray-500 mt-1">
                  {algo.parameters.length} parameter(s)
                </div>
              </div>
            );})
          )}
        </div>
      </details>

      {/* Algorithm Detail Dialog */}
      <AlgorithmDetail
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSuccess={() => {
          // Refresh list after creation
          loadAlgorithms();
        }}
      />
    </>
  );
}
