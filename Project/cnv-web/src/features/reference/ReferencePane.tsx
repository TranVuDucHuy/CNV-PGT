/**
 * ReferencePane Component
 * Hiển thị các samples được chọn làm reference
 */

"use client";

import React, { ChangeEvent, useEffect, useMemo, useState } from 'react';
import { Plus, Minus, X } from 'lucide-react';
import { useReferencesStore, addReferences, removeReferences } from './useReferences';
import { parseSampleNameToParts } from '@/features/sample/sampleUtils';
import { SampleSummary } from '@/types/sample';
import { Checkbox } from '@mui/material';

type SampleItem = {
  id: string;
  name: string;
  cell_type?: string;
  date?: string;
  flowcell_id?: string;
  cycle_id?: string;
  embryo_id?: string;
  [k: string]: any;
};

interface ReferencePaneProps {
  samples: SampleSummary[];
  onRefresh?: () => Promise<void>;
}

export default function ReferencePane({ samples, onRefresh }: ReferencePaneProps) {
  const { referenceIds } = useReferencesStore();
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedForAdd, setSelectedForAdd] = useState<Set<string>>(new Set());
  const [selectedForRemove, setSelectedForRemove] = useState<Set<string>>(new Set());
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());

  // Lấy danh sách references từ samples
  const referenceSamples = useMemo(() => {
    return samples.filter((s) => referenceIds.has(s.id));
  }, [samples, referenceIds]);

  // Lấy samples chưa là reference để hiển thị trong modal
  const availableSamples = useMemo(() => {
    return samples.filter((s) => !referenceIds.has(s.id));
  }, [samples, referenceIds]);

  // Group references theo Flowcell > Cycle
  const groupedReferences = useMemo(() => {
    const map = new Map<
      string,
      Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>
    >();

    for (const sRaw of referenceSamples as SampleItem[]) {
      const s = sRaw as SampleItem;
      const fallbackParsed = parseSampleNameToParts(s.name);
      const flowcell = s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo;

      const parsed = { flowcell, cycle, embryo, displayName: display };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }

    // Sort
    const sortedMap = new Map<string, Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>>();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>();
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!;
            arr.sort((a, b) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [referenceSamples]);

  // Group available samples cho modal
  const groupedAvailable = useMemo(() => {
    const map = new Map<
      string,
      Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>
    >();

    for (const sRaw of availableSamples as SampleItem[]) {
      const s = sRaw as SampleItem;
      const fallbackParsed = parseSampleNameToParts(s.name);
      const flowcell = s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo;

      const parsed = { flowcell, cycle, embryo, displayName: display };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }

    const sortedMap = new Map<string, Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>>();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>();
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!;
            arr.sort((a, b) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [availableSamples]);

  const handleAddClick = () => {
    setSelectedForAdd(new Set());
    setAddDialogOpen(true);
  };

  const handleAddConfirm = () => {
    addReferences(selectedForAdd);
    if (onRefresh) {
      onRefresh();
    }
    setAddDialogOpen(false);
    setSelectedForAdd(new Set());
  };

  const handleRemoveClick = () => {
    if (selectedForRemove.size > 0) {
      removeReferences(selectedForRemove);
      setSelectedForRemove(new Set());
    }
  };

  const toggleSelectForRemove = (id: string) => {
    setSelectedForRemove((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectForAdd = (id: string) => {
    setSelectedForAdd((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleOpenFlowcell = (flowcell: string) => {
    setOpenFlowcells((prev) => {
      const next = new Set(prev);
      if (next.has(flowcell)) next.delete(flowcell);
      else next.add(flowcell);
      return next;
    });
  };

  const toggleOpenCycle = (flowcell: string, cycle: string) => {
    const key = `${flowcell}|${cycle}`;
    setOpenCycles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <>
      <details open className="border rounded-md">
        <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
          <span>Reference [{referenceSamples.length}]</span>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.preventDefault();
                handleAddClick();
              }}
              title="Add"
              className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
            >
              <Plus size={16} />
            </button>
            <button
              onClick={(e) => {
                e.preventDefault();
                handleRemoveClick();
              }}
              title="Remove"
              className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
            >
              <Minus size={16} />
            </button>
          </div>
        </summary>

        <div className="p-3 space-y-2">
          {referenceSamples.length === 0 ? (
            <div className="text-gray-500 text-sm text-center py-4">
              No references yet. Click + to add.
            </div>
          ) : (
            <div className="space-y-3 max-h-[40vh] overflow-y-auto">
              {Array.from(groupedReferences.entries()).map(([flowcell, cycleMap]) => {
                const isOpenFlow = openFlowcells.has(flowcell);
                return (
                  <div key={flowcell} className="border rounded p-2 bg-white">
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => toggleOpenFlowcell(flowcell)}
                        className="text-left font-semibold"
                      >
                        {flowcell} <span className="text-sm text-gray-500">({Array.from(cycleMap.values()).flat().length})</span>
                      </button>
                    </div>

                    {isOpenFlow && (
                      <div className="pl-3 pt-1 space-y-2">
                        {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                          const cycleKey = `${flowcell}|${cycle}`;
                          const isOpenCycle = openCycles.has(cycleKey);
                          return (
                            <div key={cycle} className="rounded p-1 bg-gray-50">
                              <button onClick={() => toggleOpenCycle(flowcell, cycle)} className="text-left font-medium">
                                {cycle} <span className="text-sm text-gray-500">({arr.length})</span>
                              </button>

                              {isOpenCycle && (
                                <div className="pl-3 pt-1 space-y-1">
                                  {arr.map(({ sample, parsed }) => {
                                    const isSelected = selectedForRemove.has(sample.id);
                                    return (
                                      <div
                                        key={sample.id}
                                        role="button"
                                        onClick={() => toggleSelectForRemove(sample.id)}
                                        className={`p-1 rounded cursor-pointer transition-colors ${
                                          isSelected ? "bg-blue-100 border-blue-500" : "bg-white hover:bg-gray-50"
                                        }`}
                                      >
                                        <div className="text-sm font-medium">{parsed.displayName}</div>
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </details>

      {/* Add Dialog */}
      {addDialogOpen && (
        <dialog open className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setAddDialogOpen(false)}>
          <div
            className="bg-white rounded-lg shadow-xl w-full max-w-2xl m-4 max-h-[80vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">Add Samples to Reference</h3>
              <button onClick={() => setAddDialogOpen(false)} className="text-gray-500 hover:text-gray-700">
                <X size={20} />
              </button>
            </div>

            <div className="p-4 overflow-y-auto flex-1">
              {availableSamples.length === 0 ? (
                <div className="text-gray-500 text-center py-8">All samples are already references</div>
              ) : (
                <div className="space-y-3">
                  {Array.from(groupedAvailable.entries()).map(([flowcell, cycleMap]) => (
                    <div key={flowcell} className="border rounded p-2">
                      <div className="font-semibold mb-2">{flowcell}</div>
                      <div className="pl-3 space-y-2">
                        {Array.from(cycleMap.entries()).map(([cycle, arr]) => (
                          <div key={cycle}>
                            <div className="font-medium text-sm mb-1">{cycle}</div>
                            <div className="pl-3 space-y-1">
                              {arr.map(({ sample, parsed }) => {
                                const isSelected = selectedForAdd.has(sample.id);
                                return (
                                  <div
                                    key={sample.id}
                                    className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                                      isSelected ? "bg-blue-50 border border-blue-300" : "bg-gray-50 hover:bg-gray-100"
                                    }`}
                                    onClick={() => toggleSelectForAdd(sample.id)}
                                  >
                                    <Checkbox checked={isSelected} onChange={() => toggleSelectForAdd(sample.id)} />
                                    <div className="flex-1">
                                      <div className="text-sm font-medium">{parsed.displayName}</div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center justify-between p-4 border-t">
              <div className="text-sm text-gray-600">{selectedForAdd.size} selected</div>
              <div className="flex gap-2">
                <button
                  onClick={() => setAddDialogOpen(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddConfirm}
                  disabled={selectedForAdd.size === 0}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </dialog>
      )}
    </>
  );
}
