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
} from "@mui/material";

import { SampleBin } from "@/types/result";

type Order = "asc" | "desc";

type Props = {
  data: SampleBin[];
  dense?: boolean;
  onRowClick?: (row: SampleBin) => void;
  fullHeight?: boolean; // new
  sx?: SxProps<Theme>;
};

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  const va = (a as any)[orderBy];
  const vb = (b as any)[orderBy];

  // handle undefined/null
  if (va == null && vb == null) return 0;
  if (va == null) return 1;
  if (vb == null) return -1;

  if (typeof va === "number" && typeof vb === "number") {
    return vb - va;
  }
  // for boolean -> convert to number
  if (typeof va === "boolean" && typeof vb === "boolean") {
    return Number(vb) - Number(va);
  }
  // fallback to string comparison
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

  // prepare rows: augment gc_content_percent and result_name for sorting
  const rows = React.useMemo(() => {
    return data.map((r) => ({
      ...r,
      gc_content_percent: r.gc_content != null ? r.gc_content * 100 : null,
      result_name: r.result?.reference_genome ?? "",
    }));
  }, [data]);

  // pick comparator key: cast to any because we augmented rows
  const sortedRows = stableSort(rows, getComparator(order, orderBy as any));

  return (
    <Paper
      className={`space-y-3 ${fullHeight ? "w-full h-full" : "max-h-[120vh]"}`}
      style={
        fullHeight ? { display: "flex", flexDirection: "column" } : undefined
      }
      sx={{ overflow: "auto", ...sx }}
    >
      <TableContainer style={fullHeight ? { height: "100%" } : undefined}>
        <Table size={dense ? "small" : "medium"} stickyHeader={!!fullHeight}>
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

              <TableCell
                align="right"
                sortDirection={orderBy === "start" ? order : false}
              >
                <TableSortLabel
                  active={orderBy === "start"}
                  direction={orderBy === "start" ? order : "asc"}
                  onClick={() => handleRequestSort("start")}
                >
                  Start
                </TableSortLabel>
              </TableCell>

              <TableCell
                align="right"
                sortDirection={orderBy === "end" ? order : false}
              >
                <TableSortLabel
                  active={orderBy === "end"}
                  direction={orderBy === "end" ? order : "asc"}
                  onClick={() => handleRequestSort("end")}
                >
                  End
                </TableSortLabel>
              </TableCell>

              <TableCell
                align="right"
                sortDirection={orderBy === "copy_number" ? order : false}
              >
                <TableSortLabel
                  active={orderBy === "copy_number"}
                  direction={orderBy === "copy_number" ? order : "asc"}
                  onClick={() => handleRequestSort("copy_number")}
                >
                  Copy #
                </TableSortLabel>
              </TableCell>

              <TableCell
                align="right"
                sortDirection={orderBy === "read_count" ? order : false}
              >
                <TableSortLabel
                  active={orderBy === "read_count"}
                  direction={orderBy === "read_count" ? order : "asc"}
                  onClick={() => handleRequestSort("read_count")}
                >
                  Read Count
                </TableSortLabel>
              </TableCell>

              <TableCell
                align="right"
                sortDirection={orderBy === "gc_content_percent" ? order : false}
              >
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
