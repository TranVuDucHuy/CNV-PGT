"use client";

import React, { ChangeEvent, useEffect, useState, useMemo } from "react";
import { Plus, Minus, Edit3, X } from "lucide-react";
import useResultHandle from "./resultHandle";
import OperatingDialog from "@/components/OperatingDialog";
import { Checkbox } from "@mui/material";
import { useAlgorithms } from "../algorithm/useAlgorithms";

export default function ResultPane() {
  const {
    results,
    binFile,
    segmentFile,
    loading,
    error,
    algo,
    setBinFile,
    setSegmentFile,
    save,
    refresh,
    removeResults,
    setAlgo,
  } = useResultHandle();

  const { algorithms } = useAlgorithms();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [uploadDialog, setUploadDialog] = useState<boolean>(false);
  const [removeDialog, setRemoveDialog] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();

  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());
  const [openEmbryos, setOpenEmbryos] = useState<Set<string>>(new Set());

  // ======== Group results by Flowcell -> Cycle -> Embryo -> Algorithm -> Params =========
  const groupedResults = useMemo(() => {
    const map = new Map<
      string,
      Map<
        string,
        Map<
          string,
          Map<
            string,
            Array<{ result: typeof results[number]; paramIndex: number }>
          >
        >
      >
    >();

    for (const r of results) {
      const {flowcell, cycle, embryo} = parseSampleNameToParts(r.sample_name);
      const algoId = r.algorithm_name ?? "UNKNOWN";
      const params = [""];

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;

      if (!cycleMap.has(cycle)) cycleMap.set(cycle, new Map());
      const embryoMap = cycleMap.get(cycle)!;

      if (!embryoMap.has(embryo)) embryoMap.set(embryo, new Map());
      const algoMap = embryoMap.get(embryo)!;

      if (!algoMap.has(algoId)) algoMap.set(algoId, []);
      const paramArray = algoMap.get(algoId)!;

      params.forEach((pId, idx) => {
        paramArray.push({ result: r, paramIndex: idx });
      });
    }

    return map;
  }, [results]);

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
    embryo
  };
}

  // ======== Helpers for cascade select =========
  const getAllResultIdsUnderFlowcell = (flowcell: string) => {
    const cycleMap = groupedResults.get(flowcell);
    if (!cycleMap) return [];
    const ids: string[] = [];
    for (const embryoMap of cycleMap.values()) {
      for (const algoMap of embryoMap.values()) {
        for (const arr of algoMap.values()) {
          arr.forEach((item) => ids.push(item.result.id));
        }
      }
    }
    return ids;
  };

  const getAllResultIdsUnderCycle = (flowcell: string, cycle: string) => {
    const cycleMap = groupedResults.get(flowcell)?.get(cycle);
    if (!cycleMap) return [];
    const ids: string[] = [];
    for (const embryoMap of cycleMap.values()) {
      for (const arr of embryoMap.values()) {
        arr.forEach((item) => ids.push(item.result.id));
      }
    }
    return ids;
  };

  const getAllResultIdsUnderEmbryo = (flowcell: string, cycle: string, embryo: string) => {
    const embryoMap = groupedResults.get(flowcell)?.get(cycle)?.get(embryo);
    if (!embryoMap) return [];
    const ids: string[] = [];
    for (const arr of embryoMap.values()) {
      arr.forEach((item) => ids.push(item.result.id));
    }
    return ids;
  };

  const getAllResultIdsUnderAlgo = (flowcell: string, cycle: string, embryo: string, algoId: string) => {
    const arr = groupedResults.get(flowcell)?.get(cycle)?.get(embryo)?.get(algoId);
    if (!arr) return [];
    return arr.map((item) => item.result.id);
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectFlowcell = (flowcell: string) => {
    const ids = getAllResultIdsUnderFlowcell(flowcell);
    const anySelected = ids.some((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => (anySelected ? next.delete(id) : next.add(id)));
      return next;
    });
  };

  const toggleSelectCycle = (flowcell: string, cycle: string) => {
    const ids = getAllResultIdsUnderCycle(flowcell, cycle);
    const anySelected = ids.some((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => (anySelected ? next.delete(id) : next.add(id)));
      return next;
    });
  };

  const toggleSelectEmbryo = (flowcell: string, cycle: string, embryo: string) => {
    const ids = getAllResultIdsUnderEmbryo(flowcell, cycle, embryo);
    const anySelected = ids.some((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => (anySelected ? next.delete(id) : next.add(id)));
      return next;
    });
  };

  const toggleSelectAlgo = (flowcell: string, cycle: string, embryo: string, algoId: string) => {
    const ids = getAllResultIdsUnderAlgo(flowcell, cycle, embryo, algoId);
    const anySelected = ids.some((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      ids.forEach((id) => (anySelected ? next.delete(id) : next.add(id)));
      return next;
    });
  };

  const openOperatingDialog = (prom: Promise<any>) => {
    setOperating(true);
    setPromise(prom);
  };

  // ======== Keyboard escape for upload dialog ========
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && uploadDialog) setUploadDialog(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [uploadDialog]);

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Result</span>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.preventDefault();
              setUploadDialog(true);
            }}
            title="Add"
            className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              if (selectedIds.size > 0) setRemoveDialog(true);
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

      <div className="p-3 space-y-2 max-h-96 overflow-y-auto">
        {results.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-4">No results yet. Click + to add one.</div>
        ) : (
          Array.from(groupedResults.entries()).map(([flowcell, cycleMap]) => {
            const flowcellAll = getAllResultIdsUnderFlowcell(flowcell).every((id) => selectedIds.has(id));
            return (
              <div key={flowcell} className="border p-2 rounded bg-white">
                <div className="flex items-center gap-2">
                  <Checkbox checked={flowcellAll} onChange={() => toggleSelectFlowcell(flowcell)} />
                  <button
                    className="font-medium"
                    onClick={() => setOpenFlowcells((prev) => {
                      const next = new Set(prev);
                      next.has(flowcell) ? next.delete(flowcell) : next.add(flowcell);
                      return next;
                    })}
                  >
                    {flowcell}
                  </button>
                </div>

                {openFlowcells.has(flowcell) &&
                  Array.from(cycleMap.entries()).map(([cycle, embryoMap]) => {
                    const cycleAll = getAllResultIdsUnderCycle(flowcell, cycle).every((id) =>
                      selectedIds.has(id)
                    );
                    return (
                      <div key={cycle} className="pl-5 mt-1">
                        <div className="flex items-center gap-2">
                          <Checkbox checked={cycleAll} onChange={() => toggleSelectCycle(flowcell, cycle)} />
                          <button
                            className="font-medium"
                            onClick={() =>
                              setOpenCycles((prev) => {
                                const next = new Set(prev);
                                const key = `${flowcell}|${cycle}`;
                                next.has(key) ? next.delete(key) : next.add(key);
                                return next;
                              })
                            }
                          >
                            {cycle}
                          </button>
                        </div>

                        {openCycles.has(`${flowcell}|${cycle}`) &&
                          Array.from(embryoMap.entries()).map(([embryo, algoMap]) => {
                            const embryoAll = getAllResultIdsUnderEmbryo(flowcell, cycle, embryo).every((id) =>
                              selectedIds.has(id)
                            );
                            return (
                              <div key={embryo} className="pl-5 mt-1">
                                <div className="flex items-center gap-2">
                                  <Checkbox checked={embryoAll} onChange={() => toggleSelectEmbryo(flowcell, cycle, embryo)} />
                                  <button
                                    className="font-medium"
                                    onClick={() =>
                                      setOpenEmbryos((prev) => {
                                        const next = new Set(prev);
                                        const key = `${flowcell}|${cycle}|${embryo}`;
                                        next.has(key) ? next.delete(key) : next.add(key);
                                        return next;
                                      })
                                    }
                                  >
                                    {embryo}
                                  </button>
                                </div>

                                {openEmbryos.has(`${flowcell}|${cycle}|${embryo}`) &&
                                  Array.from(algoMap.entries()).map(([algoId, params]) => {
                                    const algoAll = getAllResultIdsUnderAlgo(flowcell, cycle, embryo, algoId).every(
                                      (id) => selectedIds.has(id)
                                    );
                                    return (
                                      <div key={algoId} className="pl-5 mt-1">
                                        <div className="flex items-center gap-2">
                                          <Checkbox checked={algoAll} onChange={() => toggleSelectAlgo(flowcell, cycle, embryo, algoId)} />
                                          <span className="font-medium">{params[0]?.result.algorithm_name}</span>
                                        </div>
                                        <div className="pl-5">
                                          {params.slice(0, 2).map((p) => (
                                            <div key={p.paramIndex} className="flex items-center gap-2">
                                              <Checkbox
                                                checked={selectedIds.has(p.result.id)}
                                                onChange={() => toggleSelect(p.result.id)}
                                              />
                                              <span>Param {p.paramIndex + 1}</span>
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    );
                                  })}
                              </div>
                            );
                          })}
                      </div>
                    );
                  })}
              </div>
            );
          })
        )}
      </div>

      {operating && promise && <OperatingDialog promise={promise} onDelayDone={() => setOperating(false)} autoCloseDelay={1000} />}

      {/* Upload Dialog */}
      {uploadDialog && (
        <dialog open className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setUploadDialog(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!operating && binFile && segmentFile) {
                openOperatingDialog(save());
                setUploadDialog(false);
              }
            }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload Result</h3>
              <button type="button" onClick={() => setUploadDialog(false)} className="p-1 rounded hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Select Bin File</label>
                <input type="file" accept=".tsv" onChange={(e) => setBinFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full rounded border px-3 py-2" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Select Segment File</label>
                <input type="file" accept=".tsv" onChange={(e) => setSegmentFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full rounded border px-3 py-2" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Select Algorithm</label>

                <div>
                  {algo ? <div>Selected Algorithm {algo.name}</div> : <div></div>}
                </div>
                <div>
                  {algorithms.length === 0 ? (
                    <div className="text-gray-500 text-sm text-center py-4">No algorithms yet. Click + to add one.</div>
                  ) : (
                    <div className="overflow-y-auto max-h-50 space-y-2">
                      {algorithms.map((al) => {
                        const isSelected = al.id !== undefined && al === algo;
                        return (
                          <div
                            key={al.id}
                            role="button"
                            onClick={() => setAlgo(al)}
                            aria-pressed={isSelected}
                            className={`border p-2 rounded shadow-sm cursor-pointer transition-colors ${
                              isSelected ? "bg-blue-100 border-blue-500" : "bg-white hover:bg-gray-50"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium">
                                {al.name} <span className="text-xs text-gray-500">v{al.version}</span>
                                {isSelected && <span className="ml-2 text-xs text-blue-700">(selected)</span>}
                              </span>
                            </div>
                            {al.description && <p className="text-xs text-gray-600 mt-1">{al.description}</p>}
                            <div className="text-xs text-gray-500 mt-1">{al.parameters.length} parameter(s)</div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button type="button" onClick={() => setUploadDialog(false)} className="px-3 py-2 rounded border hover:bg-gray-50">
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
      {/* Dialog xóa */}
      {removeDialog && (
        <dialog open className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setRemoveDialog(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save();
            }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => {
              if (!operating) {
                e.stopPropagation();
                openOperatingDialog(removeResults(selectedIds));
                setRemoveDialog(false);
              }
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">You sure want to remove these samples</h3>
            </div>

            <div className="space-y-4">
              <div className="overflow-y-auto max-h-50">
                {results.map((r) => {
                  const isSelected = r.id !== undefined && selectedIds.has(r.id);
                  if (isSelected) {
                    return (
                      <div key={r.id} className={`border p-2 rounded shadow-sm transition-colors 'bg-white hover:bg-gray-50'`}>
                        <div className="font-medium">{r.id}</div>
                        <div className="font-medium">{r.reference_genome}</div>
                        <div className="font-medium">{r.algorithm_name}</div>
                      </div>
                    );
                  }
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
