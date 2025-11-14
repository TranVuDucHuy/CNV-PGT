"use client";

import React, { ChangeEvent, useEffect, useState } from "react";
import { Plus, Minus, Edit3, X } from "lucide-react";
import useResultHandle from "./resultHandle"
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
    algoId,
    setBinFile,
    setSegmentFile,
    save,
    refresh,
    removeResults,
    getAll,
    setAlgoId
  } = useResultHandle();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [uploadDialog, setUploadDialog] = useState<boolean>(false);
  const [removeDialog, setRemoveDialog] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();
  const [isSelectAll, setIsSelectAll] = useState<boolean>(false);
  const { algorithms } = useAlgorithms();

  useEffect(() => {
    // close on Escape handled inside hook via isOpen effect if needed, keep for safety
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && uploadDialog) setUploadDialog(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [uploadDialog, setUploadDialog]);

  // Sync selectedIds with samples list: remove any selected id that no longer exists
  useEffect(() => {
    if (results.length === 0) {
      setSelectedIds(new Set());
      setIsSelectAll(false);
      return;
    }

    setSelectedIds((prev) => {
      const next = new Set<string>();
      const sampleIds = new Set(results.map((r) => r.id));
      let changed = false;
      for (const id of prev) {
        if (id && sampleIds.has(id)) {
          next.add(id);
        } else {
          changed = true; // removed some stale id
        }
      }
      // if nothing selected previously, just return prev (but we already created next)
      if (changed) return next;
      return prev;
    });
  }, [results]);

  // whenever selectedIds or samples change, update isSelectAll
  useEffect(() => {
    const total = results.length;
    const selectedCount = selectedIds.size;
    setIsSelectAll(total > 0 && selectedCount === total);
  }, [selectedIds, results]);

  const toggleSelect = (id: string | undefined) => {
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
    // isSelectAll sẽ được cập nhật bởi effect trên
  };

  const toggleSelectAll = (event: ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;
    if (checked) {
      // chọn tất cả
      const next = new Set<string>();
      results.forEach((r) => {
        if (r.id) next.add(r.id);
      });
      setSelectedIds(next);
      setIsSelectAll(results.length > 0 && next.size === results.length);
    } else {
      // bỏ chọn tất cả
      setSelectedIds(new Set());
      setIsSelectAll(false);
    }
  };

  const openOperatingDialog = (prom: Promise<any>) => {
    setOperating(true)
    setPromise(prom)
  }

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Result</span>
        <div className="flex items-center gap-2">
          
          <button
            onClick={(e) => { e.preventDefault(); setUploadDialog(true); }}
            title="Add"
            className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={(e) => { e.preventDefault(); if (selectedIds.size > 0) {setRemoveDialog(true)} }}
            title="Remove"
            className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
          >
            <Minus size={16} />
          </button>
          <button
            title="Edit"
            className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
          >
            <Edit3 size={16} />
          </button>
          
          
        </div>
      </summary>
      <div className="flex items-center gap-2">
        <div>
          {
            selectedIds.size
          }
          selected
        </div>
        <div >
          <Checkbox
            checked={isSelectAll}
            onChange={toggleSelectAll}
          />
          <span className="text-sm font-medium">Select All</span>
        </div>
      </div>

      <div className="p-3 space-y-2">
        {
          loading ? (
              <div className="text-gray-500 text-sm text-center py-4">
                Loading algorithms...
              </div>
          ) : results.length === 0 ? (
            <div className="text-gray-500 text-sm text-center py-4">No results yet. Click + to add one.</div>
          ) : (
            <div className="overflow-y-auto max-h-50 space-y-2">
              {
                results.map((r) => {
                    const isSelected = r.id !== undefined && selectedIds.has(r.id);
                    return (
                      <div 
                        key={r.id} 
                        role="button"
                        onClick={() => toggleSelect(r.id)}
                        aria-pressed={isSelected}
                        className={`border p-2 rounded shadow-sm cursor-pointer transition-colors ${
                          isSelected ? 'bg-blue-100 border-blue-500' : 'bg-white hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{r.id}</div>
                            <div className="text-sm text-gray-600">{r.reference_genome}</div>
                            <div className="text-sm text-gray-600">{r.algorithm_name}</div>
                          </div>
                        </div>
                      </div>
                    )
                  }
                )
              }
            </div>
          )
        }
      </div>
      
      {
        operating && promise ? (
          <OperatingDialog promise={promise} onDelayDone={() => setOperating(false)} autoCloseDelay={1000}></OperatingDialog>
        ) : (
          <div></div>
        )
      }
      
      
      {/* Dialog chỉ upload file */}
      {uploadDialog && (
        <dialog
          open
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setUploadDialog(false)} // click ngoài dialog đóng
        >
          <form
            onSubmit={(e) => { e.preventDefault();
              if (!operating)
              {
                if (binFile && segmentFile) {
                  openOperatingDialog(save())
                  setUploadDialog(false)
                }
              }
             }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => e.stopPropagation()} // click trong form không đóng dialog
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload Sample</h3>
              <button type="button" onClick={() => setUploadDialog(false)} className="p-1 rounded hover:bg-gray-100">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Select Bin File</label>
                <input
                  type="file"
                  accept=".tsv"
                  onChange={(e) => setBinFile(e.target.files?.[0] ?? null)}
                  className="mt-1 block w-full rounded border px-3 py-2"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Select Segment File</label>
                <input
                  type="file"
                  accept=".tsv"
                  onChange={(e) => setSegmentFile(e.target.files?.[0] ?? null)}
                  className="mt-1 block w-full rounded border px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Select Algorithm</label>

                <div>
                  {
                    algoId ? (
                      <div>
                        Selected Algorithm {algoId}
                      </div>
                    ) : (
                      <div></div>
                    )
                  }
                </div>
                <div>
                  {
                    algorithms.length === 0 ? (
                      <div className="text-gray-500 text-sm text-center py-4">
                        No algorithms yet. Click + to add one.
                      </div>
                    ) : (
                      
                      <div className="overflow-y-auto max-h-50 space-y-2">
                        {
                          algorithms.map((algo) => {
                            const isSelected = algo.id !== undefined && algo.id === algoId;
                            return (
                            <div
                              key={algo.id}
                              role="button"
                              onClick={() => setAlgoId(algo.id)}
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
                        }
                      </div>
                    )}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadDialog(false)}
                  className="px-3 py-2 rounded border hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700"
                >
                  {
                    operating ? (
                      <div>
                        Uploading
                      </div>
                    ) : (
                      <div>
                        Upload
                      </div>
                    )
                  }
                </button>
              </div>
            </div>
          </form>
        </dialog>
      )}
      
      {/* Dialog xóa */}
      {removeDialog && (
        <dialog
          open
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={ () => setRemoveDialog(false) } // click ngoài dialog đóng
        >
          <form
            onSubmit={(e) => { e.preventDefault(); save(); }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={
              (e) => {
                if (!operating) {
                  e.stopPropagation();
                  openOperatingDialog(removeResults(selectedIds));
                  setRemoveDialog(false);
                }
                
              }
            } // click trong form không đóng dialog
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">You sure want to remove these samples</h3>
            </div>

            <div className="space-y-4">
              <div className="overflow-y-auto max-h-50">
                {
                  results.map((r) => {
                      const isSelected = r.id !== undefined && selectedIds.has(r.id);
                      if (isSelected)
                      {
                        return (
                          <div 
                          key={r.id} 
                          className={`border p-2 rounded shadow-sm transition-colors 'bg-white hover:bg-gray-50'`}
                          >
                            <div className="font-medium">{r.id}</div>
                            <div className="font-medium">{r.reference_genome}</div>
                            <div className="font-medium">{r.algorithm_name}</div>
                          </div>
                        )
                      }
                      
                    }
                  )
                }
              </div>
              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRemoveDialog(false)}
                  className="px-3 py-2 rounded border hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700"
                >
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
