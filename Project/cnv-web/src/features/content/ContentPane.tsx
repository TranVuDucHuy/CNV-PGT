"use client";

import React, { useMemo } from "react";
import { useSelector } from "react-redux";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import SampleSegmentTable from "./viewpanes/SampleSegmentTable";
import DraggableWindow from "@/components/DraggableWindow";
import { SampleBin, SampleSegment } from "@/types/result";
import CNVChart from "./viewpanes/CNVChart";
import { RootState } from "@/utils/store";
import { Typography, Box, Divider } from "@mui/material";

export default function ContentPane() {
  const { checked, setChecked } = useViewHandle();
  
  // Lấy danh sách ID từ Redux
  const selectedResultIds = useSelector((state: RootState) => state.app.selectedResults);
  const { selectedResultDto, resultDtos } = useResultHandle();

  const [bins, setBins] = React.useState<SampleBin[]>([]);
  const [segments, setSegments] = React.useState<SampleSegment[]>([]);

  // Logic cho single view (Bin/Segment Table)
  React.useEffect(() => {
    const srcBins = selectedResultDto?.bins ?? [];
    const srcSegments = selectedResultDto?.segments ?? [];
    const copyBins = Array.isArray(srcBins) ? structuredCloneSafe(srcBins) : [];
    const copySegments = Array.isArray(srcSegments) ? structuredCloneSafe(srcSegments) : [];
    setBins(copyBins);
    setSegments(copySegments);
  }, [selectedResultDto]);

  // Logic cho multi-chart view
  const multiChartData = useMemo(() => {
    if (selectedResultIds.length === 0) return [];
    return resultDtos.filter(dto => dto.id && selectedResultIds.includes(dto.id));
  }, [selectedResultIds, resultDtos]);

  function structuredCloneSafe<T>(v: T): T {
    try { return structuredClone(v); } catch { return JSON.parse(JSON.stringify(v)); }
  }

  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const zIndexRef = React.useRef<number>(100);
  const [windowsOrder, setWindowsOrder] = React.useState<string[]>([]);

  React.useEffect(() => {
    const ids: string[] = [];
    if (checked.bin) ids.push("bin");
    if (checked.segment) ids.push("segment");
    if (checked.table) ids.push("table");
    setWindowsOrder((prev) => {
      const merged = [...prev.filter((p) => ids.includes(p)), ...ids.filter((i) => !prev.includes(i))];
      return merged;
    });
  }, [checked.bin, checked.segment, checked.table]);

  const bringToFront = (id: string) => {
    zIndexRef.current += 1;
    setWindowsOrder((prev) => [...prev.filter((p) => p !== id), id]);
  };

  const defaults: Record<string, Partial<{ top: number; left: number; width: number; height: number }>> = {
    bin: { top: 16, left: 16, width: 740, height: 360 },
    segment: { top: 56, left: 76, width: 740, height: 360 },
    table: { top: 20, left: 100, width: 900, height: 700 }, // Window to hơn chút để chứa nhiều biểu đồ
  };

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden bg-gray-100">
      {!checked.bin && !checked.segment && !checked.table && (
        <div className="w-full h-full flex items-center justify-center">
          <span className="text-gray-400">Select an item and toggle views to start</span>
        </div>
      )}

      {/* --- BIN TABLE --- */}
      {checked.bin && (
        <DraggableWindow
          key={selectedResultDto ? `bin-${selectedResultDto.id}` : "bin-none"}
          id="bin"
          title={`Bins: ${selectedResultDto?.sample_name ?? ""}`}
          initial={defaults.bin}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, bin: false })}
          onBringToFront={() => bringToFront("bin")}
          zIndex={windowsOrder.indexOf("bin") >= 0 ? 100 + windowsOrder.indexOf("bin") : 100}
        >
          <div className="w-full h-full bg-white">
            <SampleBinTable data={bins} dense fullHeight />
          </div>
        </DraggableWindow>
      )}

      {/* --- SEGMENT TABLE --- */}
      {checked.segment && (
        <DraggableWindow
          key={selectedResultDto ? `segment-${selectedResultDto.id}` : "segment-none"}
          id="segment"
          title={`Segments: ${selectedResultDto?.sample_name ?? ""}`}
          initial={defaults.segment}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, segment: false })}
          onBringToFront={() => bringToFront("segment")}
          zIndex={windowsOrder.indexOf("segment") >= 0 ? 100 + windowsOrder.indexOf("segment") : 100}
        >
          <div className="w-full h-full bg-white">
            <SampleSegmentTable data={segments} dense fullHeight />
          </div>
        </DraggableWindow>
      )}

      {/* --- MULTI CHART WINDOW --- */}
      {checked.table && (
        <DraggableWindow
          key={`multi-chart-${selectedResultIds.join("-")}`} 
          id="table"
          title={`CNV Analysis Charts (${multiChartData.length})`}
          initial={defaults.table}
          containerRef={containerRef}
          onClose={() => setChecked?.({ ...checked, table: false })}
          onBringToFront={() => bringToFront("table")}
          zIndex={windowsOrder.indexOf("table") >= 0 ? 100 + windowsOrder.indexOf("table") : 100}
        >
          {/* Scrollable Container */}
          <div className="w-full h-full overflow-y-auto bg-gray-50 p-4">
            {multiChartData.length === 0 ? (
               <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                  <Typography color="textSecondary">Loading or no data selected...</Typography>
               </Box>
            ) : (
              <div className="flex flex-col gap-6">
                {multiChartData.map((dto, index) => (
                  <Box 
                    key={dto.id} 
                    sx={{ 
                      bgcolor: 'white', 
                      p: 2, 
                      borderRadius: 2, 
                      boxShadow: 1,
                      border: '1px solid #e0e0e0',
                      // QUAN TRỌNG: flexShrink 0 để không bị co lại khi list dài
                      flexShrink: 0,
                      display: 'flex',
                      flexDirection: 'column'
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                       <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {index + 1}. {dto.sample_name}
                       </Typography>
                       <Typography variant="caption" color="textSecondary" sx={{ bgcolor: '#f0f0f0', px: 1, borderRadius: 1 }}>
                          {dto.algorithm_name}
                       </Typography>
                    </Box>
                    
                    <Divider sx={{ mb: 2 }} />

                    {/* Container cho biểu đồ - Set chiều cao cố định TẠI ĐÂY */}
                    <Box sx={{ height: 350, width: '100%', position: 'relative' }}>
                      <CNVChart 
                        bins={dto.bins || []} 
                        segments={dto.segments || []} 
                        // Không cần title trong chart nữa vì đã có header ở trên
                      />
                    </Box>
                  </Box>
                ))}
                {/* Khoảng trống dưới cùng để scroll thoải mái */}
                <div className="h-4 w-full"></div>
              </div>
            )}
          </div>
        </DraggableWindow>
      )}
    </div>
  );
}