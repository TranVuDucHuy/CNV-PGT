// ResultPane.tsx
"use client";

import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
import { useSelector, useDispatch } from "react-redux"; // Redux hooks
import { Plus, Minus, Edit3 } from "lucide-react";
import useResultHandle from "./resultHandle";
import { useAlgorithms } from "../algorithm/useAlgorithms";
import CenterDialog from "@/components/CenterDialog";
import OperatingDialog from "@/components/OperatingDialog";
import { Box, Button, Checkbox, Collapse, IconButton, Stack, Typography, CircularProgress, FormControlLabel } from "@mui/material";
import { parseSampleNameToParts } from "@/features/sample/sampleUtils";
import MUIAccordionPane from "@/components/MUIAccordionPane";
import { useRouter } from "next/navigation";

// --- Imports mới cho Type và Redux ---
import { ResultSummary } from "@/types/result"; // Import type chính xác để sửa lỗi 'any'
import { RootState } from "@/utils/store"; // Đường dẫn tới store của bạn
import { toggleResultSelection, setSelectedResults, clearSelection } from "@/utils/appSlice"; // Đường dẫn tới slice của bạn

export default function ResultPane() {
  const dispatch = useDispatch();

  // 1. Lấy danh sách ID đang chọn từ Redux
  const selectedResultIds = useSelector((state: RootState) => state.app.selectedResults);

  const {
    results,
    binFile,
    segmentFile,
    createdAt,
    loading,
    // error,
    algo,
    setBinFile,
    setSegmentFile,
    setCreatedAt,
    save,
    // refresh,
    removeResults,
    setAlgo,
    setSelectedResultId,
  } = useResultHandle();

  const { algorithms, loadAlgorithms } = useAlgorithms();

  // 2. Chuyển mảng ID từ Redux sang Set để tối ưu hiệu năng tìm kiếm (O(1)) khi render
  const selectedIdsSet = useMemo(() => new Set(selectedResultIds), [selectedResultIds]);

  const [uploadDialogOpen, setUploadDialogOpen] = useState<boolean>(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();

  // UI expand/collapse state
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);

  const router = useRouter();

  // Logic: Nếu chọn đúng 1 item thì set SelectedResultId để hiển thị chi tiết bên phải (nếu có)
  useEffect(() => {
    if (selectedResultIds.length === 1) {
      setSelectedResultId?.(selectedResultIds[0]);
    } else {
      setSelectedResultId?.(null);
    }
  }, [selectedResultIds, setSelectedResultId]);

  const handleOpenResultsPage = () => {
    window.open("/result", "_blank", "noopener,noreferrer");
  };

  // 3. FIX LỖI: Định nghĩa kiểu dữ liệu cụ thể cho Map thay vì dùng 'any'
  const grouped = useMemo(() => {
    const map = new Map<
      string,
      Map<
        string,
        Array<{
          result: ResultSummary; // <--- SỬA TẠI ĐÂY: Dùng type chuẩn thay vì any
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();

    for (const r of results) {
      const parsed = parseSampleNameToParts(r.sample_name);
      const flowcell = parsed.flowcell ?? "UNKNOWN";
      const cycle = parsed.cycle ?? "UNKNOWN";

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ result: r, parsed });
    }

    // sort for stable UI
    // Cũng cần định nghĩa lại type cho sortedMap giống map ở trên
    const sortedMap = new Map<
      string,
      Map<
        string,
        Array<{
          result: ResultSummary; // <--- SỬA TẠI ĐÂY
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();

    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map(); // TS tự suy luận được từ sortedMap
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!.slice();
            arr.sort((a, b) => (a.parsed.embryo > b.parsed.embryo ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [results]);

  // Mảng flat để support Shift+Click range select
  const flattenedResults = useMemo(() => {
    const result: ResultSummary[] = [];
    for (const [, cycleMap] of grouped.entries()) {
      for (const [, arr] of cycleMap.entries()) {
        for (const { result: r } of arr) {
          result.push(r);
        }
      }
    }
    return result;
  }, [grouped]);

  // 4. Các hàm xử lý chọn bằng Redux Actions
  const toggleSelect = (id?: string, event?: React.MouseEvent) => {
    if (!id) return;

    // Xử lý Shift+Click: toggle range từ lastClickedId đến id hiện tại
    if (event?.shiftKey && lastClickedId !== null) {
      const startIdx = flattenedResults.findIndex((r) => r.id === lastClickedId);
      const endIdx = flattenedResults.findIndex((r) => r.id === id);
      if (startIdx !== -1 && endIdx !== -1) {
        const [min, max] = startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
        const idsToToggle: string[] = [];
        for (let i = min; i <= max; i++) {
          if (flattenedResults[i]?.id) idsToToggle.push(flattenedResults[i].id);
        }
        // Kiểm tra nếu tất cả đã được chọn thì deselect, ngược lại select
        const allSelected = idsToToggle.every((rid) => selectedIdsSet.has(rid));
        if (allSelected) {
          const newIds = selectedResultIds.filter((rid) => !idsToToggle.includes(rid));
          dispatch(setSelectedResults(newIds));
        } else {
          const newIds = Array.from(new Set([...selectedResultIds, ...idsToToggle]));
          dispatch(setSelectedResults(newIds));
        }
      }
      return;
    }

    dispatch(toggleResultSelection(id));
    setLastClickedId(id);
  };

  const toggleOpenFlowcell = (flowcell: string) => {
    setOpenFlowcells((prev) => {
      const next = new Set(prev);
      if (next.has(flowcell)) next.delete(flowcell);
      else next.add(flowcell);
      return next;
    });
  };

  const toggleOpenCycle = (flowcell: string, cycle: string) => {
    const key = `${flowcell}|${cycle}`;
    setOpenCycles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const openOperatingDialog = (prom: Promise<any>) => {
    setOperating(true);
    setPromise(prom);
  };

  const handleUploadConfirm = () => {
    if (!operating && binFile && segmentFile) {
      openOperatingDialog(save());
      setUploadDialogOpen(false);
    }
  };

  const handleRemoveConfirm = () => {
    if (!operating) {
      // Truyền mảng string[] (selectedResultIds) thay vì Set
      openOperatingDialog(removeResults(selectedResultIds));
      setRemoveDialogOpen(false);
    }
  };

  const headerRight = (
    <Stack direction="row" spacing={1} alignItems="center">
      <Button
        onClick={(e) => {
          e.stopPropagation();
          setUploadDialogOpen(true);
          loadAlgorithms();
          // If no date is set yet, default to today (YYYY-MM-DD)
          if (!createdAt) {
            setCreatedAt(new Date().toISOString().split("T")[0]);
          }
        }}
        title="Add"
        size="small"
        sx={{
          minWidth: 0,
          p: 0.5,
          border: 2,
          borderColor: "#10B981",
          bgcolor: "transparent",
          color: "#10B981",
          "& svg": { color: "#10B981" },
          "&:hover": { bgcolor: "#10B981", "& svg": { color: "#fff" } },
        }}
      >
        <Plus size={16} />
      </Button>

      <Button
        onClick={(e) => {
          e.stopPropagation();
          if (selectedResultIds.length > 0) setRemoveDialogOpen(true);
        }}
        title="Remove"
        size="small"
        sx={{
          minWidth: 0,
          p: 0.5,
          border: 2,
          borderColor: "#DC2626",
          bgcolor: "transparent",
          color: "#DC2626",
          "& svg": { color: "#DC2626" },
          "&:hover": { bgcolor: "#DC2626", "& svg": { color: "#fff" },},
        }}
      >
        <Minus size={16} />
      </Button>

      <Button
        onClick={(e) => e.stopPropagation()}
        title="Edit" 
        size="small" 
        sx={{ 
                    minWidth: 0,
          p: 0.5,
          border: 2,
          borderColor: "#3B82F6",
          bgcolor: "transparent",
          color: "#3B82F6",
          "& svg": { color: "#3B82F6" },
          "&:hover": { bgcolor: "#3B82F6", "& svg": { color: "#fff" },},
        }}
      >
        <Edit3 size={16} />
      </Button>
    </Stack>
  );

  return (
    <MUIAccordionPane title="Result" defaultExpanded headerRight={headerRight}>
      <Box>
        {loading ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <CircularProgress size={20} />
            <Typography variant="body1" sx={{ mt: 1 }}>
              Loading results...
            </Typography>
          </Box>
        ) : results.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body1">
              No results yet. Click Add to add one.
            </Typography>
          </Box>
        ) : (
          <Box sx={{ maxHeight: "40vh", overflowY: "scroll", pr: 1, scrollbarGutter: "stable" }}>
            <Stack spacing={1}>
              {Array.from(grouped.entries()).map(([flowcell, cycleMap]) => {
                const isOpenFlow = openFlowcells.has(flowcell);
                const totalCount = Array.from(cycleMap.values()).flat().length;

                return (
                  <Box key={flowcell} sx={{ bgcolor: "#fff", p: 1, borderRadius: 1, border: 1, borderColor: "grey.200" }}>
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                      }}
                    >
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Button onClick={() => toggleOpenFlowcell(flowcell)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                          <Typography variant="body2">{flowcell}</Typography>
                          <Typography variant="body1" sx={{ ml: 1 }}>
                            [{totalCount}]
                          </Typography>
                        </Button>
                      </Box>
                    </Box>

                    <Collapse in={isOpenFlow} unmountOnExit>
                      <Box sx={{ pl: 1, pt: 1 }}>
                        <Stack spacing={1}>
                          {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                            const cycleKey = `${flowcell}|${cycle}`;
                            const isOpenCycle = openCycles.has(cycleKey);

                            return (
                              <Box key={cycle} sx={{ borderRadius: 1, p: 1, pr: 0 }}>
                                <Box
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                  }}
                                >
                                  <Box
                                    sx={{
                                      display: "flex",
                                      alignItems: "center",
                                      gap: 1,
                                    }}
                                  >
                                    <Button onClick={() => toggleOpenCycle(flowcell, cycle)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                                      <Typography variant="body2">{cycle}</Typography>
                                      {/* <Typography variant="body2" sx={{ ml: 1}}>[{arr.length}]</Typography> */}
                                    </Button>
                                  </Box>
                                </Box>

                                <Collapse in={isOpenCycle} unmountOnExit>
                                  <Box sx={{ pl: 1, pt: 1 }}>
                                    <Stack spacing={1}>
                                      {arr.map(({ result, parsed }) => {
                                        const isSelected = result.id !== undefined && selectedIdsSet.has(result.id);
                                        return (
                                          <Box
                                            key={result.id}
                                            role="button"
                                            onClick={(e) => toggleSelect(result.id, e)}
                                            aria-pressed={isSelected}
                                            sx={{
                                              p: 1,
                                              pr: 3,
                                              borderRadius: 1,
                                              cursor: "pointer",
                                              border: isSelected ? "1px solid" : "1px solid transparent",
                                              borderColor: isSelected ? "primary.main" : "transparent",
                                              bgcolor: isSelected ? "#DBEAFE" : "#fff",
                                              transition: "background-color 0.12s",
                                              display: "flex",
                                              alignItems: "center",
                                              justifyContent: "space-between",
                                              userSelect: "none",
                                            }}
                                          >
                                            <Typography variant="body1">{parsed.embryo ?? result.id}</Typography>
                                            <Typography variant="caption">{result.algorithm_name ?? "-"}</Typography>
                                          </Box>
                                        );
                                      })}
                                    </Stack>
                                  </Box>
                                </Collapse>
                              </Box>
                            );
                          })}
                        </Stack>
                      </Box>
                    </Collapse>
                  </Box>
                );
              })}
            </Stack>
          </Box>
        )}
      </Box>

      {operating && promise ? <OperatingDialog promise={promise} onDelayDone={() => setOperating(false)} autoCloseDelay={1000} /> : null}

      {/* Upload dialog */}
      <CenterDialog
        open={uploadDialogOpen}
        title={
          <Typography variant="h3" component="h3">
            Upload Result
          </Typography>
        }
        onClose={() => setUploadDialogOpen(false)}
        onConfirm={handleUploadConfirm}
        confirmLabel="Upload"
        cancelLabel="Cancel"
      >
        <Stack spacing={2}>
          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Bin File
            </Typography>
            <input
              type="file"
              accept=".tsv"
              onChange={(e) => setBinFile(e.target.files?.[0] ?? null)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                borderRadius: 6,
                border: "1px solid rgba(0,0,0,0.23)",
              }}
              required
              title=""
            />
            <style>{`
              input[type="file"]::file-selector-button {
                display: none;
              }
            `}</style>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Segment File
            </Typography>
            <input
              type="file"
              accept=".tsv"
              onChange={(e) => setSegmentFile(e.target.files?.[0] ?? null)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                borderRadius: 6,
                border: "1px solid rgba(0,0,0,0.23)",
              }}
              required
              title=""
            />
            <style>{`
              input[type="file"]::file-selector-button {
                display: none;
              }
            `}</style>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Algorithm
            </Typography>

            {/* <Box sx={{ mb: 1 }}>{algo ? <Typography variant="body2">Selected Algorithm {algo.name}</Typography> : <></>}</Box> */}

            {algorithms.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 2 }}>
                <Typography variant="body1">
                  No algorithms yet. You need to add an algorithm first.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ maxHeight: 160, overflowY: "scroll" }}>
                <Stack spacing={1}>
                  {algorithms.map((al) => {
                    const isSelected = al.id !== undefined && al === algo;
                    return (
                      <Box
                        key={al.id}
                        onClick={() => setAlgo(al)}
                        sx={{
                          border: 1,
                          borderColor: isSelected ? "primary.main" : "grey.200",
                          p: 1,
                          borderRadius: 1,
                          bgcolor: isSelected ? "#DBEAFE" : "#fff",
                          cursor: "pointer",
                        }}
                      >
                        <Stack direction="row" alignItems="center" justifyContent="space-between">
                          <Box>
                            <Typography variant="body1">
                              {al.name}{" "}
                              <Typography component="span" variant="caption" color="text.secondary">
                                v{al.version}
                              </Typography>
                            </Typography>
                          </Box>
                          {isSelected && (
                            <Typography variant="caption" color="primary">
                              (selected)
                            </Typography>
                          )}
                        </Stack>
                      </Box>
                    );
                  })}
                </Stack>
              </Box>
            )}
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Date
            </Typography>
            <input
              type="date"
              value={createdAt || ""}
              onChange={(e) => setCreatedAt(e.target.value || null)}
              style={{
                display: "block",
                width: "100%",
                padding: 8,
                borderRadius: 6,
                border: "1px solid rgba(0,0,0,0.23)",
              }}
            />
          </Box>
        </Stack>
      </CenterDialog>

      {/* Remove confirm dialog */}
      <CenterDialog
        open={removeDialogOpen}
        title={
          <>
            <Typography variant="h3" component="h3">{`Remove results`}</Typography>
            <Typography variant="body2" sx={{ pt: 1 }}>{`Are you sure you want to remove ${selectedResultIds.length} result(s)?`}</Typography>
          </>
        }
        onClose={() => setRemoveDialogOpen(false)}
        onConfirm={handleRemoveConfirm}
        confirmLabel="Yes"
        cancelLabel="Cancel"
      >
        <Box sx={{ maxHeight: 240, overflowY: "auto" }}>
          <Stack spacing={1}>
            {results.map((r: any) => {
              const isSelected = r.id !== undefined && selectedIdsSet.has(r.id);
              if (!isSelected) return null;
              return (
                <Box
                  key={r.id}
                  sx={{
                    border: 1,
                    borderColor: "grey.200",
                    p: 1,
                    borderRadius: 1,
                    bgcolor: "#fff",
                  }}
                >
                  <Typography variant="body1">{r.sample_name}</Typography>
                  <Typography variant="caption" display="block" sx={{ pt: 0.5 }}>
                    {r.algorithm_name}
                  </Typography>
                </Box>
              );
            })}
          </Stack>
        </Box>
      </CenterDialog>
    </MUIAccordionPane>
  );
}
