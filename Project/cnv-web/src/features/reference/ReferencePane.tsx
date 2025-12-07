/**
 * ReferencePane Component
 * Hiển thị các samples được chọn làm reference
 */

"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Plus, Minus, ChevronRight } from "lucide-react";
import { useReferencesStore, addReferences, removeReferences } from "./useReferences";
import { parseSampleNameToParts } from "@/features/sample/sampleUtils";
import { SampleSummary } from "@/types/sample";
import { Box, Button, Checkbox, Collapse, IconButton, Stack, Typography } from "@mui/material";
import MUIAccordionPane from "@/components/MUIAccordionPane";
import CenterDialog from "@/components/CenterDialog";

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

interface ReferencePaneProps {
  samples: SampleSummary[];
  onRefresh?: () => Promise<void>;
}

export default function ReferencePane({ samples, onRefresh }: ReferencePaneProps) {
  const { referenceIds } = useReferencesStore();
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [selectedForAdd, setSelectedForAdd] = useState<Set<string>>(new Set());
  const [selectedForRemove, setSelectedForRemove] = useState<Set<string>>(new Set());
  const [openFlowcells, setOpenFlowcells] = useState<Set<string>>(new Set());
  const [openCycles, setOpenCycles] = useState<Set<string>>(new Set());
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);

  // Lấy danh sách references từ samples
  const referenceSamples = useMemo(() => {
    return samples.filter((s) => referenceIds.has(s.id));
  }, [samples, referenceIds]);

  // Group references theo Flowcell > Cycle
  const groupedReferences = useMemo(() => {
    const map = new Map<
      string,
      Map<
        string,
        Array<{
          sample: SampleItem;
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();

    for (const sRaw of referenceSamples as SampleItem[]) {
      const s = sRaw as SampleItem;
      const fallbackParsed = parseSampleNameToParts(s.name);
      const flowcell = s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo;

      const parsed = { flowcell, cycle, embryo, displayName: display };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }
    // Sort
    const sortedMap = new Map<
      string,
      Map<
        string,
        Array<{
          sample: SampleItem;
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<
          string,
          Array<{
            sample: SampleItem;
            parsed: ReturnType<typeof parseSampleNameToParts>;
          }>
        >();
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!;
            arr.sort((a, b) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [referenceSamples]);

  // Lấy samples chưa là reference để hiển thị trong modal
  const availableSamples = useMemo(() => {
    return samples.filter((s) => !referenceIds.has(s.id));
  }, [samples, referenceIds]);

  // Group available samples cho modal
  const groupedAvailable = useMemo(() => {
    const map = new Map<
      string,
      Map<
        string,
        Array<{
          sample: SampleItem;
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();

    for (const sRaw of availableSamples as SampleItem[]) {
      const s = sRaw as SampleItem;
      const fallbackParsed = parseSampleNameToParts(s.name);
      const flowcell = s.flowcell_id && s.flowcell_id !== "rand" ? s.flowcell_id : fallbackParsed.flowcell;
      const cycle = s.cycle_id && s.cycle_id !== "rand" ? s.cycle_id : fallbackParsed.cycle;
      const embryo = s.embryo_id && s.embryo_id !== "rand" ? s.embryo_id : fallbackParsed.embryo;
      const display = embryo;

      const parsed = { flowcell, cycle, embryo, displayName: display };

      if (!map.has(flowcell)) map.set(flowcell, new Map());
      const cycleMap = map.get(flowcell)!;
      if (!cycleMap.has(cycle)) cycleMap.set(cycle, []);
      cycleMap.get(cycle)!.push({ sample: s, parsed });
    }

    const sortedMap = new Map<
      string,
      Map<
        string,
        Array<{
          sample: SampleItem;
          parsed: ReturnType<typeof parseSampleNameToParts>;
        }>
      >
    >();
    Array.from(map.keys())
      .sort()
      .forEach((flow) => {
        const cycles = map.get(flow)!;
        const sortedCycles = new Map<
          string,
          Array<{
            sample: SampleItem;
            parsed: ReturnType<typeof parseSampleNameToParts>;
          }>
        >();
        Array.from(cycles.keys())
          .sort()
          .forEach((c) => {
            const arr = cycles.get(c)!;
            arr.sort((a, b) => (a.parsed.displayName > b.parsed.displayName ? 1 : -1));
            sortedCycles.set(c, arr);
          });
        sortedMap.set(flow, sortedCycles);
      });

    return sortedMap;
  }, [availableSamples]);

  // Helper function để flatten grouped samples
  const flattenGroupedSamples = (grouped: typeof groupedReferences) => {
    const result: SampleItem[] = [];
    for (const [, cycleMap] of grouped.entries()) {
      for (const [, arr] of cycleMap.entries()) {
        for (const { sample } of arr) {
          result.push(sample);
        }
      }
    }
    return result;
  };

  // Mảng flat để support Shift+Click range select - references
  const flattenedReferences = useMemo(() => flattenGroupedSamples(groupedReferences), [groupedReferences]);

  // Mảng flat để support Shift+Click range select - available samples
  const flattenedAvailable = useMemo(() => flattenGroupedSamples(groupedAvailable), [groupedAvailable]);

  const handleAddClick = () => {
    setSelectedForAdd(new Set());
    setAddDialogOpen(true);
  };

  const handleAddConfirm = () => {
    addReferences(selectedForAdd);
    if (onRefresh) {
      onRefresh();
    }
    setAddDialogOpen(false);
    setSelectedForAdd(new Set());
  };

  const handleRemoveClick = () => {
    if (selectedForRemove.size > 0) {
      removeReferences(selectedForRemove);
      setSelectedForRemove(new Set());
    }
  };

  const toggleSelect = (id: string, event?: React.MouseEvent, mode: "remove" | "add" = "remove") => {
    if (!id) return;

    const flattened = mode === "remove" ? flattenedReferences : flattenedAvailable;
    const selected = mode === "remove" ? selectedForRemove : selectedForAdd;
    const setSelected = mode === "remove" ? setSelectedForRemove : setSelectedForAdd;

    // Xử lý Shift+Click: toggle range từ lastClickedId đến id hiện tại
    if (event?.shiftKey && lastClickedId !== null) {
      const startIdx = flattened.findIndex((s) => s.id === lastClickedId);
      const endIdx = flattened.findIndex((s) => s.id === id);
      if (startIdx !== -1 && endIdx !== -1) {
        const [min, max] = startIdx < endIdx ? [startIdx, endIdx] : [endIdx, startIdx];
        setSelected((prev) => {
          const next = new Set(prev);
          const allSelected = Array.from({ length: max - min + 1 }, (_, i) => min + i).every((i) => flattened[i] && next.has(flattened[i].id));
          for (let i = min; i <= max; i++) {
            if (flattened[i]?.id) {
              if (allSelected) {
                next.delete(flattened[i].id);
              } else {
                next.add(flattened[i].id);
              }
            }
          }
          return next;
        });
      }
      return;
    }

    setSelected((prev) => {
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

  const headerRight = (
    <Stack direction="row" spacing={1} alignItems="center">
      <Button
        onClick={(e) => {
          e.stopPropagation();
          handleAddClick();
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
          if (selectedForRemove.size > 0) {
            handleRemoveClick();
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
          "&:hover": { bgcolor: "#DC2626", "& svg": { color: "#fff" } },
        }}
      >
        <Minus size={16} />
      </Button>
    </Stack>
  );

  return (
    <MUIAccordionPane title="Reference" defaultExpanded headerRight={headerRight}>
      <Box>
        {referenceSamples.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 3 }}>
            <Typography variant="body1">No references yet. Click Add to add one.</Typography>
          </Box>
        ) : (
          <Box
            sx={{
              maxHeight: "40vh",
              overflowY: "scroll",
              pr: 1,
              scrollbarGutter: "stable",
            }}
          >
            <Stack spacing={1}>
              {Array.from(groupedReferences.entries()).map(([flowcell, cycleMap]) => {
                const isOpenFlow = openFlowcells.has(flowcell);
                const totalCount = Array.from(cycleMap.values()).flat().length;
                return (
                  <Box
                    key={flowcell}
                    sx={{
                      p: 1.25,
                      borderRadius: 1,
                      border: "1px solid",
                      borderColor: "rgba(0,0,0,0.12)",
                      bgcolor: "transparent",
                      "&:hover": {
                        bgcolor: "#F9FAFB",
                      },
                      transition: "all 0.12s",
                    }}
                  >
                    {/* Flowcell Header */}
                    <Box sx={{ display: "flex", alignItems: "center", width: "100%" }}>
                      {/* Button mở/đóng cây */}
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleOpenFlowcell(flowcell);
                        }}
                        sx={{ mr: 0.5, p: 0.5 }}
                      >
                        <ChevronRight
                          size={16}
                          style={{
                            transform: isOpenFlow ? "rotate(90deg)" : "rotate(0deg)",
                            transition: "transform 0.2s ease-in-out",
                          }}
                        />
                      </IconButton>

                      {/* Title */}
                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          cursor: "pointer",
                          flex: 1,
                          userSelect: "none",
                        }}
                      >
                        <Typography variant="body2">{flowcell}</Typography>
                        <Typography variant="body1" sx={{ ml: 1 }}>
                          [{totalCount}]
                        </Typography>
                      </Box>
                    </Box>

                    <Collapse in={isOpenFlow} unmountOnExit>
                      <Box sx={{ p: 1 }}>
                        <Stack spacing={0}>
                          {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                            const cycleKey = `${flowcell}|${cycle}`;
                            const isOpenCycle = openCycles.has(cycleKey);
                            return (
                              <Box
                                key={cycle}
                                sx={{
                                  py: 1,
                                  borderRadius: 1,
                                  bgcolor: "transparent",
                                  "&:hover": {
                                    bgcolor: "#F9FAFB",
                                  },
                                  transition: "all 0.12s",
                                }}
                              >
                                {/* Cycle Header */}
                                <Box sx={{ display: "flex", alignItems: "center", width: "100%" }}>
                                  {/* Button mở/đóng cây con */}
                                  <IconButton
                                    size="small"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleOpenCycle(flowcell, cycle);
                                    }}
                                    sx={{ mr: 0.5, p: 0.5 }}
                                  >
                                    <ChevronRight
                                      size={16}
                                      style={{
                                        transform: isOpenCycle ? "rotate(90deg)" : "rotate(0deg)",
                                        transition: "transform 0.2s ease-in-out",
                                      }}
                                    />
                                  </IconButton>

                                  {/* Title */}
                                  <Box
                                    sx={{
                                      flex: 1,
                                      userSelect: "none",
                                    }}
                                  >
                                    <Typography variant="body2">{cycle}</Typography>
                                  </Box>
                                </Box>

                                <Collapse in={isOpenCycle} unmountOnExit>
                                  <Box sx={{ pl: 3.5, pt: 1 }}>
                                    <Stack spacing={1}>
                                      {arr.map(({ sample, parsed }: any) => {
                                        const isSelected = sample.id !== undefined && selectedForRemove.has(sample.id);
                                        return (
                                          <Box
                                            key={sample.id}
                                            role="button"
                                            onClick={(e) => toggleSelect(sample.id, e, "remove")}
                                            aria-pressed={isSelected}
                                            sx={{
                                              p: 1,
                                              borderRadius: 1,
                                              cursor: "pointer",
                                              borderColor: isSelected ? "primary.main" : "transparent",
                                              bgcolor: isSelected ? "#DBEAFE" : "transparent",
                                              transition: "all 0.12s",
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

      {/* Add Dialog */}
      <CenterDialog
        open={addDialogOpen}
        title={
          <Typography variant="h3" component="h3">
            Add Samples to Reference
          </Typography>
        }
        onClose={() => setAddDialogOpen(false)}
        onConfirm={handleAddConfirm}
        confirmLabel="Add"
        cancelLabel="Cancel"
      >
        <Box>
          {availableSamples.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 3 }}>
              <Typography variant="body1">All samples are already references</Typography>
            </Box>
          ) : (
            <Box
              sx={{
                maxHeight: "40vh",
                overflowY: "auto",
                pr: 1,
                scrollbarGutter: "stable",
                // border: 1,
                borderColor: "grey.200",
                p: 1,
                borderRadius: 1,
              }}
            >
              <Stack spacing={1}>
                {Array.from(groupedAvailable.entries()).map(([flowcell, cycleMap]) => {
                  const isOpenFlow = openFlowcells.has(flowcell);
                  const totalCount = Array.from(cycleMap.values()).flat().length;

                  // Check if all children in this flowcell are selected
                  const flowcellIds = Array.from(cycleMap.values())
                    .flat()
                    .map((item: any) => item.sample.id);
                  const isFlowcellSelected = flowcellIds.length > 0 && flowcellIds.every((id) => selectedForAdd.has(id));

                  return (
                    <Box
                      key={flowcell}
                      sx={{
                        p: 1.25,
                        borderRadius: 1,
                        border: "1px solid",
                        borderColor: isFlowcellSelected ? "primary.main" : "rgba(0,0,0,0.12)",
                        bgcolor: isFlowcellSelected ? "#DBEAFE" : "transparent",
                        color: isFlowcellSelected ? "primary.main" : "text.primary",
                        "&:hover": {
                          bgcolor: isFlowcellSelected ? "#DBEAFE" : "#F9FAFB",
                        },
                        transition: "all 0.12s",
                      }}
                    >
                      {/* Flowcell Header */}
                      <Box sx={{ display: "flex", alignItems: "center", width: "100%" }}>
                        {/* Button mở/đóng cây */}
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleOpenFlowcell(flowcell);
                          }}
                          sx={{ mr: 0.5, p: 0.5 }}
                        >
                          <ChevronRight
                            size={16}
                            style={{
                              transform: isOpenFlow ? "rotate(90deg)" : "rotate(0deg)",
                              transition: "transform 0.2s ease-in-out",
                            }}
                          />
                        </IconButton>

                        {/* Title click để chọn con */}
                        <Box
                          onClick={() => {
                            // Toggle all children in this flowcell
                            const allSelected = flowcellIds.every((id) => selectedForAdd.has(id));
                            setSelectedForAdd((prev) => {
                              const next = new Set(prev);
                              if (allSelected) {
                                flowcellIds.forEach((id) => next.delete(id));
                              } else {
                                flowcellIds.forEach((id) => next.add(id));
                              }
                              return next;
                            });
                          }}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            cursor: "pointer",
                            flex: 1,
                            userSelect: "none",
                          }}
                        >
                          <Typography variant="body2">{flowcell}</Typography>
                          <Typography variant="body1" sx={{ ml: 1 }}>
                            [{totalCount}]
                          </Typography>
                        </Box>
                      </Box>

                      <Collapse in={isOpenFlow} unmountOnExit>
                        <Box sx={{ p: 1 }}>
                          <Stack spacing={0}>
                            {Array.from(cycleMap.entries()).map(([cycle, arr]) => {
                              const cycleKey = `${flowcell}|${cycle}`;
                              const isOpenCycle = openCycles.has(cycleKey);

                              // Check if all children in this cycle are selected
                              const cycleIds = arr.map((item: any) => item.sample.id);
                              const isCycleSelected = cycleIds.length > 0 && cycleIds.every((id) => selectedForAdd.has(id));

                              return (
                                <Box
                                  key={cycle}
                                  sx={{
                                    py: 1,
                                    borderRadius: 1,
                                    borderColor: isCycleSelected ? "primary.main" : "transparent",
                                    bgcolor: isCycleSelected ? "#DBEAFE" : "transparent",
                                    color: isCycleSelected ? "primary.main" : "text.primary",
                                    "&:hover": {
                                      bgcolor: isCycleSelected ? "#DBEAFE" : "#F9FAFB",
                                    },
                                    transition: "all 0.12s",
                                  }}
                                >
                                  {/* Cycle Header */}
                                  <Box sx={{ display: "flex", alignItems: "center", width: "100%" }}>
                                    {/* Button mở/đóng cây con */}
                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        toggleOpenCycle(flowcell, cycle);
                                      }}
                                      sx={{ mr: 0.5, p: 0.5 }}
                                    >
                                      <ChevronRight
                                        size={16}
                                        style={{
                                          transform: isOpenCycle ? "rotate(90deg)" : "rotate(0deg)",
                                          transition: "transform 0.2s ease-in-out",
                                        }}
                                      />
                                    </IconButton>

                                    {/* Title click để chọn con */}
                                    <Box
                                      onClick={() => {
                                        // Toggle all children in this cycle
                                        const allSelected = cycleIds.every((id) => selectedForAdd.has(id));
                                        setSelectedForAdd((prev) => {
                                          const next = new Set(prev);
                                          if (allSelected) {
                                            cycleIds.forEach((id) => next.delete(id));
                                          } else {
                                            cycleIds.forEach((id) => next.add(id));
                                          }
                                          return next;
                                        });
                                      }}
                                      sx={{
                                        cursor: "pointer",
                                        flex: 1,
                                        userSelect: "none",
                                      }}
                                    >
                                      <Typography variant="body2">{cycle}</Typography>
                                    </Box>
                                  </Box>

                                  <Collapse in={isOpenCycle} unmountOnExit>
                                    <Box sx={{ pl: 3.5, pt: 1 }}>
                                      <Stack spacing={1}>
                                        {arr.map(({ sample, parsed }: any) => {
                                          const isSelected = sample.id !== undefined && selectedForAdd.has(sample.id);
                                          return (
                                            <Box
                                              key={sample.id}
                                              role="button"
                                              onClick={(e) => toggleSelect(sample.id, e, "add")}
                                              aria-pressed={isSelected}
                                              sx={{
                                                p: 1,
                                                borderRadius: 1,
                                                cursor: "pointer",
                                                borderColor: isSelected ? "primary.main" : "transparent",
                                                bgcolor: isSelected ? "#DBEAFE" : "transparent",
                                                transition: "all 0.12s",
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
      </CenterDialog>
    </MUIAccordionPane>
  );
}
