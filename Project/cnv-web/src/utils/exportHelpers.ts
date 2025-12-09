import { SampleBin, SampleSegment } from "@/types/result";
import html2canvas from "html2canvas";

/**
 * Export bins to CSV format
 */
export const exportBinsToCSV = (bins: SampleBin[], fileName: string) => {
  const headers = ["Chromosome", "Start", "End", "Copy Number", "Read Count", "GC-content"];
  const csvContent = bins.map((row) => {
    const gcPercent = row.gc_content != null ? (row.gc_content * 100).toFixed(2) : "";
    return [row.chromosome, row.start, row.end, row.copy_number, row.read_count, gcPercent].join(",");
  });
  const csvString = [headers.join(","), ...csvContent].join("\n");
  downloadCSV(csvString, fileName);
};

/**
 * Export segments to CSV format
 */
export const exportSegmentsToCSV = (segments: SampleSegment[], fileName: string) => {
  const headers = ["Chromosome", "Start", "End", "Copy Number", "Confidence", "Man Change"];
  const csvContent = segments.map((row) => {
    const confidence = row.confidence != null ? row.confidence.toFixed(4) : "";
    const manChange = row.man_change ? "Yes" : "No";
    return [row.chromosome, row.start, row.end, row.copy_number, confidence, manChange].join(",");
  });
  const csvString = [headers.join(","), ...csvContent].join("\n");
  downloadCSV(csvString, fileName);
};

/**
 * Export chart element to PNG format
 * @param elementId - The ID of the HTML element containing the chart
 * @param fileName - The name of the exported file
 */
export const exportChartToPNG = async (elementId: string, fileName: string) => {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with id "${elementId}" not found`);
    return;
  }

  try {
    const canvas = await html2canvas(element, {
      backgroundColor: "#ffffff",
      scale: 2,
      ignoreElements: (el) => el.hasAttribute("data-html2canvas-ignore"),
    });

    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Chart export failed:", error);
  }
};

/**
 * Helper function to download CSV file
 */
const downloadCSV = (csvString: string, fileName: string) => {
  const blob = new Blob(["\uFEFF" + csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", fileName);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
