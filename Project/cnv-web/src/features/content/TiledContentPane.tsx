"use client";

import { useEffect, useMemo, useState } from "react";
import { useViewHandle } from "../view/viewHandle";
import useResultHandle from "../result/resultHandle";
import SampleBinTable from "./viewpanes/SampleBinTable";
import SampleSegmentTable from "./viewpanes/SampleSegmentTable";
import {
  CycleReportResponse,
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

const defaultHeights = {
  bin: 400,
  segment: 400,
  table: 500,
  report: 600,
};

export default function TiledContentPane() {
  const { checked } = useViewHandle();
  const { selectedResultDto } = useResultHandle();

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
      console.log("Clearing report state as report view is unchecked");
      setResultReport(null);
      setReportError(null);
      setReportLoading(false);

      setCycleReport(null);
      setCycleReportError(null);
      setCycleReportLoading(false);
      return;
    }

    Promise.all([loadReport(), loadCycleReport()]);
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

  const loadReport = () => {
    if (!selectedResultDto) return;
    setReportLoading(true);
    setReportError(null);
    resultAPI
      .getReport(selectedResultDto.id)
      .then((report) => {
        console.log("Fetched report successfully");
        setResultReport(report);
      })
      .catch((err: any) => {
        setReportError(err.message || "Failed to fetch result report");
      })
      .finally(() => {
        setReportLoading(false);
        console.log("Finished fetching report");
      });
  };

  const loadCycleReport = () => {
    if (!selectedResultDto) return;

    setCycleReportLoading(true);
    setCycleReportError(null);

    resultAPI
      .getCycleReport([selectedResultDto.id])
      .then((report) => {
        console.log("Fetched cycle report successfully: ", report);
        setCycleReport(report);
      })
      .catch((err: any) => {
        console.error("Error fetching cycle report: ", err);
        setCycleReportError(err.message || "Failed to fetch cycle report");
      })
      .finally(() => {
        setCycleReportLoading(false);
      });
  };

  const items = useMemo(() => {
    const res = [];
    if (checked.bin) {
      res.push({
        id: "bin",
        title: `Sample Bins ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.bin,
        content: <SampleBinTable data={bins} dense fullHeight />,
      });
    }
    if (checked.segment) {
      res.push({
        id: "segment",
        title: `Sample Segments ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.segment,
        content: <SampleSegmentTable data={segments} dense fullHeight />,
      });
    }
    if (checked.table) {
      res.push({
        id: "table",
        title: `Sample Table ${selectedResultDto?.sample_name} - ${selectedResultDto?.algorithm_name}`,
        initialHeight: defaultHeights.table,
        content: (
          <CNVChart bins={bins} segments={segments} sx={{ height: "100%" }} />
        ),
      });
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
      });
    }

    return res;
  }, [
    checked,
    selectedResultDto,
    bins,
    segments,
    reportLoading,
    reportError,
    resultReport,
    cycleReportLoading,
    cycleReportError,
    cycleReport,
  ]);

  // useEffect(() => {}, [bins, segments]);

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
