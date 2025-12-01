// SampleBinTable.tsx
import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TableSortLabel,
  SxProps,
  Theme,
  Button,
  Box,
} from "@mui/material";

import { SampleBin } from "@/types/result";

type Order = "asc" | "desc";

type Props = {
  data: SampleBin[];
  dense?: boolean;
  onRowClick?: (row: SampleBin) => void;
  fullHeight?: boolean;
  sx?: SxProps<Theme>;
};

// ... (Giữ nguyên các hàm comparator không đổi)
function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  const va = (a as any)[orderBy];
  const vb = (b as any)[orderBy];

  if (va == null && vb == null) return 0;
  if (va == null) return 1;
  if (vb == null) return -1;

  if (typeof va === "number" && typeof vb === "number") {
    return vb - va;
  }
  if (typeof va === "boolean" && typeof vb === "boolean") {
    return Number(vb) - Number(va);
  }
  return String(vb).localeCompare(String(va), undefined, { numeric: true });
}

function getComparator<Key extends keyof any>(
  order: Order,
  orderBy: Key
): (a: { [key in Key]: any }, b: { [key in Key]: any }) => number {
  return order === "desc"
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort<T>(array: T[], comparator: (a: T, b: T) => number) {
  const stabilized = array.map((el, index) => [el, index] as [T, number]);
  stabilized.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) return order;
    return a[1] - b[1];
  });
  return stabilized.map((el) => el[0]);
}

export default function SampleBinTable({
  data,
  dense = false,
  onRowClick,
  fullHeight = false,
  sx,
}: Props) {
  const [order, setOrder] = React.useState<Order>("asc");
  const [orderBy, setOrderBy] = React.useState<
    keyof SampleBin | "gc_content_percent" | "result_name"
  >("chromosome");

  const handleRequestSort = (property: typeof orderBy) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const rows = React.useMemo(() => {
    return data.map((r) => ({
      ...r,
      gc_content_percent: r.gc_content != null ? r.gc_content * 100 : null,
      result_name: r.result?.reference_genome ?? "",
    }));
  }, [data]);

  const sortedRows = stableSort(rows, getComparator(order, orderBy as any));

  const handleExportCSV = () => {
    const headers = ["Chromosome", "Start", "End", "Copy #", "Read Count", "GC %"];
    const csvContent = sortedRows.map((row) => {
      return [
        row.chromosome,
        row.start,
        row.end,
        row.copy_number,
        row.read_count,
        row.gc_content != null ? (row.gc_content * 100).toFixed(2) : "",
      ].join(",");
    });
    const csvString = [headers.join(","), ...csvContent].join("\n");
    const blob = new Blob(["\uFEFF" + csvString], { type: "text/csv;charset=utf-8;" });
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
      className={`space-y-3 ${fullHeight ? "w-full h-full" : "max-h-[120vh]"}`}
      style={
        fullHeight ? { display: "flex", flexDirection: "column" } : undefined
      }
      sx={{ overflow: "hidden", ...sx }}
    >
      {/* --- CẬP NHẬT TOOLBAR VỚI NÚT BÉ HƠN --- */}
      <Box sx={{ p: 1, pr: 2, display: 'flex', justifyContent: 'flex-end', borderBottom: '1px solid #e0e0e0' }}>
        <Button 
          variant="outlined"  // Đổi sang outlined cho nhẹ
          size="small"        // Size nhỏ của MUI
          onClick={handleExportCSV}
          sx={{
            fontSize: '0.75rem', // Giảm cỡ chữ
            padding: '2px 8px',  // Giảm padding
            minWidth: 'auto',    // Bỏ chiều rộng tối thiểu mặc định
            height: '28px',      // Set chiều cao cố định nhỏ
            textTransform: 'none' // Bỏ viết hoa toàn bộ để trông gọn hơn
          }}
        >
          Export CSV
        </Button>
      </Box>

      <TableContainer 
        style={fullHeight ? { height: "100%", overflow: 'auto' } : { maxHeight: '120vh', overflow: 'auto' }}
      >
        <Table size={dense ? "small" : "medium"} stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell
                sortDirection={orderBy === "chromosome" ? order : false}
              >
                <TableSortLabel
                  active={orderBy === "chromosome"}
                  direction={orderBy === "chromosome" ? order : "asc"}
                  onClick={() => handleRequestSort("chromosome")}
                >
                  Chromosome
                </TableSortLabel>
              </TableCell>

              <TableCell align="right" sortDirection={orderBy === "start" ? order : false}>
                <TableSortLabel
                  active={orderBy === "start"}
                  direction={orderBy === "start" ? order : "asc"}
                  onClick={() => handleRequestSort("start")}
                >
                  Start
                </TableSortLabel>
              </TableCell>

              <TableCell align="right" sortDirection={orderBy === "end" ? order : false}>
                <TableSortLabel
                  active={orderBy === "end"}
                  direction={orderBy === "end" ? order : "asc"}
                  onClick={() => handleRequestSort("end")}
                >
                  End
                </TableSortLabel>
              </TableCell>

              <TableCell align="right" sortDirection={orderBy === "copy_number" ? order : false}>
                <TableSortLabel
                  active={orderBy === "copy_number"}
                  direction={orderBy === "copy_number" ? order : "asc"}
                  onClick={() => handleRequestSort("copy_number")}
                >
                  Copy #
                </TableSortLabel>
              </TableCell>

              <TableCell align="right" sortDirection={orderBy === "read_count" ? order : false}>
                <TableSortLabel
                  active={orderBy === "read_count"}
                  direction={orderBy === "read_count" ? order : "asc"}
                  onClick={() => handleRequestSort("read_count")}
                >
                  Read Count
                </TableSortLabel>
              </TableCell>

              <TableCell align="right" sortDirection={orderBy === "gc_content_percent" ? order : false}>
                <TableSortLabel
                  active={orderBy === "gc_content_percent"}
                  direction={orderBy === "gc_content_percent" ? order : "asc"}
                  onClick={() => handleRequestSort("gc_content_percent")}
                >
                  GC %
                </TableSortLabel>
              </TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {sortedRows.length === 0 && (
              <TableRow key="empty">
                <TableCell colSpan={9} align="center">
                  Không có dữ liệu
                </TableCell>
              </TableRow>
            )}

            {sortedRows.map((r, index) => (
              <TableRow
                key={r.id ?? `row-${index}`}
                hover
                onClick={() => onRowClick?.(r)}
                style={{ cursor: onRowClick ? "pointer" : "default" }}
              >
                <TableCell>
                  {typeof r.chromosome === "string"
                    ? r.chromosome
                    : JSON.stringify(r.chromosome)}
                </TableCell>
                <TableCell align="right">{r.start}</TableCell>
                <TableCell align="right">{r.end}</TableCell>
                <TableCell align="right">{r.copy_number}</TableCell>
                <TableCell align="right">{r.read_count}</TableCell>
                <TableCell align="right">
                  {r.gc_content != null
                    ? (r.gc_content * 100).toFixed(2) + "%"
                    : "-"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}