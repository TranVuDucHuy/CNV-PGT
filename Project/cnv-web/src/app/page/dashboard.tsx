"use client";

import React, { useState } from "react";
import { Plus, Minus, Edit3, StepForward, Download } from "lucide-react";

const DashboardView: React.FC = () => {
  const [samples, setSamples] = useState<string[]>([]);
  const [checked, setChecked] = useState({
    baseline: false,
    bicSeq2: false,
    wisecondorX: false,
    blueFuse: false,
    scatterChart: false,
    boxPlot: false,
    dataTable: false,
    report: false,
  });

  const handleAddSample = () => {
    const newSample = `Sample ${samples.length + 1}`;
    setSamples([...samples, newSample]);
  };

  const toggleCheck = (key: keyof typeof checked) => {
    setChecked({ ...checked, [key]: !checked[key] });
    console.log(`Toggled ${key}:`, !checked[key]);
  };

  return (
    <div className="flex flex-col h-screen font-sans">

      {/* Menu Bar */}
      <nav className="bg-gray-200 border-b border-gray-400 px-4 py-2 flex items-center">
        <div className="relative group">
          <span className="cursor-pointer font-semibold">Sample ▾</span>
          <ul className="absolute hidden group-hover:block bg-white border mt-1 shadow-md">
            <li>
              <button
                onClick={handleAddSample}
                className="px-4 py-2 hover:bg-gray-100 w-full text-left"
              >
                Add
              </button>
            </li>
            <li>
              <button className="px-4 py-2 hover:bg-gray-100 w-full text-left">
                Delete
              </button>
            </li>
          </ul>
        </div>
      </nav>

      {/* Split Pane */}
      <div className="flex flex-1">

        {/* Left Pane */}
        <div className="w-60 border-r border-gray-300 bg-gray-50 p-3 overflow-y-auto space-y-3">

          

          {/* Sample Section */}
          <details open className="border rounded-md">
            <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
              <span>Sample</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleAddSample}
                  title="Add"
                  className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
                >
                  <Plus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      setSamples(samples.slice(0, -1));
                    }
                  }}
                  title="Remove"
                  className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
                >
                  <Minus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      const newSamples = [...samples];
                      newSamples[newSamples.length - 1] += " (edited)";
                      setSamples(newSamples);
                    }
                  }}
                  title="Edit"
                  className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
                >
                  <Edit3 size={16} />
                </button>
              </div>
            </summary>

            <div className="p-3 space-y-2">
              {samples.map((s, i) => (
                <div key={i} className="border p-2 rounded bg-white shadow-sm">
                  {s}
                </div>
              ))}
            </div>
          </details>



          {/* Algorithm Section */}
          <details open className="border rounded-md">
            <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
              <span>Algorithm</span>
              <div className="flex items-center gap-2">
                <button
                  
                  title="Add"
                  className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
                >
                  <Plus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      setSamples(samples.slice(0, -1));
                    }
                  }}
                  title="Remove"
                  className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
                >
                  <Minus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      const newSamples = [...samples];
                      newSamples[newSamples.length - 1] += " (edited)";
                      setSamples(newSamples);
                    }
                  }}
                  title="Edit"
                  className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
                >
                  <Edit3 size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      const newSamples = [...samples];
                      newSamples[newSamples.length - 1] += " (edited)";
                      setSamples(newSamples);
                    }
                  }}
                  title="Edit"
                  className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
                >
                  <StepForward size={16} />
                </button>
              </div>
            </summary>

            <div className="p-3 space-y-2">
              {/* {samples.map((s, i) => (
                <div key={i} className="border p-2 rounded bg-white shadow-sm">
                  {s}
                </div>
              ))} */}
            </div>
          </details>

          {/* Result Section */}
          <details open className="border rounded-md">
            <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer flex items-center justify-between">
              <span>Result</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleAddSample}
                  title="Add"
                  className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
                >
                  <Plus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      setSamples(samples.slice(0, -1));
                    }
                  }}
                  title="Remove"
                  className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
                >
                  <Minus size={16} />
                </button>
                <button
                  onClick={() => {
                    if (samples.length > 0) {
                      const newSamples = [...samples];
                      newSamples[newSamples.length - 1] += " (edited)";
                      setSamples(newSamples);
                    }
                  }}
                  title="Export"
                  className="p-1 bg-blue-500 hover:bg-blue-600 text-white rounded"
                >
                  <Download size={16} />
                </button>
              </div>
            </summary>

            <div className="p-3 space-y-2">
              {samples.map((s, i) => (
                <div key={i} className="border p-2 rounded bg-white shadow-sm">
                  {s}
                </div>
              ))}
            </div>
          </details>
          {/* View Section */}
          <details open className="border rounded-md">
            <summary className="bg-gray-300 px-3 py-2 font-semibold cursor-pointer">
              View
            </summary>
            <div className="p-3 space-y-2">
              {["bin", "segment", "aberration", "trash", "report"].map((key) => (
                <label key={key} className="block">
                  <input
                    type="checkbox"
                    checked={checked[key as keyof typeof checked]}
                    onChange={() => toggleCheck(key as keyof typeof checked)}
                    className="mr-2"
                  />
                  {key
                    .replace(/([A-Z])/g, " $1")
                    .replace(/^./, (c) => c.toUpperCase())}
                </label>
              ))}
            </div>
          </details>

          
        </div>

        {/* Right Pane */}
        <div className="flex-1 bg-gray-100 flex items-center justify-center">
          <div
            id="contentArea"
            className="w-full h-full bg-gray-200 border rounded-lg flex items-center justify-center"
          >
            <span className="text-gray-600">
              {checked.dataTable
                ? "Showing Data Table..."
                : checked.scatterChart
                ? "Scatter Chart View"
                : "Content Area"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
