"use client";

import { useEffect, useMemo, useState } from "react";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import SampleSegmentTable from "./viewpanes/SampleSegmentTable";
import {
  CycleReportResponse,
  ResultDto,
  ResultReportResponse,
  SampleBin,
  SampleSegment,
} from "@/types/result";
import CNVChart from "./viewpanes/CNVChart";
import DynamicStack from "@/components/DynamicStack";
import { ResultReport } from "../result/ResultReport";
import { resultAPI } from "@/services";
import {
  exportToXlsx,
  exportToDocx,
  exportToPdf,
  exportCycleReportToDocx,
  exportCycleReportToXlsx,
  exportCycleReportToPdf,
} from "@/utils/documentExporter";
import { CycleReport } from "../result/CycleReport";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/utils/store";
import { setViewOption, removeSelectedResult } from "@/utils/appSlice";
import { parseSampleNameToParts } from "../sample/sampleUtils";

const defaultHeights = {
  bin: 400,
  segment: 400,
  table: 500,
  report: 600,
};

export default function TiledContentPane() {
  const checked = useSelector((state: RootState) => state.app.viewChecked);
  const selectedResultIds = useSelector((state: RootState) => state.app.selectedResults);
  const dispatch = useDispatch()
  
  // 1. Lấy thêm resultDtos từ hook
  const { selectedResultDto, resultDtos } = useResultHandle();

  const [bins, setBins] = useState<SampleBin[]>([]);
  const [segments, setSegments] = useState<SampleSegment[]>([]);

  const [resultReport, setResultReport] = useState<ResultReportResponse | null>(
    null
  );

  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  const [cycleReport, setCycleReport] = useState<CycleReportResponse | null>(
    null
  );
  const [cycleReportLoading, setCycleReportLoading] = useState(false);
  const [cycleReportError, setCycleReportError] = useState<string | null>(null);

  useEffect(() => {
    const srcBins = selectedResultDto?.bins ?? [];
    const srcSegments = selectedResultDto?.segments ?? [];

    const copyBins = Array.isArray(srcBins) ? structuredCloneSafe(srcBins) : [];
    const copySegments = Array.isArray(srcSegments)
      ? structuredCloneSafe(srcSegments)
      : [];

    setBins(copyBins);
    setSegments(copySegments);

    if (!selectedResultDto) {
      setResultReport(null);
      setReportError(null);
      setReportLoading(false);
      return;
    }

    loadReport(selectedResultDto.id);
  }, [selectedResultDto]);

  useEffect(() => {
    if (selectedResultIds.length === 0) {
      setCycleReport(null);
      setCycleReportError(null);
      setCycleReportLoading(false);
      return;
    }

    loadCycleReport(selectedResultIds);
  }, [selectedResultIds]);

  // helper for structured clone fallback
  function structuredCloneSafe<T>(v: T): T {
    try {
      // @ts-ignore
      return structuredClone(v);
    } catch {
      return JSON.parse(JSON.stringify(v));
    }
  }

  const loadReport = (resultId: string) => {
    setReportLoading(true);
    setReportError(null);
    resultAPI
      .getReport(resultId)
      .then((report) => {
        setResultReport(report);
      })
      .catch((err: any) => {
        setReportError(err.message || "Failed to fetch result report");
      })
      .finally(() => {
        setReportLoading(false);
      });
  };

  const loadCycleReport = (resultIds: string[]) => {
    setCycleReportLoading(true);
    setCycleReportError(null);

    resultAPI
      .getCycleReport(resultIds)
      .then((report) => {
        setCycleReport(report);
      })
      .catch((err: any) => {
        setCycleReportError(err.message || "Failed to fetch cycle report");
      })
      .finally(() => {
        setCycleReportLoading(false);
      });
  };

  const items = useMemo(() => {
    const res = [];
    // Các phần Table và Report giữ nguyên (hiển thị cho selectedResultDto hoặc logic cũ)
    if (checked.bin) {
      res.push({
        id: "bin",
        title: `Sample Bins ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.bin,
        content: <SampleBinTable data={bins} dense fullHeight />,
        onClose: () => dispatch(setViewOption({key: "bin", value: false}))
      });
    }
    if (checked.segment) {
      res.push({
        id: "segment",
        title: `Sample Segments ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.segment,
        content: <SampleSegmentTable data={segments} dense fullHeight />,
        onClose: () => dispatch(setViewOption({key: "segment", value: false}))
      });
    }

    // 2. Logic hiển thị Chart: Lặp qua resultDtos để tạo nhiều chart xếp chồng
    if (checked.chart) {
      // Ưu tiên dùng resultDtos (danh sách chọn), nếu không có thì fallback về selectedResultDto (chọn đơn)
      const chartTargets: ResultDto[] = []

      for (let i = 0; i < selectedResultIds.length; i++) {
        for (let j = 0; j < resultDtos.length; j++) {
          if (resultDtos[j].id == selectedResultIds[i]) {
            
            chartTargets.push(resultDtos[j])
          }
        }
      }

      let cycle = null
      let canShow = true
      for (let i = 0; i < chartTargets.length; i++) {
        const parts = parseSampleNameToParts(chartTargets[i].sample_name)
        if (!cycle) {
          cycle = parts.cycle
        }
        else {
          if (cycle !== parts.cycle) {
            canShow = false
            break
          }
        }
      }

      if (canShow) {
        chartTargets.forEach((dto) => {
          res.push({
            id: `chart-${dto.id}`, // Tạo ID duy nhất cho mỗi chart pane
            title: `Sample Chart ${dto.sample_name} - ${dto.algorithm_name}`,
            initialHeight: defaultHeights.table,
            content: (
              <CNVChart 
                bins={dto.bins ?? []} 
                segments={dto.segments ?? []} 
                sx={{ height: "100%" }} 
              />
            ),
            // Khi tắt chart, ta tắt cờ 'chart' trong view handle (ẩn tất cả chart)
            onClose: () => {
              dispatch(removeSelectedResult(dto.id))
              if (selectedResultIds.length == 1) {
                dispatch(setViewOption({key: "chart", value: false}))
              }
            }
          });
        });
      }
      else {
        res.push({
          id: `chart-none`,
            title: `Sample Chart None`,
            initialHeight: defaultHeights.table,
            content: (
              <div>
                Results have to have same cycle
              </div>
            )
        })
      }
    }

    if (checked.report) {
      res.push({
        id: "report",
        title: `Sample Report ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.report,
        content: (
          <ResultReport
            loading={reportLoading}
            error={reportError}
            report={resultReport}
            exportToDocx={exportToDocx}
            exportToXlsx={exportToXlsx}
            exportToPdf={exportToPdf}
            sx={{ height: "100%" }}
          />
        ),
        onClose: () => dispatch(setViewOption({key: "report", value: false}))
      });
    }

    if (checked.cycleReport) {
      res.push({
        id: "cycleReport",
        title: `Cycle Report ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.report,
        content: (
          <CycleReport
            loading={cycleReportLoading}
            error={cycleReportError}
            report={cycleReport}
            exportToDocx={exportCycleReportToDocx}
            exportToXlsx={exportCycleReportToXlsx}
            exportToPdf={exportCycleReportToPdf}
            sx={{ height: "100%" }}
          />
        ),
        onClose: () => dispatch(setViewOption({key: "cycleReport", value: false}))
      });
    }

    return res;
  }, [
    checked,
    selectedResultDto,
    resultDtos, // Thêm dependency này
    bins,
    segments,
    reportLoading,
    reportError,
    resultReport,
    cycleReportLoading,
    cycleReportError,
    cycleReport,
  ]);

  return (
    <DynamicStack
      sx={{
        width: "100%",
        padding: 2,
      }}
      items={items}
    />
  );
}