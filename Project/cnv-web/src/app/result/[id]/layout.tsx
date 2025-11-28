"use client";

import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { resultAPI } from "@/services/result.api";
import { ResultReportResponse } from "@/types/result";
import {
  exportToXlsx,
  exportToDocx,
  exportToPdf,
} from "@/utils/documentExporter";
import { ResultReport } from "@/features/result/ResultReport";

const ResultDetailPageLayout: React.FC = () => {
  const { id } = useParams();

  const [resultReport, setResultReport] = useState<ResultReportResponse | null>(
    null
  );
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Fetch the report for the selected result
  useEffect(() => {
    if (!id) return;

    const fetchReport = async () => {
      try {
        setReportLoading(true);
        setReportError(null);
        const report = await resultAPI.getReport(id as string);
        setResultReport(report);
      } catch (err: any) {
        setReportError(err.message || "Failed to fetch result report");
      } finally {
        setReportLoading(false);
      }
    };

    fetchReport();
  }, [id]);

  // Handle export menu open

  return (
    <ResultReport
      loading={reportLoading}
      error={reportError}
      report={resultReport}
      exportToDocx={exportToDocx}
      exportToXlsx={exportToXlsx}
      exportToPdf={exportToPdf}
    />
  );
};

export default ResultDetailPageLayout;
