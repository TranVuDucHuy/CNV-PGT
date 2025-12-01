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
  SxProps,
  Theme,
  Button, // Import Button
  Box,    // Import Box
} from "@mui/material";

import { SampleSegment } from "@/types/result";

type Order = "asc" | "desc";

type Props = {
  data: SampleSegment[];
  dense?: boolean;
  onRowClick?: (row: SampleSegment) => void;
  fullHeight?: boolean;
  sx?: SxProps<Theme>;
};

type ColId =
  | "chromosome"
  | "start"
  | "end"
  | "copy_number"
  | "confidence"
  | "man_change";

const DEFAULT_COLS: {
  id: ColId;
  label: string;
  align?: "right" | "left" | "center";
  minWidth?: number;
  defaultWidth: number;
}[] = [
  { id: "chromosome", label: "Chromosome", defaultWidth: 140, minWidth: 80 },
  {
    id: "start",
    label: "Start",
    align: "right",
    defaultWidth: 110,
    minWidth: 80,
  },
  { id: "end", label: "End", align: "right", defaultWidth: 110, minWidth: 80 },
  {
    id: "copy_number",
    label: "Copy #",
    align: "right",
    defaultWidth: 100,
    minWidth: 70,
  },
  {
    id: "confidence",
    label: "Confidence",
    align: "right",
    defaultWidth: 140,
    minWidth: 90,
  },
  { id: "man_change", label: "Manual Change", defaultWidth: 140, minWidth: 90 },
];

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

function getComparator<Key extends keyof any>(order: Order, orderBy: Key) {
  return order === "desc"
    ? (a: { [key in Key]: any }, b: { [key in Key]: any }) =>
        descendingComparator(a, b, orderBy)
    : (a: { [key in Key]: any }, b: { [key in Key]: any }) =>
        -descendingComparator(a, b, orderBy);
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
  sx,
}: Props) {
  const [order, setOrder] = React.useState<Order>("asc");
  const [orderBy, setOrderBy] = React.useState<
    keyof SampleSegment | "result_name"
  >("chromosome");

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

  // ---- widths state
  const [widths, setWidths] = React.useState<Record<ColId, number>>(() =>
    DEFAULT_COLS.reduce((acc, c) => {
      acc[c.id] = c.defaultWidth;
      return acc;
    }, {} as Record<ColId, number>)
  );

  // ---- refs & pending
  const resizingRef = React.useRef<ColId | null>(null);
  const resizeStartRef = React.useRef<{
    startX: number;
    startWidth: number;
    minWidth: number;
  } | null>(null);

  // guide
  const [guideLeft, setGuideLeft] = React.useState<number | null>(null);
  const guideRef = React.useRef<number | null>(null);
  const tableContainerRef = React.useRef<HTMLDivElement | null>(null);

  const [hoveredResizer, setHoveredResizer] = React.useState<ColId | null>(
    null
  );

  // immediate width update (no RAF) - simpler and reliable
  const scheduleWidthUpdateImmediate = React.useCallback(
    (col: ColId, width: number) => {
      setWidths((prev) => {
        const next = { ...prev, [col]: width };
        return next;
      });
    },
    []
  );

  // unified move/up handlers
  const internalPointerMove = React.useCallback(
    (clientX: number) => {
      if (!resizingRef.current) return;
      const col = resizingRef.current;
      const rs = resizeStartRef.current;
      if (!rs) return;

      const cb = tableContainerRef.current;
      if (cb) {
        const rect = cb.getBoundingClientRect();
        const left = clientX - rect.left + cb.scrollLeft;
        const clamped = Math.max(0, Math.min(cb.scrollWidth, left));
        guideRef.current = clamped;
        setGuideLeft(guideRef.current);
      }

      const dx = clientX - rs.startX;
      const newW = Math.max(rs.minWidth, Math.round(rs.startWidth + dx));

      scheduleWidthUpdateImmediate(col, newW);
      document.body.style.userSelect = "none";
    },
    [scheduleWidthUpdateImmediate]
  );

  const internalPointerUp = React.useCallback(() => {
    resizingRef.current = null;
    resizeStartRef.current = null;
    guideRef.current = null;
    setGuideLeft(null);
    document.body.style.userSelect = "";
    setHoveredResizer(null);

    try {
      document.removeEventListener("mousemove", docMouseMove);
      document.removeEventListener("mouseup", docMouseUp);
    } catch (err) {
      // ignore
    }
  }, []);

  // fallback doc handlers
  const docMouseMove = React.useCallback(
    (ev: MouseEvent) => {
      internalPointerMove(ev.clientX);
    },
    [internalPointerMove]
  );

  const docMouseUp = React.useCallback(
    (ev: MouseEvent) => {
      internalPointerUp();
    },
    [internalPointerUp]
  );

  React.useEffect(() => {
    const onPointerMove = (ev: PointerEvent) => {
      if (!resizingRef.current) return;
      internalPointerMove(ev.clientX);
    };

    const onPointerUp = (ev: PointerEvent) => {
      if (!resizingRef.current) return;
      internalPointerUp();
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
    };
  }, [internalPointerMove, internalPointerUp]);

  // start resize
  const startResize = React.useCallback(
    (colId: ColId, clientX: number, minWidth = 60) => {
      resizingRef.current = colId;
      resizeStartRef.current = {
        startX: clientX,
        startWidth: widths[colId],
        minWidth,
      };

      const cb = tableContainerRef.current;
      if (cb) {
        const rect = cb.getBoundingClientRect();
        const left = clientX - rect.left + cb.scrollLeft;
        const clamped = Math.max(0, Math.min(cb.scrollWidth, left));
        guideRef.current = clamped;
        setGuideLeft(clamped);
      }

      try {
        document.addEventListener("mousemove", docMouseMove);
        document.addEventListener("mouseup", docMouseUp);
      } catch (err) {
        // ignore
      }

      document.body.style.userSelect = "none";
    },
    [docMouseMove, docMouseUp, widths]
  );

  const onResizerPointerDown =
    (colId: ColId, minWidth = 60) =>
    (e: React.PointerEvent) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      try {
        (e.currentTarget as Element).setPointerCapture(e.pointerId);
      } catch (err) {
        // ignore
      }
      startResize(colId, e.clientX, minWidth);
      e.stopPropagation();
      e.preventDefault();
    };

  const onResizerMouseDown =
    (colId: ColId, minWidth = 60) =>
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.button !== 0) return;
      e.currentTarget.focus?.();
      startResize(colId, e.clientX, minWidth);
      e.stopPropagation();
      e.preventDefault();
    };

  const cellStyle = (colId: ColId): React.CSSProperties => {
    return {
      whiteSpace: "nowrap",
      overflow: "hidden",
      textOverflow: "ellipsis",
      boxSizing: "border-box",
      paddingRight: 8,
      borderRight: "1px solid rgba(0,0,0,0.08)",
    };
  };

  const RESIZER_HIT = 16;

  // --- CSV Export Logic ---
  const handleExportCSV = () => {
    const headers = [
      "Chromosome",
      "Start",
      "End",
      "Copy #",
      "Confidence",
      "Manual Change",
    ];
    const csvContent = sortedRows.map((row) => {
      return [
        row.chromosome,
        row.start,
        row.end,
        row.copy_number,
        row.confidence != null ? Number(row.confidence).toFixed(4) : "",
        row.man_change ? "Yes" : "No",
      ].join(",");
    });
    const csvString = [headers.join(","), ...csvContent].join("\n");
    const blob = new Blob(["\uFEFF" + csvString], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `sample_segment_export_${new Date().toISOString().slice(0, 10)}.csv`
    );
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
      sx={{ overflow: "hidden", ...sx }} // Đổi thành hidden để toolbar cố định
    >
      {/* --- TOOLBAR --- */}
      <Box
        sx={{
          p: 1,
          pr: 2,
          display: "flex",
          justifyContent: "flex-end",
          borderBottom: "1px solid #e0e0e0",
          flexShrink: 0, // Không bị co lại
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

      <TableContainer
        ref={tableContainerRef}
        style={{
          // Điều chỉnh chiều cao cho phần còn lại
          height: fullHeight ? "100%" : undefined,
          maxHeight: fullHeight ? undefined : "120vh",
          overflowX: "auto",
          overflowY: "auto",
          position: "relative",
          flexGrow: 1, // Chiếm phần còn lại của Paper
        }}
      >
        {/* Guide */}
        {guideLeft != null && (
          <div
            style={{
              position: "absolute",
              left: guideLeft - (tableContainerRef.current?.scrollLeft ?? 0),
              top: 0,
              bottom: 0,
              width: 2,
              pointerEvents: "none",
              background: "rgba(33,150,243,0.9)",
              boxShadow: "0 0 6px rgba(33,150,243,0.25)",
              zIndex: 30,
            }}
          />
        )}

        <Table
          size={dense ? "small" : "medium"}
          stickyHeader
          style={{ tableLayout: "fixed", width: "100%" }}
        >
          <colgroup>
            {DEFAULT_COLS.map((c) => (
              <col key={c.id} style={{ width: `${widths[c.id]}px` }} />
            ))}
          </colgroup>

          <TableHead>
            <TableRow>
              {DEFAULT_COLS.map((col) => {
                const isHovered = hoveredResizer === col.id;
                return (
                  <TableCell
                    key={col.id}
                    sortDirection={orderBy === col.id ? order : false}
                    align={col.align ?? "left"}
                    style={{
                      position: "relative",
                      paddingRight: 0,
                      ...cellStyle(col.id as ColId),
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        height: "100%",
                        paddingLeft: 8,
                      }}
                    >
                      <TableSortLabel
                        active={orderBy === col.id}
                        direction={orderBy === col.id ? order : "asc"}
                        onClick={() => handleRequestSort(col.id as any)}
                        style={{ flex: 1 }}
                      >
                        {col.label}
                      </TableSortLabel>

                      {/* Resizer hit area (pointer + mouse fallback) */}
                      <div
                        role="separator"
                        aria-orientation="horizontal"
                        onPointerDown={onResizerPointerDown(
                          col.id as ColId,
                          col.minWidth ?? 60
                        )}
                        onMouseDown={onResizerMouseDown(
                          col.id as ColId,
                          col.minWidth ?? 60
                        )}
                        onMouseEnter={() => setHoveredResizer(col.id)}
                        onMouseLeave={() =>
                          setHoveredResizer((cur) =>
                            cur === col.id ? null : cur
                          )
                        }
                        style={{
                          position: "absolute",
                          right: 0,
                          top: 0,
                          height: "100%",
                          width: RESIZER_HIT,
                          transform: `translateX(${-(RESIZER_HIT / 2)}px)`,
                          cursor: "ew-resize",
                          touchAction: "none",
                          background: isHovered
                            ? "rgba(33,150,243,0.06)"
                            : "transparent",
                          display: "inline-block",
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />

                      {/* Visible divider */}
                      <div
                        style={{
                          position: "absolute",
                          right: Math.max(0, RESIZER_HIT / 2 - 1),
                          top: 8,
                          bottom: 8,
                          width: 1,
                          background: isHovered
                            ? "rgba(33,150,243,0.9)"
                            : "rgba(0,0,0,0.12)",
                          pointerEvents: "none",
                        }}
                      />
                    </div>
                  </TableCell>
                );
              })}
            </TableRow>
          </TableHead>

          <TableBody>
            {sortedRows.length === 0 && (
              <TableRow key="empty">
                <TableCell colSpan={DEFAULT_COLS.length} align="center">
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
                <TableCell style={cellStyle("chromosome")}>
                  {typeof r.chromosome === "string"
                    ? r.chromosome
                    : JSON.stringify(r.chromosome)}
                </TableCell>
                <TableCell align="right" style={cellStyle("start")}>
                  {r.start}
                </TableCell>
                <TableCell align="right" style={cellStyle("end")}>
                  {r.end}
                </TableCell>
                <TableCell align="right" style={cellStyle("copy_number")}>
                  {r.copy_number}
                </TableCell>
                <TableCell align="right" style={cellStyle("confidence")}>
                  {r.confidence != null
                    ? Number(r.confidence).toFixed(4)
                    : "-"}
                </TableCell>
                <TableCell style={cellStyle("man_change")}>
                  {r.man_change ? "Yes" : "No"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}