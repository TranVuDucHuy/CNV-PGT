// ContentPane.tsx
"use client";

import React from "react";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import SampleSegmentTable from "./viewpanes/SampleSegmentTable";
import DraggableWindow from "@/components/DraggableWindow";
import { SampleBin, SampleSegment } from "@/types/result";
import CNVChart from "./viewpanes/CNVChart";

export default function ContentPane() {
  const { checked, setChecked } = useViewHandle();
  const { selectedResultDto } = useResultHandle();

  const [bins, setBins] = React.useState<SampleBin[]>([]);
  const [segments, setSegments] = React.useState<SampleSegment[]>([]);

  React.useEffect(() => {
    const srcBins = selectedResultDto?.bins ?? [];
    const srcSegments = selectedResultDto?.segments ?? [];

    const copyBins = Array.isArray(srcBins) ? structuredCloneSafe(srcBins) : [];
    const copySegments = Array.isArray(srcSegments) ? structuredCloneSafe(srcSegments) : [];

    setBins(copyBins);
    setSegments(copySegments);
  }, [selectedResultDto]);

  // helper for structured clone fallback
  function structuredCloneSafe<T>(v: T): T {
    try {
      // @ts-ignore
      return structuredClone(v);
    } catch {
      return JSON.parse(JSON.stringify(v));
    }
  }

  // container ref to restrict windows
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  // z-index management
  const zIndexRef = React.useRef<number>(100);
  const [windowsOrder, setWindowsOrder] = React.useState<string[]>([]); // order of ids, last = top

  React.useEffect(() => {
    const ids: string[] = [];
    if (checked.bin) ids.push("bin");
    if (checked.segment) ids.push("segment");
    setWindowsOrder((prev) => {
      const merged = [...prev.filter((p) => ids.includes(p)), ...ids.filter((i) => !prev.includes(i))];
      return merged;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checked.bin, checked.segment]);

  const bringToFront = (id: string) => {
    zIndexRef.current += 1;
    setWindowsOrder((prev) => [...prev.filter((p) => p !== id), id]);
  };

  const defaults: Record<string, Partial<{ top: number; left: number; width: number; height: number }>> = {
    bin: { top: 16, left: 16, width: 740, height: 360 },
    segment: { top: 56, left: 76, width: 740, height: 360 },
  };

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {!checked.bin && !checked.segment && (
        <div className="w-full h-full flex items-center justify-center">
          <span className="text-gray-600">Content Area</span>
        </div>
      )}

      {checked.bin && (
        <DraggableWindow
          key={selectedResultDto ? `bin-${selectedResultDto.id}` : "bin-none"}
          id="bin"
          title={`Sample Bins ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`}
          initial={defaults.bin}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, bin: false })}
          onBringToFront={() => bringToFront("bin")}
          zIndex={windowsOrder.indexOf("bin") >= 0 ? 100 + windowsOrder.indexOf("bin") : 100}
        >
          <div className="w-full h-full">
            <SampleBinTable data={bins} dense fullHeight />
          </div>
        </DraggableWindow>
      )}

      {checked.segment && (
        <DraggableWindow
          key={selectedResultDto ? `segment-${selectedResultDto.id}` : "segment-none"}
          id="segment"
          title={`Sample Segments ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`}
          initial={defaults.segment}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, segment: false })}
          onBringToFront={() => bringToFront("segment")}
          zIndex={windowsOrder.indexOf("segment") >= 0 ? 100 + windowsOrder.indexOf("segment") : 100}
        >
          <div className="w-full h-full">
            <SampleSegmentTable data={segments} dense fullHeight />
          </div>
        </DraggableWindow>
      )}

      {checked.table && (
        <DraggableWindow
          key={selectedResultDto ? `table-${selectedResultDto.id}` : "table-none"}
          id="table"
          title={`Sample Table ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`}
          initial={defaults.table}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, table: false })}
          onBringToFront={() => bringToFront("table")}
          zIndex={windowsOrder.indexOf("table") >= 0 ? 100 + windowsOrder.indexOf("table") : 100}
        >
          <div className="w-full h-full">
            <CNVChart bins={bins} segments={segments} />
          </div>
        </DraggableWindow>
      )}
    </div>
  );
}
