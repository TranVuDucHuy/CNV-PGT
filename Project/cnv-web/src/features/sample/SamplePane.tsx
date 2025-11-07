"use client";

import React, { useEffect } from "react";
import { Plus, Minus, Edit3, X } from "lucide-react";
import useSampleHandle from "./sampleHandle";

export default function SamplePane() {
  const {
    samples,
    isOpen,
    open,
    close,
    setFile,
    save,
    removeLast,
  } = useSampleHandle();

  useEffect(() => {
    // close on Escape handled inside hook via isOpen effect if needed, keep for safety
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  return (
    <details open className="border rounded-md">
      <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
        <span>Sample</span>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => { e.preventDefault(); open(); }}
            title="Add"
            className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
          >
            <Plus size={16} />
          </button>
          <button
            onClick={(e) => { e.preventDefault(); removeLast(); }}
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

      <div className="p-3 space-y-2">
        {samples.length === 0 ? (
          <div className="text-gray-500 text-sm text-center py-4">No samples yet. Click + to add one.</div>
        ) : (
          samples.map((s, i) => (
            <div key={s.id} className="border p-2 rounded bg-white shadow-sm">
              <div className="font-medium">{}</div>
              
            </div>
          ))
        )}
      </div>

      {/* Dialog chỉ upload file */}
      {isOpen && (
        <dialog
          open
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={close} // click ngoài dialog đóng
        >
          <form
            onSubmit={(e) => { e.preventDefault(); save(); }}
            method="dialog"
            className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative"
            onClick={(e) => e.stopPropagation()} // click trong form không đóng dialog
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
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="mt-1 block w-full rounded border px-3 py-2"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={close}
                  className="px-3 py-2 rounded border hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700"
                >
                  Upload
                </button>
              </div>
            </div>
          </form>
        </dialog>
      )}

    </details>
  );
}
