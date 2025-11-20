// dashboard.tsx
"use client";

import React from "react";
import SamplePane from "@/features/sample/SamplePane";
import AlgorithmPane from "@/features/algorithm/AlgorithmPane";
import ResultPane from "@/features/result/ResultPane";
import ViewPane from "@/features/view/ViewPane";
import ContentPane from "@/features/content/ContentPane";
import { ViewProvider } from "@/features/view/viewHandle";
import ReferencePane from "@/features/reference/ReferencePane";
import useSampleHandle from "@/features/sample/sampleHandle";

const DashboardView: React.FC = () => {
  const { samples, refresh } = useSampleHandle();
  return (
    <div className="flex flex-col h-screen font-sans">
      {/* Menu Bar */}
      <nav className="bg-gray-200 border-b border-gray-400 px-4 py-2 flex items-center">
        <h1 className="text-lg font-bold">CNV Analysis Dashboard</h1>
      </nav>

      {/* Split Pane */}
      <div className="flex flex-1">
        <ViewProvider>
          {/* Left Pane */}
          <div className="w-60 border-r border-gray-300 bg-gray-50 p-3 overflow-y-auto space-y-3">
            <SamplePane />
            <ReferencePane samples={samples} onRefresh={refresh} />            
            <AlgorithmPane />
            <ResultPane />
            <ViewPane />
          </div>

          {/* Right Pane - Content Area (now full-size) */}
          <div className="flex-1 bg-gray-100 flex">
            <div
              id="contentArea"
              className="w-full h-full bg-gray-200 border rounded-lg flex flex-col p-3"
            >
              <ContentPane />
            </div>
          </div>
        </ViewProvider>
      </div>
    </div>
  );
};

export default DashboardView;
