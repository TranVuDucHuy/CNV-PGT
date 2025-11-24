// SamplePane.tsx
"use client";

import React, { ChangeEvent, useEffect, useMemo, useState } from "react";
import { Plus, Minus, Edit3 } from "lucide-react";
import useSampleHandle from "./sampleHandle";
import CenterDialog from "@/components/CenterDialog";
import OperatingDialog from "@/components/OperatingDialog";
import { Checkbox, Box, Button, Stack, Typography, CircularProgress, Collapse, IconButton } from "@mui/material";
import { ReferenceGenome, CellType } from "@/types/sample";
import { syncWithSamples } from "@/features/reference/useReferences";
import { parseSampleNameToParts } from "./sampleUtils";
import MUIAccordionPane from "@/components/MUIAccordionPane";

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
  const {
    files,
    samples = [],
    isOpen,
    open,
    loading,
    error,
    close,
    setFile,
    save,
    saveManyFiles,
    removeSamples,
  } = useSampleHandle();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [removeDialogOpen, setRemoveDialogOpen] = useState<boolean>(false);
  const [operating, setOperating] = useState(false);
  const [promise, setPromise] = useState<Promise<any> | undefined>();
  const [isSelectAll, setIsSelectAll] = useState<boolean>(false);
  const [referenceGenome, setReferenceGenome] = useState<ReferenceGenome>(ReferenceGenome.HG19);
  const [cellType, setCellType] = useState<string>("Other");
  const [uploadDate, setUploadDate] = useState<string>(new Date().toISOString().split("T")[0]);

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
    if (!samples || samples.length === 0) {
      setSelectedIds(new Set());
      setIsSelectAll(false);
      syncWithSamples(new Set());
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
  }, [samples]);

  useEffect(() => {
    const total = samples.length;
    const selectedCount = selectedIds.size;
    setIsSelectAll(total > 0 && selectedCount === total);
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

      const flowcell =
        s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
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

  const toggleSelect = (id: string | undefined) => {
    if (id === undefined || id === null) return;
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (event: ChangeEvent<HTMLInputElement>) => {
    const checked = event.target.checked;
    if (checked) {
      const next = new Set<string>();
      for (const s of samples as SampleItem[]) {
        if (s.id) next.add(s.id);
      }
      setSelectedIds(next);
      setIsSelectAll((samples as SampleItem[]).length > 0 && next.size === (samples as SampleItem[]).length);
    } else {
      setSelectedIds(new Set());
      setIsSelectAll(false);
    }
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
        variant="contained"
        size="small"
        sx={{ minWidth: 0, px: 1, bgcolor: "#10B981", "&:hover": { bgcolor: "#059669" } }}
      >
        <Plus size={14} />
      </Button>

      <Button
        onClick={(e) => {
          e.stopPropagation();
          if (selectedIds.size > 0) {
            setRemoveDialogOpen(true);
          }
        }}
        title="Remove"
        variant="contained"
        size="small"
        sx={{ minWidth: 0, px: 1, bgcolor: "#EF4444", "&:hover": { bgcolor: "#DC2626" } }}
      >
        <Minus size={14} />
      </Button>

      <IconButton
        onClick={(e) => e.stopPropagation()}
        title="Edit"
        size="small"
        sx={{ bgcolor: "#3B82F6", color: "#fff", "&:hover": { bgcolor: "#2563EB" } }}
      >
        <Edit3 size={16} />
      </IconButton>
    </Stack>
  );

  return (
    <MUIAccordionPane title="Sample" defaultExpanded headerRight={headerRight}>
      <Box>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 1 }}>
          <Typography variant="body2">{selectedIds.size} selected</Typography>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Checkbox checked={isSelectAll} onChange={toggleSelectAll} size="small" />
            <Typography variant="body2">Select All</Typography>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Loading samples...
            </Typography>
          </Box>
        ) : samples.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No samples yet. Click + to add one.
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
                      <Box>
                        <Button onClick={() => toggleOpenFlowcell(flowcell)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                          <Typography sx={{ fontWeight: 600 }}>{flowcell}</Typography>
                          <Typography sx={{ ml: 1, fontSize: "0.75rem", color: "text.secondary" }}>({totalCount})</Typography>
                        </Button>
                      </Box>
                    </Box>

                    <Collapse in={isOpenFlow} unmountOnExit>
                      <Box sx={{ pl: 4, pt: 1 }}>
                        <Stack spacing={1}>
                          {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                            const cycleKey = `${flowcell}|${cycle}`;
                            const isOpenCycle = openCycles.has(cycleKey);
                            return (
                              <Box key={cycle} sx={{ borderRadius: 1, p: 1, bgcolor: "#F9FAFB" }}>
                                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                  <Box>
                                    <Button onClick={() => toggleOpenCycle(flowcell, cycle)} sx={{ textTransform: "none", p: 0, minWidth: 0 }}>
                                      <Typography sx={{ fontWeight: 500 }}>{cycle}</Typography>
                                      <Typography sx={{ ml: 1, fontSize: "0.75rem", color: "text.secondary" }}>({arr.length})</Typography>
                                    </Button>
                                  </Box>
                                </Box>

                                <Collapse in={isOpenCycle} unmountOnExit>
                                  <Box sx={{ pl: 4, pt: 1 }}>
                                    <Stack spacing={1}>
                                      {arr.map(({ sample, parsed }: any) => {
                                        const isSelected = sample.id !== undefined && selectedIds.has(sample.id);
                                        return (
                                          <Box
                                            key={sample.id}
                                            role="button"
                                            onClick={() => toggleSelect(sample.id)}
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
                                              {parsed.displayName}
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

      <CenterDialog
        open={isOpen}
        title="Upload Sample"
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
            <input
              type="file"
              accept=".bam"
              onChange={(e) => setFile(Array.from(e.target.files ?? []))}
              style={{ display: "block", width: "100%" }}
              required
              multiple
            />
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Reference Genome
            </Typography>
            <select
              value={referenceGenome}
              onChange={(e) => setReferenceGenome(e.target.value as ReferenceGenome)}
              style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }}
              required
            >
              <option value={ReferenceGenome.HG19}>HG19</option>
              <option value={ReferenceGenome.HG38}>HG38</option>
            </select>
          </Box>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5 }}>
              Cell Type
            </Typography>
            <select
              value={cellType}
              onChange={(e) => setCellType(e.target.value)}
              style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }}
              required
            >
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
            <input
              type="date"
              value={uploadDate}
              onChange={(e) => setUploadDate(e.target.value)}
              style={{ display: "block", width: "100%", padding: 8, borderRadius: 6, border: "1px solid rgba(0,0,0,0.23)" }}
              required
            />
          </Box>
        </Stack>
      </CenterDialog>

      <CenterDialog
        open={removeDialogOpen}
        title={`You sure want to remove these samples (${selectedIds.size})`}
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
              const parsed = parseSampleNameToParts(s.name);
              return (
                <Box key={s.id} sx={{ border: 1, borderColor: "grey.200", p: 1, borderRadius: 1, bgcolor: "#fff" }}>
                  <Typography sx={{ fontWeight: 500 }}>{parsed.displayName}</Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {s.cell_type ?? "-"}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" display="block">
                    {s.date ?? "-"}
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
