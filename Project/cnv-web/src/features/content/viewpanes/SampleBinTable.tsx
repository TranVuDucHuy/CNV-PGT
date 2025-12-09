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

  return (
    <Paper
      sx={{
        display: "flex",
        flexDirection: "column",
        height: fullHeight ? "100%" : "auto",
        maxHeight: fullHeight ? undefined : "120vh",
        overflow: "hidden",
        ...sx,
        bgcolor: "#FAFAFA",
      }}
    >
      {/* DataGrid */}
      <Box sx={{ flexGrow: 1, width: "100%", minHeight: 0, overflow: "hidden", p: 2, pb: 4 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          density={dense ? "compact" : "standard"}
          disableRowSelectionOnClick
          hideFooterPagination
          hideFooter
          onRowClick={(params) => {
            if (onRowClick) {
              onRowClick(params.row._original);
            }
          }}
          sx={{
            height: "100%",
            border: `1px solid #D1D5DB`,
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
