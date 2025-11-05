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

  const handleAdd = () => {
    setDialogOpen(true);
  };

  const handleDelete = async () => {
    if (algorithms.length > 0) {
      const lastAlgo = algorithms[algorithms.length - 1];
      if (lastAlgo.id) {
        await deleteAlgorithm(lastAlgo.id);
      }
    }
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
              title="Remove Last"
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
            algorithms.map((algo) => (
              <div
                key={algo.id}
                className="border p-2 rounded bg-white shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{algo.name} <span className="text-xs text-gray-500">v{algo.version}</span></span>
                </div>
                {algo.description && (
                  <p className="text-xs text-gray-600 mt-1">{algo.description}</p>
                )}
                <div className="text-xs text-gray-500 mt-1">
                  {algo.parameters.length} parameter(s)
                </div>
              </div>
            ))
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
