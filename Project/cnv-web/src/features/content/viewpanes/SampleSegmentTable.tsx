// SampleSegmentTable.tsx
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
} from "@mui/material";

import { SampleSegment } from "@/types/result";

type Order = "asc" | "desc";

type Props = {
  data: SampleSegment[];
  dense?: boolean;
  onRowClick?: (row: SampleSegment) => void;
  fullHeight?: boolean;
};

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

export default function SampleSegmentTable({
  data,
  dense = false,
  onRowClick,
  fullHeight = false,
}: Props) {
  const [order, setOrder] = React.useState<Order>("asc");
  const [orderBy, setOrderBy] = React.useState<keyof SampleSegment | "result_name">("id");

  const handleRequestSort = (property: typeof orderBy) => {
    const isAsc = orderBy === property && order === "asc";
    setOrder(isAsc ? "desc" : "asc");
    setOrderBy(property);
  };

  const rows = React.useMemo(() => {
    return data.map((r) => ({
      ...r,
      result_name: r.result?.reference_genome ?? "",
    }));
  }, [data]);

  const sortedRows = stableSort(rows, getComparator(order, orderBy as any));

  return (
    <Paper
      className={`space-y-3 overflow-y-auto ${fullHeight ? "w-full h-full" : "max-h-[120vh]"}`}
      style={fullHeight ? { display: "flex", flexDirection: "column" } : undefined}
    >
      <TableContainer style={fullHeight ? { height: "100%" } : undefined}>
        <Table size={dense ? "small" : "medium"} stickyHeader={!!fullHeight}>
          <TableHead>
            <TableRow>
              <TableCell sortDirection={orderBy === "id" ? order : false}>
                <TableSortLabel
                  active={orderBy === "id"}
                  direction={orderBy === "id" ? order : "asc"}
                  onClick={() => handleRequestSort("id")}
                >
                  ID
                </TableSortLabel>
              </TableCell>

              <TableCell sortDirection={orderBy === "result_id" ? order : false}>
                <TableSortLabel
                  active={orderBy === "result_id"}
                  direction={orderBy === "result_id" ? order : "asc"}
                  onClick={() => handleRequestSort("result_id")}
                >
                  Result ID
                </TableSortLabel>
              </TableCell>

              <TableCell sortDirection={orderBy === "chromosome" ? order : false}>
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

              <TableCell align="right" sortDirection={orderBy === "confidence" ? order : false}>
                <TableSortLabel
                  active={orderBy === "confidence"}
                  direction={orderBy === "confidence" ? order : "asc"}
                  onClick={() => handleRequestSort("confidence")}
                >
                  Confidence
                </TableSortLabel>
              </TableCell>

              <TableCell sortDirection={orderBy === "man_change" ? order : false}>
                <TableSortLabel
                  active={orderBy === "man_change"}
                  direction={orderBy === "man_change" ? order : "asc"}
                  onClick={() => handleRequestSort("man_change")}
                >
                  Manual Change
                </TableSortLabel>
              </TableCell>

              <TableCell sortDirection={orderBy === "result_name" ? order : false}>
                <TableSortLabel
                  active={orderBy === "result_name"}
                  direction={orderBy === "result_name" ? order : "asc"}
                  onClick={() => handleRequestSort("result_name")}
                >
                  Result Name
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
                <TableCell>{r.id}</TableCell>
                <TableCell>{r.result_id}</TableCell>
                <TableCell>
                  {typeof r.chromosome === "string" ? r.chromosome : JSON.stringify(r.chromosome)}
                </TableCell>
                <TableCell align="right">{r.start}</TableCell>
                <TableCell align="right">{r.end}</TableCell>
                <TableCell align="right">{r.copy_number}</TableCell>
                <TableCell align="right">
                  {r.confidence != null ? Number(r.confidence).toFixed(4) : "-"}
                </TableCell>
                <TableCell>{r.man_change ? "Yes" : "No"}</TableCell>
                <TableCell>{r.result?.reference_genome}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
