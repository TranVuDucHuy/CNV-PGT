import { ResultReportResponse } from "@/types/result";
import * as XLSX from "xlsx";
import {
  Document,
  Packer,
  Paragraph,
  Table,
  TableCell,
  TableRow,
  TextRun,
  AlignmentType,
  WidthType,
  BorderStyle,
} from "docx";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

/**
 * Export ResultReportResponse to Excel (XLSX) format
 * All data in a single sheet with vertical layout
 */
export const exportToXlsx = (data: ResultReportResponse) => {
  const workbook = XLSX.utils.book_new();

  // Single sheet with all data
  const allData: any[][] = [];

  // Title
  allData.push(["CNV Analysis Report"]);
  allData.push([]);

  // Sample Information (vertical layout)
  allData.push(["Sample Information"]);
  allData.push(["Flowcell ID", data.sample.flowcell_id]);
  allData.push(["Cycle ID", data.sample.cycle_id]);
  allData.push(["Embryo ID", data.sample.embryo_id]);
  allData.push(["Cell Type", data.sample.cell_type]);
  allData.push(["Reference Genome", data.sample.reference_genome]);
  allData.push(["Date", data.sample.date]);
  allData.push([]);

  // Algorithm Information (vertical layout)
  allData.push(["Algorithm Information"]);
  allData.push(["Name", data.algorithm.name]);
  allData.push(["Version", data.algorithm.version]);
  allData.push([]);

  // Algorithm Parameters
  allData.push(["Parameters"]);
  allData.push(["Parameter", "Type", "Default", "Value"]);
  data.algorithm.parameters.forEach((p) => {
    allData.push([p.name, p.type, String(p.default), String(p.value)]);
  });
  allData.push([]);

  // Aberration Analysis Section
  allData.push(["Aberration Analysis"]);
  allData.push([]);

  // Summary
  allData.push(["Summary"]);
  if (
    data.aberration.aberration_summary &&
    data.aberration.aberration_summary.length > 0
  ) {
    data.aberration.aberration_summary.forEach((summary) => {
      allData.push([summary]);
    });
  } else {
    allData.push(["No aberrations detected"]);
  }
  allData.push([]);

  // Segments
  allData.push(["Segments"]);
  allData.push([
    "Chromosome",
    "Start",
    "End",
    "Copy Number",
    "Confidence",
    "Size",
    "Type",
    "Mosaicism",
    "Aberration Code",
    "Assessment",
    "Annotation",
  ]);
  data.aberration.aberration_segments.forEach((seg) => {
    allData.push([
      seg.chromosome,
      seg.start,
      seg.end,
      seg.copy_number,
      seg.confidence ?? "N/A",
      seg.size,
      seg.type,
      seg.mosaicism,
      seg.aberration_code,
      seg.assessment,
      seg.annotation_for_segment ?? "N/A",
    ]);
  });

  const sheet = XLSX.utils.aoa_to_sheet(allData);
  XLSX.utils.book_append_sheet(workbook, sheet, "CNV Report");

  // Generate file and trigger download
  const fileName = `CNV_Report_${data.sample.embryo_id}_${
    new Date().toISOString().split("T")[0]
  }.xlsx`;
  XLSX.writeFile(workbook, fileName);
};

/**
 * Export ResultReportResponse to Word (DOCX) format
 */
export const exportToDocx = (data: ResultReportResponse) => {
  const doc = new Document({
    sections: [
      {
        children: [
          // Title
          new Paragraph({
            text: "CNV Analysis Report",
            heading: "Heading1",
            alignment: AlignmentType.CENTER,
          }),
          new Paragraph({ text: "" }),

          // Sample Information Section (vertical layout)
          new Paragraph({
            text: "Sample Information",
            heading: "Heading2",
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              createTableRow("Flowcell ID", data.sample.flowcell_id),
              createTableRow("Cycle ID", data.sample.cycle_id),
              createTableRow("Embryo ID", data.sample.embryo_id),
              createTableRow("Cell Type", data.sample.cell_type),
              createTableRow("Reference Genome", data.sample.reference_genome),
              createTableRow("Date", data.sample.date),
            ],
          }),
          new Paragraph({ text: "" }),

          // Algorithm Information Section (vertical layout)
          new Paragraph({
            text: "Algorithm Information",
            heading: "Heading2",
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              createTableRow("Name", data.algorithm.name),
              createTableRow("Version", data.algorithm.version),
            ],
          }),
          new Paragraph({ text: "" }),

          // Algorithm Parameters
          new Paragraph({
            text: "Parameters",
            heading: "Heading3",
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [
                          new TextRun({ text: "Parameter", bold: true }),
                        ],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Type", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [
                          new TextRun({ text: "Default", bold: true }),
                        ],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Value", bold: true })],
                      }),
                    ],
                  }),
                ],
              }),
              ...data.algorithm.parameters.map(
                (p) =>
                  new TableRow({
                    children: [
                      new TableCell({ children: [new Paragraph(p.name)] }),
                      new TableCell({ children: [new Paragraph(p.type)] }),
                      new TableCell({
                        children: [new Paragraph(String(p.default))],
                      }),
                      new TableCell({
                        children: [new Paragraph(String(p.value))],
                      }),
                    ],
                  })
              ),
            ],
          }),
          new Paragraph({ text: "" }),

          // Aberration Analysis Section
          new Paragraph({
            text: "Aberration Analysis",
            heading: "Heading2",
          }),

          // Summary
          new Paragraph({
            text: "Summary",
            heading: "Heading3",
          }),
          ...(data.aberration.aberration_summary &&
          data.aberration.aberration_summary.length > 0
            ? data.aberration.aberration_summary.map(
                (summary) =>
                  new Paragraph({
                    text: summary,
                    bullet: { level: 0 },
                  })
              )
            : [new Paragraph({ text: "No aberrations detected" })]),
          new Paragraph({ text: "" }),

          // Segments
          new Paragraph({
            text: "Segments",
            heading: "Heading3",
          }),
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: [
              new TableRow({
                children: [
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Chr", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Start", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "End", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "CN", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Type", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [new TextRun({ text: "Size", bold: true })],
                      }),
                    ],
                  }),
                  new TableCell({
                    children: [
                      new Paragraph({
                        children: [
                          new TextRun({ text: "Assessment", bold: true }),
                        ],
                      }),
                    ],
                  }),
                ],
              }),
              ...data.aberration.aberration_segments.map(
                (seg) =>
                  new TableRow({
                    children: [
                      new TableCell({
                        children: [new Paragraph(seg.chromosome)],
                      }),
                      new TableCell({
                        children: [new Paragraph(String(seg.start))],
                      }),
                      new TableCell({
                        children: [new Paragraph(String(seg.end))],
                      }),
                      new TableCell({
                        children: [new Paragraph(String(seg.copy_number))],
                      }),
                      new TableCell({ children: [new Paragraph(seg.type)] }),
                      new TableCell({
                        children: [new Paragraph(String(seg.size))],
                      }),
                      new TableCell({
                        children: [new Paragraph(seg.assessment)],
                      }),
                    ],
                  })
              ),
            ],
          }),
        ],
      },
    ],
  });

  // Generate and download
  Packer.toBlob(doc).then((blob) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `CNV_Report_${data.sample.embryo_id}_${
      new Date().toISOString().split("T")[0]
    }.docx`;
    link.click();
    URL.revokeObjectURL(url);
  });
};

/**
 * Export ResultReportResponse to PDF format
 */
export const exportToPdf = (data: ResultReportResponse) => {
  const doc = new jsPDF();
  let yPosition = 20;

  // Title
  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("CNV Analysis Report", 105, yPosition, { align: "center" });
  yPosition += 15;

  // Sample Information (vertical layout)
  doc.setFontSize(14);
  doc.text("Sample Information", 14, yPosition);
  yPosition += 5;

  const sampleTableData = [
    ["Flowcell ID", data.sample.flowcell_id],
    ["Cycle ID", data.sample.cycle_id],
    ["Embryo ID", data.sample.embryo_id],
    ["Cell Type", data.sample.cell_type],
    ["Reference Genome", data.sample.reference_genome],
    ["Date", data.sample.date],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [],
    body: sampleTableData,
    theme: "grid",
    styles: { fontSize: 10 },
    columnStyles: {
      0: { fontStyle: "bold", cellWidth: 50 },
      1: { cellWidth: 130 },
    },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 10;

  // Algorithm Information (vertical layout)
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Algorithm Information", 14, yPosition);
  yPosition += 5;

  const algorithmInfoData = [
    ["Name", data.algorithm.name],
    ["Version", data.algorithm.version],
  ];

  autoTable(doc, {
    startY: yPosition,
    head: [],
    body: algorithmInfoData,
    theme: "grid",
    styles: { fontSize: 10 },
    columnStyles: {
      0: { fontStyle: "bold", cellWidth: 50 },
      1: { cellWidth: 130 },
    },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 10;

  // Algorithm Parameters
  doc.setFontSize(12);
  doc.text("Parameters", 14, yPosition);
  yPosition += 5;

  const parametersData = data.algorithm.parameters.map((p) => [
    p.name,
    p.type,
    String(p.default),
    String(p.value),
  ]);

  autoTable(doc, {
    startY: yPosition,
    head: [["Parameter", "Type", "Default", "Value"]],
    body: parametersData,
    theme: "striped",
    styles: { fontSize: 9 },
    headStyles: { fillColor: [66, 139, 202] },
  });

  yPosition = (doc as any).lastAutoTable.finalY + 10;

  // Aberration Analysis Section
  if (yPosition > 250) {
    doc.addPage();
    yPosition = 20;
  }

  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.text("Aberration Analysis", 14, yPosition);
  yPosition += 10;

  // Summary
  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Summary", 14, yPosition);
  yPosition += 8;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  if (
    data.aberration.aberration_summary &&
    data.aberration.aberration_summary.length > 0
  ) {
    data.aberration.aberration_summary.forEach((summary) => {
      if (yPosition > 280) {
        doc.addPage();
        yPosition = 20;
      }
      const lines = doc.splitTextToSize(`• ${summary}`, 180);
      doc.text(lines, 14, yPosition);
      yPosition += lines.length * 6;
    });
  } else {
    doc.text("No aberrations detected", 14, yPosition);
    yPosition += 6;
  }

  yPosition += 5;

  // Segments
  if (yPosition > 250 || data.aberration.aberration_segments.length > 0) {
    doc.addPage();
    yPosition = 20;
  }

  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.text("Segments", 14, yPosition);
  yPosition += 5;

  const segmentsData = data.aberration.aberration_segments.map((seg) => [
    seg.chromosome,
    String(seg.start),
    String(seg.end),
    String(seg.copy_number),
    seg.type,
    String(seg.size),
    String(seg.mosaicism),
    seg.assessment,
  ]);

  autoTable(doc, {
    startY: yPosition,
    head: [
      ["Chr", "Start", "End", "CN", "Type", "Size", "Mosaicism", "Assessment"],
    ],
    body: segmentsData,
    theme: "striped",
    styles: { fontSize: 8 },
    headStyles: { fillColor: [66, 139, 202] },
    columnStyles: {
      0: { cellWidth: 15 },
      1: { cellWidth: 25 },
      2: { cellWidth: 25 },
      3: { cellWidth: 15 },
      4: { cellWidth: 25 },
      5: { cellWidth: 20 },
      6: { cellWidth: 25 },
      7: { cellWidth: 35 },
    },
  });

  // Save PDF
  const fileName = `CNV_Report_${data.sample.embryo_id}_${
    new Date().toISOString().split("T")[0]
  }.pdf`;
  doc.save(fileName);
};

/**
 * Helper function to create a table row for DOCX
 */
function createTableRow(label: string, value: string): TableRow {
  return new TableRow({
    children: [
      new TableCell({
        children: [
          new Paragraph({
            children: [new TextRun({ text: label, bold: true })],
          }),
        ],
        width: { size: 30, type: WidthType.PERCENTAGE },
      }),
      new TableCell({
        children: [new Paragraph(value)],
        width: { size: 70, type: WidthType.PERCENTAGE },
      }),
    ],
  });
}
