// SampleBinTable.tsx
import React from "react";
import { Paper, SxProps, Theme, Button, Box } from "@mui/material";
import { DataGrid, GridColDef, GridRowsProp } from "@mui/x-data-grid";

import { SampleBin } from "@/types/result";
import { CHROMOSOME_ORDER, sortByChromosome } from "@/utils/chromosomeSort";

type Props = {
  data: SampleBin[];
  dense?: boolean;
  onRowClick?: (row: SampleBin) => void;
  fullHeight?: boolean;
  sx?: SxProps<Theme>;
};

export default function SampleBinTable({ data, dense = false, onRowClick, fullHeight = false, sx }: Props) {
  // Define columns for DataGrid
  const columns: GridColDef[] = React.useMemo(
    () => [
      {
        field: "chromosome",
        headerName: "Chromosome",
        width: 140,
        minWidth: 80,
        resizable: true,
        align: "left",
        headerAlign: "left",
        sortComparator: (a, b) => {
          const orderA = CHROMOSOME_ORDER[a] ?? 999;
          const orderB = CHROMOSOME_ORDER[b] ?? 999;
          return orderA - orderB;
        },
      },
      {
        field: "start",
        headerName: "Start",
        type: "number",
        width: 110,
        minWidth: 80,
        resizable: true,
        align: "left",
        headerAlign: "left",
      },
      {
        field: "end",
        headerName: "End",
        type: "number",
        width: 110,
        minWidth: 80,
        resizable: true,
        align: "left",
        headerAlign: "left",
      },
      {
        field: "copy_number",
        headerName: "Copy Number",
        type: "number",
        width: 130,
        minWidth: 90,
        resizable: true,
        align: "left",
        headerAlign: "left",
      },
      {
        field: "read_count",
        headerName: "Read Count",
        type: "number",
        width: 130,
        minWidth: 90,
        resizable: true,
        align: "left",
        headerAlign: "left",
      },
      {
        field: "gc_content_percent",
        headerName: "GC-content",
        type: "number",
        width: 100,
        minWidth: 80,
        resizable: true,
        align: "left",
        headerAlign: "left",
        valueFormatter: (value) => {
          return value != null ? Number(value).toFixed(2) + "%" : "-";
        },
      },
    ],
    []
  );

  // Transform data to rows with unique IDs
  const rows: GridRowsProp = React.useMemo(() => {
    // Sort by chromosome first, then by start position
    const sortedData = sortByChromosome(data);

    return sortedData.map((row, index) => ({
      id: row.id ?? `row-${index}`,
      chromosome: typeof row.chromosome === "string" ? row.chromosome : JSON.stringify(row.chromosome),
      start: row.start,
      end: row.end,
      copy_number: row.copy_number,
      read_count: row.read_count,
      gc_content_percent: row.gc_content != null ? row.gc_content * 100 : null,
      _original: row, // Store original data for onRowClick
    }));
  }, [data]);

  // --- CSV Export Logic ---
  const handleExportCSV = () => {
    const headers = ["Chromosome", "Start", "End", "Copy #", "Read Count", "GC %"];
    const csvContent = rows.map((row) => {
      return [row.chromosome, row.start, row.end, row.copy_number, row.read_count, row.gc_content_percent != null ? Number(row.gc_content_percent).toFixed(2) : ""].join(",");
    });
    const csvString = [headers.join(","), ...csvContent].join("\n");
    const blob = new Blob(["\uFEFF" + csvString], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `sample_bin_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        height: fullHeight ? "100%" : "auto",
        maxHeight: fullHeight ? undefined : "120vh",
        overflow: "hidden",
        ...sx,
      }}
    >
      {/* --- TOOLBAR --- */}
      <Box
        sx={{
          p: 1,
          pr: 2,
          display: "flex",
          justifyContent: "flex-end",
          borderBottom: "1px solid #e0e0e0",
          flexShrink: 0,
        }}
      >
        <Button
          variant="outlined"
          size="small"
          onClick={handleExportCSV}
          sx={{
            fontSize: "0.75rem",
            padding: "2px 8px",
            minWidth: "auto",
            height: "28px",
            textTransform: "none",
          }}
        >
          Export CSV
        </Button>
      </Box>

      {/* DataGrid */}
      <Box sx={{ flexGrow: 1, width: "100%", height: fullHeight ? "100%" : 600 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          density={dense ? "compact" : "standard"}
          disableRowSelectionOnClick
          onRowClick={(params) => {
            if (onRowClick) {
              onRowClick(params.row._original);
            }
          }}
          sx={{
            border: "none",
            "& .MuiDataGrid-columnHeader": {
              fontSize: "15px",
              lineHeight: 1.5,
              color: "#2F5EA3",
            },
            "& .MuiDataGrid-columnHeaderTitle": {
              fontWeight: "600 !important",
            },
            "& .MuiDataGrid-cell": {
              fontSize: "14px",
              fontWeight: "500 !important",
            },
            "& .MuiDataGrid-cell:hover": {
              cursor: onRowClick ? "pointer" : "default",
            },
          }}
        />
      </Box>
    </Paper>
  );
}
