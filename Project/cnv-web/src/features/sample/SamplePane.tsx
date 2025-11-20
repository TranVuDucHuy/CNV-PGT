"use client";

import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
import { Plus, Minus, Edit3, X } from "lucide-react";
import useSampleHandle from "./sampleHandle";
import OperatingDialog from "@/components/OperatingDialog";
import { Checkbox } from "@mui/material";
import { ReferenceGenome } from "@/types/sample";

/**
 * Updated SamplePane
 * - Grouping: Flowcell -> Cycle -> Embryo
 * - Select cascade: selecting flowcell/cycle selects all children
 * - Parse sample.name if backend fields missing or 'rand'
 * - Removes plate suffix like _S93 for display
 */

type SampleItem = {
  id: string;
  name: string; // name in DB (expected to be filename without .bam)
  cell_type?: string;
  date?: string;
  // optional backend fields (may be 'rand' as placeholder)
  flowcell_id?: string;
  cycle_id?: string;
  embryo_id?: string;
  // keep any other props
  [k: string]: any;
};

function parseSampleNameToParts(rawName?: string) {
  // rawName may include .bam or not. Return { flowcell, cycle, embryo, displayName }
  if (!rawName || rawName.trim() === "") {
    return {
      flowcell: "UNKNOWN",
      cycle: "UNKNOWN",
      embryo: rawName ?? "UNKNOWN",
      displayName: rawName ?? "UNKNOWN",
    };
  }
  const name = rawName.endsWith(".bam") ? rawName.slice(0, -4) : rawName;
  const parts = name.split("-");
  if (parts.length === 1) {
    // can't split, fallback
    const embryoWithPlate = parts[0];
    const embryo = embryoWithPlate.split("_")[0];
    return {
      flowcell: "UNKNOWN",
      cycle: "UNKNOWN",
      embryo,
      displayName: embryo,
    };
  }
  // assume first part = flowcell, last part = embryo+plate, middle = cycle parts
  const flowcell = parts[0] || "UNKNOWN";
  const embryoWithPlate = parts[parts.length - 1] || "UNKNOWN";
  const embryo = embryoWithPlate.split("_")[0] || embryoWithPlate;
  const cycleParts = parts.slice(1, parts.length - 1);
  const cycle = cycleParts.join("-") || "UNKNOWN";
  return {
    flowcell,
    cycle,
    embryo,
    displayName: embryo,
  };
}

export default function SamplePane() {
  const {
    files,
    samples,
    isOpen,
    open,
    loading,
    error,
    close,
    setFile,
    save,
    saveManyFiles,
    removeSamples,
  } = useSampleHandle();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [removeDialog, setRemoveDialog] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();
  const [isSelectAll, setIsSelectAll] = useState<boolean>(false);
  const [referenceGenome, setReferenceGenome] = useState<ReferenceGenome>(ReferenceGenome.HG19);

  // UI expand/collapse state
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set()); // key: `${flowcell}|${cycle}`

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  // sync selectedIds when samples removed/changed
  useEffect(() => {
    if (!samples || samples.length === 0) {
      setSelectedIds(new Set());
      setIsSelectAll(false);
      return;
    }
    setSelectedIds((prev) => {
      const next = new Set<string>();
      const sampleIds = new Set(samples.map((s: any) => s.id));
      for (const id of prev) {
        if (id && sampleIds.has(id)) next.add(id);
      }
      return next;
    });
  }, [samples]);

  useEffect(() => {
    const total = samples.length;
    const selectedCount = selectedIds.size;
    setIsSelectAll(total > 0 && selectedCount === total);
  }, [selectedIds, samples]);

  const openOperatingDialog = (prom: Promise<any>) => {
    setOperating(true);
    setPromise(prom);
  };

  // Build grouping map: flowcell -> cycle -> samples[]
  const grouped = useMemo(() => {
    const map = new Map<
      string,
      Map<string, Array<{ sample: SampleItem; parsed: ReturnType<typeof parseSampleNameToParts> }>>
    >();

    for (const sRaw of (samples as SampleItem[] | undefined) ?? []) {
      const s = sRaw as SampleItem;

      // prefer backend-provided fields if present and not 'rand'
      const fallbackParsed = parseSampleNameToParts(s.name);

      const flowcell =
        s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo; // short name, already removed plate suffix by parse

      const parsed = {
        flowcell,
        cycle,
        embryo,
        displayName: display,
      };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }

    // sort flowcells and cycles alphabetically for stable UI
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
            // sort embryo or sample display ascending
            arr.sort((a, b) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [samples]);

  const allSampleIdsUnderFlowcell = (flowcell: string) => {
    const cycleMap = grouped.get(flowcell);
    if (!cycleMap) return [];
    const ids: string[] = [];
    for (const arr of cycleMap.values()) {
      for (const item of arr) ids.push(item.sample.id);
    }
    return ids;
  };

  const allSampleIdsUnderCycle = (flowcell: string, cycle: string) => {
    const cycleMap = grouped.get(flowcell);
    if (!cycleMap) return [];
    const arr = cycleMap.get(cycle) ?? [];
    return arr.map((it) => it.sample.id);
  };

  const isFlowcellAllSelected = (flowcell: string) => {
    const ids = allSampleIdsUnderFlowcell(flowcell);
    if (ids.length === 0) return false;
    return ids.every((id) => selectedIds.has(id));
  };

  const isFlowcellIndeterminate = (flowcell: string) => {
    const ids = allSampleIdsUnderFlowcell(flowcell);
    if (ids.length === 0) return false;
    const any = ids.some((id) => selectedIds.has(id));
    return any && !isFlowcellAllSelected(flowcell);
  };

  const isCycleAllSelected = (flowcell: string, cycle: string) => {
    const ids = allSampleIdsUnderCycle(flowcell, cycle);
    if (ids.length === 0) return false;
    return ids.every((id) => selectedIds.has(id));
  };

  const isCycleIndeterminate = (flowcell: string, cycle: string) => {
    const ids = allSampleIdsUnderCycle(flowcell, cycle);
    if (ids.length === 0) return false;
    const any = ids.some((id) => selectedIds.has(id));
    return any && !isCycleAllSelected(flowcell, cycle);
  };

  const toggleSelect = (id: string | undefined) => {
    if (id === undefined || id === null) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (event: ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;
    if (checked) {
      const next = new Set<string>();
      for (const s of samples as SampleItem[]) {
        if (s.id) next.add(s.id);
      }
      setSelectedIds(next);
      setIsSelectAll((samples as SampleItem[]).length > 0 && next.size === (samples as SampleItem[]).length);
    } else {
      setSelectedIds(new Set());
      setIsSelectAll(false);
    }
  };

  const toggleFlowcell = (flowcell: string) => {
    const ids = allSampleIdsUnderFlowcell(flowcell);
    if (ids.length === 0) return;
    const allSelected = ids.every((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const toggleCycle = (flowcell: string, cycle: string) => {
    const ids = allSampleIdsUnderCycle(flowcell, cycle);
    if (ids.length === 0) return;
    const allSelected = ids.every((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
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
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Sample</span>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.preventDefault();
              open();
            }}
            title="Add"
            className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              if (selectedIds.size > 0) {
                setRemoveDialog(true);
              }
            }}
            title="Remove"
            className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
          >
            <Minus size={16} />
          </button>
          <button title="Edit" className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded">
            <Edit3 size={16} />
          </button>
        </div>
      </summary>

      <div className="flex items-center gap-4 p-3">
        <div>{selectedIds.size} selected</div>
        <div className="flex items-center gap-2">
          <Checkbox checked={isSelectAll} onChange={toggleSelectAll} />
          <span className="text-sm font-medium">Select All</span>
        </div>
      </div>

      <div className="p-3 space-y-2">
        {loading ? (
          <div className="text-gray-500 text-sm text-center py-4">Loading samples...</div>
        ) : samples.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-4">No samples yet. Click + to add one.</div>
        ) : (
          <div className="space-y-3 max-h-[40vh] overflow-y-auto">
            {Array.from(grouped.entries()).map(([flowcell, cycleMap]) => {
              const flowcellAll = isFlowcellAllSelected(flowcell);
              const flowcellInd = isFlowcellIndeterminate(flowcell);
              const isOpenFlow = openFlowcells.has(flowcell);
              return (
                <div key={flowcell} className="border rounded p-2 bg-white">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={flowcellAll}
                        indeterminate={flowcellInd}
                        onChange={() => toggleFlowcell(flowcell)}
                      />
                      <button
                        onClick={() => toggleOpenFlowcell(flowcell)}
                        className="text-left font-semibold"
                      >
                        {flowcell} <span className="text-sm text-gray-500">({Array.from(cycleMap.values()).flat().length})</span>
                      </button>
                    </div>
                  </div>

                  {isOpenFlow && (
                    <div className="pl-5 pt-1 space-y-2">
                      {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                        const cycleAll = isCycleAllSelected(flowcell, cycle);
                        const cycleInd = isCycleIndeterminate(flowcell, cycle);
                        const cycleKey = `${flowcell}|${cycle}`;
                        const isOpenCycle = openCycles.has(cycleKey);
                        return (
                          <div key={cycle} className="rounded p-1 bg-gray-50">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Checkbox
                                  checked={cycleAll}
                                  indeterminate={cycleInd}
                                  onChange={() => toggleCycle(flowcell, cycle)}
                                />
                                <button onClick={() => toggleOpenCycle(flowcell, cycle)} className="text-left font-medium">
                                  {cycle} <span className="text-sm text-gray-500">({arr.length})</span>
                                </button>
                              </div>
                            </div>

                            {isOpenCycle && (
                              <div className="pl-5 pt-1 space-y-2">
                                {arr.map(({ sample, parsed }) => {
                                  const isSelected = sample.id !== undefined && selectedIds.has(sample.id);
                                  return (
                                    <div
                                      key={sample.id}
                                      role="button"
                                      onClick={() => toggleSelect(sample.id)}
                                      aria-pressed={isSelected}
                                      className={`p-1 rounded shadow-sm cursor-pointer transition-colors ${
                                        isSelected ? "bg-blue-100 border-blue-500" : "bg-white hover:bg-gray-50"
                                      }`}
                                    >
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <div className="font-medium">{parsed.displayName}</div>
                                          <div className="text-sm text-gray-600">{sample.cell_type ?? "-"}</div>
                                          <div className="text-sm text-gray-600">{sample.date ?? "-"}</div>
                                        </div>
                                        <div className="text-xs text-gray-500">{sample.name}</div>
                                      </div>
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

      {operating && promise ? (
        <OperatingDialog promise={promise} onDelayDone={() => setOperating(false)} autoCloseDelay={1000} />
      ) : (
        <div />
      )}

      {/* Upload dialog */}
      {isOpen && (
        <dialog open className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={close}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!operating) {
                if (files?.length && files?.length > 0) {
                  if (files?.length == 1) {
                    openOperatingDialog(save(referenceGenome));
                  } else if (files?.length > 1) {
                    openOperatingDialog(saveManyFiles(referenceGenome));
                  }
                }
              }
            }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload Sample</h3>
              <button type="button" onClick={close} className="p-1 rounded hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Select File</label>
                <input
                  type="file"
                  accept=".bam"
                  onChange={(e) => setFile(Array.from(e.target.files ?? []))}
                  className="mt-1 block w-full rounded border px-3 py-2"
                  required
                  multiple
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Reference Genome</label>
                <select
                  value={referenceGenome}
                  onChange={(e) => setReferenceGenome(e.target.value as ReferenceGenome)}
                  className="mt-1 block w-full rounded border px-3 py-2"
                  required
                >
                  <option value={ReferenceGenome.HG19}>HG19</option>
                  <option value={ReferenceGenome.HG38}>HG38</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button type="button" onClick={close} className="px-3 py-2 rounded border hover:bg-gray-50">
                  Cancel
                </button>
                <button type="submit" className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700">
                  {operating ? <div>Uploading</div> : <div>Upload</div>}
                </button>
              </div>
            </div>
          </form>
        </dialog>
      )}

      {/* Remove dialog */}
      {removeDialog && (
        <dialog
          open
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setRemoveDialog(false)}
        >
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!operating) {
                save();
                openOperatingDialog(removeSamples(selectedIds));
                setRemoveDialog(false);
              }
            }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => { e.stopPropagation();
              
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">You sure want to remove these samples</h3>
            </div>

            <div className="space-y-4">
              <div className="overflow-y-auto max-h-40">
                {samples.map((s: SampleItem) => {
                  const isSelected = s.id !== undefined && selectedIds.has(s.id);
                  if (!isSelected) return null;
                  // display short parsed name
                  const parsed = parseSampleNameToParts(s.name);
                  return (
                    <div key={s.id} className="border p-2 rounded shadow-sm transition-colors bg-white">
                      <div className="font-medium">{parsed.displayName}</div>
                      <div className="text-sm text-gray-600">{s.cell_type ?? "-"}</div>
                      <div className="text-sm text-gray-600">{s.date ?? "-"}</div>
                    </div>
                  );
                })}
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button type="button" onClick={() => setRemoveDialog(false)} className="px-3 py-2 rounded border hover:bg-gray-50">
                  Cancel
                </button>
                <button type="submit" className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700">
                  Yes
                </button>
              </div>
            </div>
          </form>
        </dialog>
      )}
    </details>
  );
}
