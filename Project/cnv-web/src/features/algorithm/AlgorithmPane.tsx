/**
 * AlgorithmPane Component
 * Tất cả UI và logic của Algorithm section
 */

"use client";

import React, { useMemo, useState } from 'react';
import { Plus, Minus, StepForward, Edit3 } from 'lucide-react';
import {
  Box,
  Button,
  Stack,
  Typography,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import MUIAccordionPane from '@/components/MUIAccordionPane';
import { useAlgorithms } from './useAlgorithms';
import AlgorithmDetail from '@/features/algorithm/AlgorithmDetail';
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

  const headerRight = (
    <Stack direction="row" spacing={1} alignItems="center">
      <Tooltip title="Add Algorithm">
        <Button
          onClick={(e) => {
            e.stopPropagation();
            handleAdd();
          }}
          variant="contained"
          size="small"
          sx={{ minWidth: 0, px: 1, bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
        >
          <Plus size={14} />
        </Button>
      </Tooltip>

      <Tooltip title="Delete Selected">
        <Button
          onClick={(e) => {
            e.stopPropagation();
            if (selectedIds.size > 0) {
              handleDelete();
            }
          }}
          variant="contained"
          size="small"
          sx={{ minWidth: 0, px: 1, bgcolor: '#EF4444', '&:hover': { bgcolor: '#DC2626' } }}
        >
          <Minus size={14} />
        </Button>
      </Tooltip>

      <Tooltip title={canRun ? 'Run Algorithm' : 'Select exactly 1 sample and 1 algorithm to run'}>
        <span>
          <Button
            onClick={(e) => {
              e.stopPropagation();
              handleRun();
            }}
            variant="contained"
            size="small"
            disabled={!canRun}
            sx={{
              minWidth: 0,
              px: 1,
              bgcolor: canRun ? '#3B82F6' : '#9CA3AF',
              '&:hover': { bgcolor: canRun ? '#2563EB' : '#9CA3AF' },
              '&:disabled': { bgcolor: '#9CA3AF', cursor: 'not-allowed' },
            }}
          >
            <StepForward size={14} />
          </Button>
        </span>
      </Tooltip>
    </Stack>
  );

  return (
    <>
      <MUIAccordionPane title="Algorithm" defaultExpanded headerRight={headerRight}>
        <Box sx={{ maxHeight: '24vh', overflowY: 'auto', pr: 1, scrollbarGutter: 'stable' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress size={32} />
            </Box>
          ) : algorithms.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" color="text.secondary">
                No algorithms yet. Click + to add one.
              </Typography>
            </Box>
          ) : (
            <Stack spacing={1}>
              {algorithms.map((algo) => {
                const isSelected = algo.id !== undefined && selectedIds.has(algo.id);
                return (
                  <Box
                    key={algo.id}
                    role="button"
                    onClick={() => toggleSelect(algo.id)}
                    aria-pressed={isSelected}
                    sx={{
                      p: 1.5,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: isSelected ? 'primary.main' : 'rgba(0,0,0,0.12)',
                      bgcolor: isSelected ? '#DBEAFE' : '#fff',
                      cursor: 'pointer',
                      transition: 'all 0.12s',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      userSelect: 'none',
                      '&:hover': {
                        bgcolor: isSelected ? '#DBEAFE' : '#F9FAFB',
                        borderColor: isSelected ? 'primary.main' : '#D1D5DB',
                      },
                    }}
                  >
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {algo.name}{' '}
                        <Typography component="span" variant="caption" color="text.secondary">
                          v{algo.version}
                        </Typography>
                      </Typography>
                    </Box>

                    <Tooltip title="Edit Algorithm">
                      <Button
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditClick(algo.id);
                        }}
                        sx={{
                          minWidth: 0,
                          p: 0.5,
                          color: 'text.secondary',
                          '&:hover': { bgcolor: '#F3F4F6' },
                        }}
                      >
                        <Edit3 size={16} />
                      </Button>
                    </Tooltip>
                  </Box>
                );
              })}
            </Stack>
          )}
        </Box>
      </MUIAccordionPane>
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
