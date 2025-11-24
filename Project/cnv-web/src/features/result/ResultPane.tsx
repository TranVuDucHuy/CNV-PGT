// ResultPane.tsx
"use client";

import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
import { Plus, Minus, Edit3 } from "lucide-react";
import useResultHandle from "./resultHandle";
import { useAlgorithms } from "../algorithm/useAlgorithms";
import CenterDialog from "@/components/CenterDialog";
import OperatingDialog from "@/components/OperatingDialog";
import { Box, Button, Checkbox, Collapse, IconButton, Stack, Typography, CircularProgress, FormControlLabel } from "@mui/material";
import { parseSampleNameToParts } from "@/features/sample/sampleUtils";
import MUIAccordionPane from "@/components/MUIAccordionPane";

export default function ResultPane() {
  const {
    results,
    binFile,
    segmentFile,
    createdAt,
    loading,
    error,
    algo,
    setBinFile,
    setSegmentFile,
    setCreatedAt,
    save,
    refresh,
    removeResults,
    setAlgo,
    setSelectedResultId,
  } = useResultHandle();

  const { algorithms, loadAlgorithms } = useAlgorithms();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [uploadDialogOpen, setUploadDialogOpen] = useState<boolean>(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();

  // UI expand/collapse state
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (selectedIds.size === 1) {
      const first = Array.from(selectedIds.values())[0];
      setSelectedResultId?.(first ?? null);
    } else {
      setSelectedResultId?.(null);
    }
  }, [selectedIds, setSelectedResultId]);

  // Build grouping map: flowcell -> cycle -> array of results (flattened)
  const grouped = useMemo(() => {
    const map = new Map<string, Map<string, Array<{ result: any; parsed: ReturnType<typeof parseSampleNameToParts> }>>>();

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
    const sortedMap = new Map<string, Map<string, Array<{ result: any; parsed: ReturnType<typeof parseSampleNameToParts> }>>>();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<string, Array<{ result: any; parsed: ReturnType<typeof parseSampleNameToParts> }>>();
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

  const toggleSelect = (id?: string) => {
    if (!id) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (e: ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    if (checked) {
      const next = new Set<string>();
      for (const r of results) if (r.id) next.add(r.id);
      setSelectedIds(next);
    } else {
      setSelectedIds(new Set());
    }
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
      openOperatingDialog(removeResults(selectedIds));
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
        }}
        title="Add"
        variant="contained"
        size="small"
        sx={{ minWidth: 0, px: 1, bgcolor: "#10B981", "&:hover": { bgcolor: "#059669" } }}
      >
        <Plus size={14} />
      </Button>

      <Button
        onClick={(e) => {
          e.stopPropagation();
          if (selectedIds.size > 0) setRemoveDialogOpen(true);
        }}
        title="Remove"
        variant="contained"
        size="small"
        sx={{ minWidth: 0, px: 1, bgcolor: "#EF4444", "&:hover": { bgcolor: "#DC2626" } }}
      >
        <Minus size={14} />
      </Button>

      <IconButton onClick={(e) => e.stopPropagation()} title="Edit" size="small" sx={{ bgcolor: "#3B82F6", color: "#fff", "&:hover": { bgcolor: "#2563EB" } }}>
        <Edit3 size={16} />
      </IconButton>
    </Stack>
  );

  return (
    <MUIAccordionPane title="Result" defaultExpanded headerRight={headerRight}>
      <Box>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 1 }}>
          <Typography variant="body2">{selectedIds.size} selected</Typography>

          <FormControlLabel
            control={
              <Checkbox
                checked={results.length > 0 && selectedIds.size === results.length}
                indeterminate={selectedIds.size > 0 && selectedIds.size < results.length}
                onChange={toggleSelectAll}
                size="small"
              />
            }
            label={<Typography variant="body2">Select All</Typography>}
          />
        </Box>

        {loading ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Loading results...
            </Typography>
          </Box>
        ) : results.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No results yet. Click Add to add one.
            </Typography>
          </Box>
        ) : (
          <Box sx={{ maxHeight: "40vh", overflowY: "auto", pr: 1 }}>
            <Stack spacing={1}>
              {Array.from(grouped.entries()).map(([flowcell, cycleMap]) => {
                const isOpenFlow = openFlowcells.has(flowcell);
                const totalCount = Array.from(cycleMap.values()).flat().length;

                return (
                  <Box key={flowcell} sx={{ borderRadius: 1, border: 1, borderColor: "grey.200", bgcolor: "#fff", p: 1 }}>
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <Button onClick={() => toggleOpenFlowcell(flowcell)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                          <Typography sx={{ fontWeight: 600, textAlign: "left" }}>{flowcell}</Typography>
                          <Typography sx={{ ml: 1, fontSize: "0.75rem", color: "text.secondary" }}>({totalCount})</Typography>
                        </Button>
                      </Box>

                      {/* no checkbox here */}
                    </Box>

                    <Collapse in={isOpenFlow} unmountOnExit>
                      <Box sx={{ pl: 4, pt: 1, pb: 0 }}>
                        <Stack spacing={1}>
                          {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                            const cycleKey = `${flowcell}|${cycle}`;
                            const isOpenCycle = openCycles.has(cycleKey);

                            return (
                              <Box key={cycle} sx={{ borderRadius: 1, p: 1, bgcolor: "#F9FAFB" }}>
                                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                    <Button onClick={() => toggleOpenCycle(flowcell, cycle)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                                      <Typography sx={{ fontWeight: 500, textAlign: "left" }}>{cycle}</Typography>
                                      <Typography sx={{ ml: 1, fontSize: "0.75rem", color: "text.secondary" }}>({arr.length})</Typography>
                                    </Button>
                                  </Box>

                                  {/* no checkbox here */}
                                </Box>

                                <Collapse in={isOpenCycle} unmountOnExit>
                                  <Box sx={{ pl: 4, pt: 1 }}>
                                    <Stack spacing={1}>
                                      {arr.map(({ result, parsed }) => {
                                        const isSelected = result.id !== undefined && selectedIds.has(result.id);
                                        return (
                                          <Box
                                            key={result.id}
                                            role="button"
                                            onClick={() => toggleSelect(result.id)}
                                            aria-pressed={isSelected}
                                            sx={{
                                              p: 1,
                                              borderRadius: 1,
                                              cursor: "pointer",
                                              border: isSelected ? "1px solid" : "1px solid transparent",
                                              borderColor: isSelected ? "primary.main" : "transparent",
                                              bgcolor: isSelected ? "#DBEAFE" : "#fff",
                                              transition: "background-color 0.12s",
                                              display: "flex",
                                              alignItems: "center",
                                              justifyContent: "space-between",
                                            }}
                                          >
                                            <Typography variant="caption" color="text.secondary">
                                              {parsed.embryo ?? result.id}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                              {result.algorithm_name ?? "-"}
                                            </Typography>
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
        title="Upload Result"
        onClose={() => setUploadDialogOpen(false)}
        onConfirm={handleUploadConfirm}
        confirmLabel="Upload"
        cancelLabel="Cancel"
      >
        {/* ...upload dialog content unchanged from previous version... */}
        <Stack spacing={2}>
          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Bin File
            </Typography>
            <input type="file" accept=".tsv" onChange={(e) => setBinFile(e.target.files?.[0] ?? null)} style={{ display: "block", width: "100%" }} required />
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Segment File
            </Typography>
            <input type="file" accept=".tsv" onChange={(e) => setSegmentFile(e.target.files?.[0] ?? null)} style={{ display: "block", width: "100%" }} required />
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select Algorithm
            </Typography>

            <Box sx={{ mb: 1 }}>{algo ? <Typography variant="body2">Selected Algorithm {algo.name}</Typography> : <></>}</Box>

            {algorithms.length === 0 ? (
              <Box sx={{ textAlign: "center", py: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  No algorithms yet. Click Add to add one.
                </Typography>
              </Box>
            ) : (
              <Box sx={{ maxHeight: 160, overflowY: "auto" }}>
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
                            <Typography variant="body2" sx={{ fontWeight: 500 }}>
                              {al.name} <Typography component="span" variant="caption" color="text.secondary">v{al.version}</Typography>
                            </Typography>
                          </Box>
                          {isSelected && <Typography variant="caption" color="primary">(selected)</Typography>}
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
            <input type="date" value={createdAt || ""} onChange={(e) => setCreatedAt(e.target.value || null)} style={{ display: "block", width: "100%", padding: 8, borderRadius: 4, border: "1px solid rgba(0,0,0,0.23)" }} />
          </Box>
        </Stack>
      </CenterDialog>

      {/* Remove confirm dialog */}
      <CenterDialog
        open={removeDialogOpen}
        title={`You sure want to remove these results (${selectedIds.size})`}
        onClose={() => setRemoveDialogOpen(false)}
        onConfirm={handleRemoveConfirm}
        confirmLabel="Yes"
        cancelLabel="Cancel"
      >
        <Box sx={{ maxHeight: 240, overflowY: "auto" }}>
          <Stack spacing={1}>
            {results.map((r: any) => {
              const isSelected = r.id !== undefined && selectedIds.has(r.id);
              if (!isSelected) return null;
              return (
                <Box key={r.id} sx={{ border: 1, borderColor: "grey.200", p: 1, borderRadius: 1, bgcolor: "#fff" }}>
                  <Typography sx={{ fontWeight: 500 }}>{r.id}</Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {r.reference_genome}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
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
