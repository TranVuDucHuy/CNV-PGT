import { Box, IconButton, Stack, SxProps, Theme, Typography } from "@mui/material";
import React, { useCallback, useMemo, useRef, useState } from "react";
import { Resizable } from "re-resizable";
import CloseIcon from "@mui/icons-material/Close";
import { ExportMenuButton, ExportAction } from "./ExportMenuButton";

export type DynamicStackDirection = "row" | "column";

export interface DynamicStackItem<T = unknown> {
  id: string;
  title: string;
  content: React.ReactNode;
  initialHeight?: string | number;
  minHeight?: string | number;
  maxHeight?: string | number;
  onClose?: () => void;
  exportOptions?: ExportAction[];
}

export interface DynamicStackProps<T = unknown> {
  items: DynamicStackItem<T>[];
  direction?: DynamicStackDirection;
  sx?: SxProps<Theme>;
  onOrderChange?: (items: DynamicStackItem<T>[]) => void;
}

const getMainAxis = (direction: DynamicStackDirection, rect: DOMRect) => {
  if (direction === "row") {
    return { start: rect.left, end: rect.right, size: rect.width };
  }
  return { start: rect.top, end: rect.bottom, size: rect.height };
};

export const DynamicStack = <T,>({ items, direction = "column", sx, onOrderChange }: DynamicStackProps<T>) => {
  const [internalItems, setInternalItems] = useState(items);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number } | null>(null);
  const [cursorPos, setCursorPos] = useState<{ x: number; y: number } | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const [itemDimensions, setItemDimensions] = useState<Record<string, { width: number; height: number }>>({});
  const [itemHeights, setItemHeights] = useState<Record<string, number>>({});

  const containerRef = useRef<HTMLDivElement | null>(null);
  const itemRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const scrollIntervalRef = useRef<number | null>(null);
  const cursorPosRef = useRef<{ x: number; y: number } | null>(null);

  React.useEffect(() => {
    setInternalItems(items);
  }, [items]);

  // Cleanup scroll interval on unmount or when dragging stops
  React.useEffect(() => {
    if (!draggingId && scrollIntervalRef.current) {
      clearInterval(scrollIntervalRef.current);
      scrollIntervalRef.current = null;
    }
  }, [draggingId]);

  const registerItemRef = useCallback((id: string, el: HTMLDivElement | null) => {
    itemRefs.current[id] = el;
    // Store dimensions when ref is registered, but only if they've changed
    if (el) {
      const width = el.offsetWidth;
      const height = el.offsetHeight;

      setItemDimensions((prev) => {
        const existing = prev[id];
        // Only update if dimensions actually changed
        if (existing?.width === width && existing?.height === height) {
          return prev;
        }
        return {
          ...prev,
          [id]: { width, height },
        };
      });
    }
  }, []);

  const isRow = direction === "row";

  const handleMouseDown = useCallback((event: React.MouseEvent, id: string) => {
    event.preventDefault();
    const headerEl = event.currentTarget as HTMLDivElement;
    const headerRect = headerEl.getBoundingClientRect();
    const offsetX = event.clientX - headerRect.left;
    const offsetY = event.clientY - headerRect.top;
    setDraggingId(id);
    setDragOffset({ x: offsetX, y: offsetY });
    setCursorPos({ x: event.clientX, y: event.clientY });
    cursorPosRef.current = { x: event.clientX, y: event.clientY };

    // We'll compute dropIndex in the next render
    setDropIndex(null);

    // Auto-scroll will be handled in handleMouseMove
  }, []);

  // Render item content - used for actual items, placeholders, and dragged items
  const renderItemContent = useCallback(
    (item: DynamicStackItem<T>, scale: number = 1, enableDrag: boolean = false) => {
      return (
        <Box
          sx={{
            height: "100%",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            transform: scale !== 1 ? `scale(${scale})` : undefined,
            transformOrigin: "top left",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            borderRadius: 1,
            border: "1px solid",
            borderColor: "grey.300",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              flexDirection: "row",
              bgcolor: "primary.light",
              p: 0.5,
            }}
          >
            <Box
              onMouseDown={enableDrag ? (e) => handleMouseDown(e, item.id) : undefined}
              sx={{
                cursor: enableDrag ? "move" : "default",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                px: 1.25,
                py: 0.5,
                userSelect: "none",
                flexGrow: 1,
              }}
            >
              <Typography variant="h4" noWrap sx={{ flex: 1, minWidth: 0 }}>
                {item.title}
              </Typography>
            </Box>
            {item.exportOptions && item.exportOptions.length > 0 && <ExportMenuButton actions={item.exportOptions} size="small" />}
            {item.onClose && (
              <IconButton onClick={item.onClose} size="small">
                <CloseIcon />
              </IconButton>
            )}
          </Box>

          <Box
            sx={{
              overflow: "auto",
              flexGrow: 1,
              minHeight: 0,
            }}
          >
            {item.content}
          </Box>
        </Box>
      );
    },
    [handleMouseDown]
  );

  const handleAutoScroll = useCallback(
    (clientX: number, clientY: number) => {
      if (!containerRef.current) return;

      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const scrollThreshold = 100; // pixels from edge to trigger scroll
      const maxScrollSpeed = 20; // max pixels per frame

      let scrollSpeed = 0;
      let shouldScroll = false;

      if (isRow) {
        // Check horizontal scrolling
        const distanceFromLeft = clientX - rect.left;
        const distanceFromRight = rect.right - clientX;

        if (distanceFromLeft < scrollThreshold && distanceFromLeft > 0) {
          // Scroll left
          const intensity = 1 - distanceFromLeft / scrollThreshold;
          scrollSpeed = -intensity * maxScrollSpeed;
          shouldScroll = true;
        } else if (distanceFromRight < scrollThreshold && distanceFromRight > 0) {
          // Scroll right
          const intensity = 1 - distanceFromRight / scrollThreshold;
          scrollSpeed = intensity * maxScrollSpeed;
          shouldScroll = true;
        }

        if (shouldScroll && scrollSpeed !== 0) {
          container.scrollLeft += scrollSpeed;
        }
      } else {
        // Check vertical scrolling
        const distanceFromTop = clientY - rect.top;
        const distanceFromBottom = rect.bottom - clientY;

        if (distanceFromTop < scrollThreshold && distanceFromTop > 0) {
          // Scroll up
          const intensity = 1 - distanceFromTop / scrollThreshold;
          scrollSpeed = -intensity * maxScrollSpeed;
          shouldScroll = true;
        } else if (distanceFromBottom < scrollThreshold && distanceFromBottom > 0) {
          // Scroll down
          const intensity = 1 - distanceFromBottom / scrollThreshold;
          scrollSpeed = intensity * maxScrollSpeed;
          shouldScroll = true;
        }

        if (shouldScroll && scrollSpeed !== 0) {
          container.scrollTop += scrollSpeed;
        }
      }
    },
    [isRow]
  );

  const computeDropIndex = useCallback(
    (clientX: number, clientY: number, draggedId: string) => {
      const pointer = isRow ? clientX : clientY;

      // Find the dragged item's current index
      const draggedIndex = internalItems.findIndex((item) => item.id === draggedId);

      // Build entries including the dragged item (it's a placeholder)
      const entries = internalItems
        .map((item, idx) => {
          const el = itemRefs.current[item.id];
          if (!el) return null;
          const rect = el.getBoundingClientRect();
          const { start, end } = getMainAxis(direction, rect);
          const mid = (start + end) / 2;
          return { id: item.id, start, end, mid, originalIndex: idx };
        })
        .filter((e): e is NonNullable<typeof e> => !!e);

      if (!entries.length) return null;

      // Find which item the pointer is over
      for (let i = 0; i < entries.length; i++) {
        const entry = entries[i];

        // Skip the dragged item itself when determining position
        if (entry.id === draggedId) {
          continue;
        }

        // If pointer is within this item's bounds
        if (pointer >= entry.start && pointer < entry.end) {
          const targetIndex = entry.originalIndex;

          // If in first half of item, insert before it
          if (pointer < entry.mid) {
            return targetIndex;
          }

          // If in second half, insert after it (which is targetIndex + 1)
          return targetIndex + 1;
        }
      }

      // If pointer is before all items
      if (pointer < entries[0].start) {
        return 0;
      }

      // If pointer is after all items
      return internalItems.length;
    },
    [direction, internalItems, isRow]
  );

  const handleMouseMove = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (!draggingId) return;
      const newPos = { x: event.clientX, y: event.clientY };
      setCursorPos(newPos);
      cursorPosRef.current = newPos;

      // Handle auto-scroll
      handleAutoScroll(event.clientX, event.clientY);

      const di = computeDropIndex(event.clientX, event.clientY, draggingId);
      setDropIndex(di);
    },
    [computeDropIndex, draggingId, handleAutoScroll]
  );

  const finalizeDrop = useCallback(() => {
    // Clear scroll interval
    if (scrollIntervalRef.current) {
      clearInterval(scrollIntervalRef.current);
      scrollIntervalRef.current = null;
    }

    if (!draggingId || dropIndex == null) {
      setDraggingId(null);
      setDragOffset(null);
      setCursorPos(null);
      setDropIndex(null);
      return;
    }

    const currentIndex = internalItems.findIndex((i) => i.id === draggingId);
    if (currentIndex === -1) {
      setDraggingId(null);
      setDragOffset(null);
      setCursorPos(null);
      setDropIndex(null);
      return;
    }

    // Check if the drop position is the same as current position
    // When dragging forward: if dropIndex == currentIndex + 1, no change
    // When dragging backward: if dropIndex == currentIndex, no change
    const isNoChange = dropIndex === currentIndex || dropIndex === currentIndex + 1;

    if (isNoChange) {
      setDraggingId(null);
      setDragOffset(null);
      setCursorPos(null);
      setDropIndex(null);
      return;
    }

    const updated = [...internalItems];
    const [moved] = updated.splice(currentIndex, 1);
    // After removing the item, adjust the insert index
    const insertIndex = dropIndex > currentIndex ? dropIndex - 1 : dropIndex;
    updated.splice(insertIndex, 0, moved);

    setInternalItems(updated);
    onOrderChange?.(updated);

    setDraggingId(null);
    setDragOffset(null);
    setCursorPos(null);
    setDropIndex(null);
  }, [draggingId, dropIndex, internalItems, onOrderChange]);

  const handleMouseUpOrLeave = useCallback(() => {
    finalizeDrop();
  }, [finalizeDrop]);

  const containerSx: SxProps<Theme> = useMemo(
    () => ({
      position: "relative",
      // display: "flex",
      // flexDirection: isRow ? "row" : "column",
      // flex: "0 0 auto",
      overflow: "auto",
      ...sx,
    }),
    [isRow, sx]
  );

  const draggingItem = draggingId ? internalItems.find((it) => it.id === draggingId) : null;

  return (
    <Box ref={containerRef} sx={containerSx} onMouseMove={handleMouseMove} onMouseUp={handleMouseUpOrLeave} onMouseLeave={handleMouseUpOrLeave}>
      {internalItems.map((item, index) => {
        const currentIndex = draggingId ? internalItems.findIndex((i) => i.id === draggingId) : -1;

        const showPlaceholder = draggingId !== null && index === currentIndex;

        // Show divider before this item if dropIndex matches this position
        const showDividerBefore = dropIndex !== null && dropIndex === index;

        // Show divider after this item if it's the last and dropIndex is at the end
        const isLast = index === internalItems.length - 1;
        const showDividerAfter = isLast && dropIndex === internalItems.length;

        return (
          <React.Fragment key={item.id}>
            {showDividerBefore && !showPlaceholder && (
              <Box
                sx={{
                  ...(isRow ? { width: 2, height: "100%" } : { height: 2, width: "100%" }),
                  bgcolor: "primary.main",
                  flexShrink: 0,
                }}
              />
            )}

            {showPlaceholder ? (
              <Box
                ref={(el: HTMLDivElement | null) => registerItemRef(item.id, el)}
                sx={{
                  flexShrink: 0,
                  flexGrow: 1,
                  opacity: 0.5,
                  ...(isRow
                    ? {
                        width: itemDimensions[item.id]?.width || 260,
                        minWidth: itemDimensions[item.id]?.width || 260,
                      }
                    : {
                        height: itemDimensions[item.id]?.height || 80,
                        minHeight: itemDimensions[item.id]?.height || 80,
                        width: "100%",
                      }),
                }}
              >
                {renderItemContent(item)}
              </Box>
            ) : (
              <Resizable
                size={{
                  width: "100%",
                  height: itemHeights[item.id] || item.initialHeight || 200,
                }}
                minHeight={item.minHeight || 100}
                maxHeight={item.maxHeight || "100%"}
                enable={{
                  top: false,
                  right: false,
                  bottom: true,
                  left: false,
                  topRight: false,
                  bottomRight: false,
                  bottomLeft: false,
                  topLeft: false,
                }}
                onResizeStop={(e, direction, ref, d) => {
                  setItemHeights((prev) => ({
                    ...prev,
                    [item.id]: (itemHeights[item.id] || (typeof item.initialHeight === "number" ? item.initialHeight : 200)) + d.height,
                  }));
                }}
                style={{
                  position: "relative",
                  flexShrink: 0,
                  flex: "0 0 auto",
                  marginBottom: 12,
                }}
              >
                <Box
                  ref={(el: HTMLDivElement | null) => registerItemRef(item.id, el)}
                  sx={{
                    height: "100%",
                    width: "100%",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  {renderItemContent(item, 1, true)}
                </Box>
              </Resizable>
            )}

            {showDividerAfter && (
              <Box
                sx={{
                  ...(isRow ? { width: 2, height: "100%" } : { height: 2, width: "100%" }),
                  bgcolor: "primary.main",
                  flexShrink: 0,
                }}
              />
            )}
          </React.Fragment>
        );
      })}

      {items.length > 0 && <Box sx={{ height: 200 }} />}

      {draggingItem && cursorPos && dragOffset && (
        <Box
          sx={{
            position: "fixed",
            zIndex: 1300,
            pointerEvents: "none",
            top: cursorPos.y - dragOffset.y * 0.5,
            left: cursorPos.x - dragOffset.x * 0.5,
            boxShadow: 6,
            width: itemDimensions[draggingItem.id]?.width || 260,
            height: itemDimensions[draggingItem.id]?.height || 200,
          }}
        >
          {renderItemContent(draggingItem)}
        </Box>
      )}
    </Box>
  );
};

export default DynamicStack;
