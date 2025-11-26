/**
 * AlgorithmPane Component
 * Tất cả UI và logic của Algorithm section
 */

"use client";

import React, { useMemo, useState } from 'react';
import { Plus, Minus, StepForward, Edit } from 'lucide-react';
import { useAlgorithms } from './useAlgorithms';
import AlgorithmDetail from '@/components/AlgorithmDetail';
import { useSelectionStore, setSelectedAlgorithm } from '@/features/selection/selectionStore';
import { useReferencesStore } from '@/features/reference/useReferences';
import { algorithmAPI } from '@/services';
import RunAlgorithmWarningDialog from './RunAlgorithmWarningDialog';
import RunningAlgorithmDialog from './RunningAlgorithmDialog';
import RunAlgorithmErrorDialog from './RunAlgorithmErrorDialog';
import useResultHandle from '@/features/result/resultHandle';

export default function AlgorithmPane() {
  const { algorithms, loading, deleteAlgorithm, loadAlgorithms, lastValues, recordLastValues } = useAlgorithms();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());
  const [editOpen, setEditOpen] = useState(false);
  const [editTargetId, setEditTargetId] = useState<string | number | null>(null);

  // Selection store để biết sample và algorithm đang chọn
  const { selectedSample, selectedAlgorithm: selectedAlgoFromStore } = useSelectionStore();
  const { referenceIds } = useReferencesStore();
  const { refresh: refreshResults } = useResultHandle();

  // Warning & Running dialogs
  const [warningOpen, setWarningOpen] = useState(false);
  const [runningOpen, setRunningOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const editTarget = useMemo(() => algorithms.find(a => a.id === editTargetId), [algorithms, editTargetId]);

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

  // Sync selection store khi chọn algorithm (chỉ khi đúng 1 algorithm được chọn)
  React.useEffect(() => {
    if (selectedIds.size === 1) {
      const selectedId = Array.from(selectedIds)[0];
      const algo = algorithms.find((a) => a.id === selectedId);
      if (algo) {
        setSelectedAlgorithm(algo);
      } else {
        setSelectedAlgorithm(null);
      }
    } else {
      setSelectedAlgorithm(null);
    }
  }, [selectedIds, algorithms]);

  const handleRun = async () => {
    // Kiểm tra điều kiện: đúng 1 sample và 1 algorithm
    if (!selectedSample || !selectedAlgoFromStore) {
      alert('Please select exactly 1 sample and 1 algorithm to run.');
      return;
    }

    const algo = selectedAlgoFromStore;
    const referencesRequired = algo.references_required ?? 0;
    const currentReferenceCount = referenceIds.size;

    // Kiểm tra exe_class và số references
    if (!algo.exe_class || currentReferenceCount < referencesRequired) {
      console.log('Cannot run algorithm, missing conditions:', {
        exe_class: algo.exe_class,
        referencesRequired,
        currentReferenceCount,
      });
      setWarningOpen(true);
      return;
    }

    // Đủ điều kiện, tiến hành chạy
    setRunningOpen(true);
    setErrorMessage(null);

    try {
      await algorithmAPI.run(algo.id, selectedSample.id);
      // Thành công -> refresh results
      setRunningOpen(false);
      await refreshResults();
      alert('Algorithm completed successfully! Check Results pane.');
    } catch (err) {
      setRunningOpen(false);
      const message = err instanceof Error ? err.message : String(err);
      setErrorMessage(message);
    }
  };

  const handleEditClick = (id: string | number | undefined) => {
    if (id === undefined || id === null) return;
    setEditTargetId(id);
    setEditOpen(true);
  };

  // Enable nút Run chỉ khi đúng 1 sample và 1 algorithm
  const canRun = selectedSample !== null && selectedAlgoFromStore !== null;

  // Lấy parameters để hiển thị trong Running dialog
  const currentParams = React.useMemo(() => {
    if (!selectedAlgoFromStore?.last_parameter_id) return {};
    const paramSet = selectedAlgoFromStore.parameters?.find(
      (p) => p.id === selectedAlgoFromStore.last_parameter_id
    );
    return paramSet?.value || {};
  }, [selectedAlgoFromStore]);

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
            {/* Run Algorithm button */}
            <button
              onClick={handleRun}
              title={canRun ? "Run Algorithm" : "Select exactly 1 sample and 1 algorithm to run"}
              disabled={!canRun}
              className={`p-1 text-white rounded ${
                canRun 
                  ? 'bg-blue-500 hover:bg-blue-600' 
                  : 'bg-gray-400 cursor-not-allowed'
              }`}
            >
              <StepForward size={16} />
            </button>
          </div>
        </summary>

  <div className="p-3 space-y-2 max-h-52 overflow-y-scroll pr-2" style={{ scrollbarGutter: 'stable' }}>
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
                className={`group border p-2 rounded cursor-pointer transition-all duration-200 ${
                  isSelected 
                    ? 'bg-blue-300 border-blue-600 shadow-md' 
                    : 'bg-white hover:bg-blue-100 hover:shadow-md hover:border-blue-400'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {algo.name} <span className="text-xs text-gray-500">v{algo.version}</span>
                    {isSelected && <span className="ml-2 text-xs text-blue-700"></span>}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleEditClick(algo.id); }}
                      title="Edit"
                      className="p-1 text-gray-600 hover:bg-gray-100 rounded transition-transform transform hover:scale-110"
                    >
                      <Edit size={16} />
                    </button>
                  </div>
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
        onSaveValues={(vals) => {
          // Values saved after creation, though not actively used yet
        }}
        onSuccess={() => {
          // Refresh list after creation
          loadAlgorithms();
        }}
      />

      {/* Edit Algorithm Dialog */}
      <AlgorithmDetail
        open={editOpen}
        mode="edit"
        initialAlgorithm={editTarget}
        onSaveValues={(vals) => {
          if (editTarget) {
            recordLastValues(String(editTarget.id), vals);
          }
        }}
        onClose={() => setEditOpen(false)}
        onSuccess={() => {
          loadAlgorithms();
          setEditOpen(false);
        }}
      />

      {/* Warning Dialog - thiếu điều kiện */}
      <RunAlgorithmWarningDialog
        open={warningOpen}
        onClose={() => setWarningOpen(false)}
        referencesRequired={selectedAlgoFromStore?.references_required ?? 0}
        onUploadModule={() => {
          // Mở edit dialog để upload module
          if (selectedAlgoFromStore) {
            setEditTargetId(selectedAlgoFromStore.id);
            setEditOpen(true);
          }
        }}
      />

      {/* Running Dialog */}
      <RunningAlgorithmDialog
        open={runningOpen}
        sampleName={selectedSample?.name || ''}
        algorithmName={selectedAlgoFromStore?.name || ''}
        algorithmVersion={selectedAlgoFromStore?.version || ''}
        parameters={currentParams}
      />

      {/* Error Dialog */}
      <RunAlgorithmErrorDialog
        open={!!errorMessage}
        errorMessage={errorMessage || ''}
        onClose={() => setErrorMessage(null)}
        onRetry={() => {
          setErrorMessage(null);
          handleRun();
        }}
      />
    </>
  );
}
