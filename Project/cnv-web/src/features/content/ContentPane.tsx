// ContentPane.tsx
"use client";

import React from "react";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import SampleSegmentTable from "./viewpanes/SampleSegmentTable";
import DraggableWindow from "@/components/DraggableWindow";
import { SampleBin, SampleSegment } from "@/types/result";

export default function ContentPane() {
  const { checked, setChecked } = useViewHandle(); // presumes setChecked exists
  const { resultDtos } = useResultHandle();

  const [bins, setBins] = React.useState<SampleBin[]>([]);
  const [segments, setSegments] = React.useState<SampleSegment[]>([]);

  React.useEffect(() => {
    const newBins = resultDtos?.[0]?.bins ?? [];
    setBins(newBins);
    const newSegments = resultDtos?.[0]?.segments ?? [];
    setSegments(newSegments);
  }, [resultDtos]);

  // container ref to restrict windows
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  // z-index management
  const zIndexRef = React.useRef<number>(100);
  const [windowsOrder, setWindowsOrder] = React.useState<string[]>([]); // order of ids, last = top

  // initialize ordering when check changes
  React.useEffect(() => {
    const ids: string[] = [];
    if (checked.bin) ids.push("bin");
    if (checked.segment) ids.push("segment");
    setWindowsOrder((prev) => {
      // keep prev order for existing ones, append new ones
      const merged = [...prev.filter((p) => ids.includes(p)), ...ids.filter((i) => !prev.includes(i))];
      return merged;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checked.bin, checked.segment]);

  const bringToFront = (id: string) => {
    zIndexRef.current += 1;
    setWindowsOrder((prev) => [...prev.filter((p) => p !== id), id]);
  };

  // default positions (so windows don't fully overlap)
  const defaults: Record<string, Partial<{ top: number; left: number; width: number; height: number }>> = {
    bin: { top: 16, left: 16, width: 740, height: 360 },
    segment: { top: 56, left: 76, width: 740, height: 360 },
  };

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {/* when none checked */}
      {!checked.bin && !checked.segment && (
        <div className="w-full h-full flex items-center justify-center">
          <span className="text-gray-600">Content Area</span>
        </div>
      )}

      {/* SampleBin window */}
      {checked.bin && (
        <DraggableWindow
          id="bin"
          title="Sample Bins"
          initial={defaults.bin}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, bin: false })}
          onBringToFront={() => bringToFront("bin")}
          zIndex={windowsOrder.indexOf("bin") >= 0 ? 100 + windowsOrder.indexOf("bin") : 100}
        >
          {/* make table fill window content: pass fullHeight so table uses available space */}
          <div className="w-full h-full">
            <SampleBinTable data={bins} dense fullHeight />
          </div>
        </DraggableWindow>
      )}

      {/* SampleSegment window */}
      {checked.segment && (
        <DraggableWindow
          id="segment"
          title="Sample Segments"
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
    </div>
  );
}
