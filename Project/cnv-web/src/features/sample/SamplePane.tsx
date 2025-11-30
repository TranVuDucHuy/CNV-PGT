// SamplePane.tsx
"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Plus, Minus, Edit3 } from "lucide-react";
import useSampleHandle from "./sampleHandle";
import CenterDialog from "@/components/CenterDialog";
import OperatingDialog from "@/components/OperatingDialog";
import { Checkbox, Box, Button, Stack, Typography, CircularProgress, Collapse, IconButton } from "@mui/material";
import { ReferenceGenome, CellType } from "@/types/sample";
import { syncWithSamples } from "@/features/reference/useReferences";
import { parseSampleNameToParts } from "./sampleUtils";
import MUIAccordionPane from "@/components/MUIAccordionPane";
import { setSelectedSample } from "@/features/selection/selectionStore";

type SampleItem = {
  id: string;
  name: string;
  cell_type?: string;
  date?: string;
  flowcell_id?: string;
  cycle_id?: string;
  embryo_id?: string;
  [k: string]: any;
};

export default function SamplePane() {
  const { files, samples = [], isOpen, open, loading, error, close, setFile, save, saveManyFiles, removeSamples } = useSampleHandle();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [removeDialogOpen, setRemoveDialogOpen] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();
  const [referenceGenome, setReferenceGenome] = useState<ReferenceGenome>(ReferenceGenome.HG19);
  const [cellType, setCellType] = useState<string>("Other");
  const [uploadDate, setUploadDate] = useState<string>(new Date().toISOString().split("T")[0]);
  const [hasLoadedOnce, setHasLoadedOnce] = useState<boolean>(false);
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);

  // UI expand/collapse state
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, close]);

  // sync selectedIds when samples removed/changed
  useEffect(() => {
    if (!loading && (samples?.length ?? 0) > 0) {
      setHasLoadedOnce(true);
    }
    if (loading) {
      return;
    }
    if (!hasLoadedOnce && (!samples || samples.length === 0)) {
      return;
    }
    if (!samples || samples.length === 0) {
      setSelectedIds(new Set());
      syncWithSamples(new Set());
      setSelectedSample(null); // Clear selection store
      return;
    }
    setSelectedIds((prev) => {
      const next = new Set<string>();
      const sampleIds = new Set(samples.map((s: any) => s.id));
      for (const id of prev) {
        if (id && sampleIds.has(id)) next.add(id);
      }
      return next;
    });

    const availableSampleIds = new Set(samples.map((s: any) => s.id));
    syncWithSamples(availableSampleIds);
  }, [samples, loading, hasLoadedOnce]);

  // Sync selection store khi selectedIds thay đổi
  useEffect(() => {
    if (selectedIds.size === 1) {
      const selectedId = Array.from(selectedIds)[0];
      const sample = samples.find((s: any) => s.id === selectedId);
      if (sample) {
        setSelectedSample(sample);
      } else {
        setSelectedSample(null);
      }
    } else {
      setSelectedSample(null);
    }
  }, [selectedIds, samples]);

  const openOperatingDialog = (prom: Promise<any>) => {
    setOperating(true);
    setPromise(prom);
  };

  // Build grouping map: flowcell -> cycle -> samples[]
  const grouped = useMemo(() => {
    const map = new Map<string, Map<string, Array<{ sample: SampleItem; parsed: any }>>>();

    for (const sRaw of (samples as SampleItem[] | undefined) ?? []) {
      const s = sRaw as SampleItem;

      const fallbackParsed = parseSampleNameToParts(s.name);

      const flowcell = s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo;

      const parsed = {
        flowcell,
        cycle,
        embryo,
        displayName: display,
      };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }

    const sortedMap = new Map<string, Map<string, Array<{ sample: SampleItem; parsed: any }>>>();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<string, Array<{ sample: SampleItem; parsed: any }>>();
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!;
            arr.sort((a: any, b: any) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [samples]);

  // Mảng flat để support Shift+Click range select
  const flattenedSamples = useMemo(() => {
    const result: SampleItem[] = [];
    for (const [, cycleMap] of grouped.entries()) {
      for (const [, arr] of cycleMap.entries()) {
        for (const { sample } of arr) {
          result.push(sample);
        }
      }
    }
    return result;
  }, [grouped]);

  const allSampleIdsUnderFlowcell = (flowcell: string) => {
    const cycleMap = grouped.get(flowcell);
    if (!cycleMap) return [];
    const ids: string[] = [];
    for (const arr of cycleMap.values()) {
      for (const item of arr) ids.push(item.sample.id);
    }
    return ids;
  };

  const allSampleIdsUnderCycle = (flowcell: string, cycle: string) => {
    const cycleMap = grouped.get(flowcell);
    if (!cycleMap) return [];
    const arr = cycleMap.get(cycle) ?? [];
    return arr.map((it: any) => it.sample.id);
  };

  const toggleSelect = (id: string | undefined, event?: React.MouseEvent) => {
    if (id === undefined || id === null) return;

    // Xử lý Shift+Click: toggle range từ lastClickedId đến id hiện tại
    if (event?.shiftKey && lastClickedId !== null) {
      const startIdx = flattenedSamples.findIndex((s) => s.id === lastClickedId);
      const endIdx = flattenedSamples.findIndex((s) => s.id === id);
      if (startIdx !== -1 && endIdx !== -1) {
        const [min, max] = startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
        setSelectedIds((prev) => {
          const next = new Set(prev);
          const allSelected = Array.from({ length: max - min + 1 }, (_, i) => min + i).every((i) => flattenedSamples[i] && next.has(flattenedSamples[i].id));
          for (let i = min; i <= max; i++) {
            if (flattenedSamples[i]?.id) {
              if (allSelected) {
                next.delete(flattenedSamples[i].id);
              } else {
                next.add(flattenedSamples[i].id);
              }
            }
          }
          return next;
        });
      }
      return;
    }

    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
    setLastClickedId(id);
  };

  const toggleFlowcell = (flowcell: string) => {
    const ids = allSampleIdsUnderFlowcell(flowcell);
    if (ids.length === 0) return;
    const allSelected = ids.every((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  const toggleCycle = (flowcell: string, cycle: string) => {
    const ids: string[] = allSampleIdsUnderCycle(flowcell, cycle);
    if (ids.length === 0) return;
    const allSelected = ids.every((id) => selectedIds.has(id));
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
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

  const handleUploadConfirm = () => {
    if (!operating) {
      if (files?.length && files?.length > 0) {
        if (files?.length == 1) {
          openOperatingDialog(save(referenceGenome, cellType, uploadDate));
        } else if (files?.length > 1) {
          openOperatingDialog(saveManyFiles(referenceGenome, cellType, uploadDate));
        }
      }
    }
  };

  const handleRemoveConfirm = () => {
    if (!operating) {
      openOperatingDialog(removeSamples(selectedIds));
      setRemoveDialogOpen(false);
    }
  };

  const headerRight = (
    <Stack direction="row" spacing={1} alignItems="center">
      <Button
        onClick={(e) => {
          e.stopPropagation();
          open();
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
          if (selectedIds.size > 0) {
            setRemoveDialogOpen(true);
          }
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
    <MUIAccordionPane title="Sample" defaultExpanded headerRight={headerRight}>
      <Box>
        {loading ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <CircularProgress size={20} />
            <Typography variant="body1" sx={{ mt: 1 }}>
              Loading samples...
            </Typography>
          </Box>
        ) : samples.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body1">No samples yet. Click Add to add one.</Typography>
          </Box>
        ) : (
          <Box sx={{ maxHeight: "40vh", overflowY: "scroll", pr: 1, scrollbarGutter: "stable" }}>
            <Stack spacing={1}>
              {Array.from(grouped.entries()).map(([flowcell, cycleMap]) => {
                const isOpenFlow = openFlowcells.has(flowcell);
                const totalCount = Array.from(cycleMap.values()).flat().length;
                return (
                  <Box key={flowcell} sx={{ bgcolor: "#fff", p: 1, borderRadius: 1, border: 1, borderColor: "grey.200" }}>
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <Box>
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
                                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                  <Box>
                                    <Button onClick={() => toggleOpenCycle(flowcell, cycle)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                                      <Typography variant="body2">{cycle}</Typography>
                                      {/* <Typography variant="body2" sx={{ ml: 1}}>[{arr.length}]</Typography> */}
                                    </Button>
                                  </Box>
                                </Box>

                                <Collapse in={isOpenCycle} unmountOnExit>
                                  <Box sx={{ pl: 1, pt: 1 }}>
                                    <Stack spacing={1}>
                                      {arr.map(({ sample, parsed }: any) => {
                                        const isSelected = sample.id !== undefined && selectedIds.has(sample.id);
                                        return (
                                          <Box
                                            key={sample.id}
                                            role="button"
                                            onClick={(e) => toggleSelect(sample.id, e)}
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
                                              userSelect: "none",
                                            }}
                                          >
                                            <Typography variant="body1">{parsed.displayName}</Typography>
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

      <CenterDialog
        open={isOpen}
        title={
          <Typography variant="h3" component="h3">
            Upload Sample
          </Typography>
        }
        onClose={() => close()}
        onConfirm={handleUploadConfirm}
        confirmLabel="Upload"
        cancelLabel="Cancel"
      >
        <Stack spacing={2}>
          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Select File
            </Typography>
            <input type="file" accept=".bam" onChange={(e) => setFile(Array.from(e.target.files ?? []))} style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }} required multiple title="" />
            <style>{`
              input[type="file"]::file-selector-button {
                display: none;
              }
            `}</style>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Reference Genome
            </Typography>
            <select value={referenceGenome} onChange={(e) => setReferenceGenome(e.target.value as ReferenceGenome)} style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }} required>
              <option value={ReferenceGenome.HG19}>HG19</option>
              <option value={ReferenceGenome.HG38}>HG38</option>
            </select>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Cell Type
            </Typography>
            <select value={cellType} onChange={(e) => setCellType(e.target.value)} style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }} required>
              <option value={CellType.POLAR_BODY_1}>Polar body 1</option>
              <option value={CellType.POLAR_BODY_2}>Polar body 2</option>
              <option value={CellType.BLASTOMERE}>Blastomere</option>
              <option value={CellType.TROPHOECTODERM}>Trophectoderm</option>
              <option value={CellType.GENOMIC_DNA}>GenomicDNA</option>
              <option value={CellType.OTHER}>Other</option>
            </select>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Date
            </Typography>
            <input type="date" value={uploadDate} onChange={(e) => setUploadDate(e.target.value)} style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }} required />
          </Box>
        </Stack>
      </CenterDialog>

      <CenterDialog
        open={removeDialogOpen}
        title={
          <>
            <Typography variant="h3" component="h3">{`Remove sample`}</Typography>
            <Typography variant="body2" sx={{ pt: 1 }}>{`Are you sure you want to remove ${selectedIds.size} sample(s)?`}</Typography>
          </>
        }
        onClose={() => setRemoveDialogOpen(false)}
        onConfirm={handleRemoveConfirm}
        confirmLabel="Yes"
        cancelLabel="Cancel"
      >
        <Box sx={{ maxHeight: 240, overflowY: "auto" }}>
          <Stack spacing={1}>
            {samples.map((s: SampleItem) => {
              const isSelected = s.id !== undefined && selectedIds.has(s.id);
              if (!isSelected) return null;
              return (
                <Box key={s.id} sx={{ border: 1, borderColor: "grey.200", p: 1, borderRadius: 1, bgcolor: "#fff" }}>
                  <Typography variant="body1">{s.name}</Typography>
                </Box>
              );
            })}
          </Stack>
        </Box>
      </CenterDialog>
    </MUIAccordionPane>
  );
}
