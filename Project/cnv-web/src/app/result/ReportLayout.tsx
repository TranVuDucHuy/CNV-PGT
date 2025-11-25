"use client";

import { ResultSummary } from "@/types/result";
import { formatDateTime } from "@/utils/datetimeFormatter";
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  Alert,
  Skeleton,
  Typography,
  Stack,
} from "@mui/material";
import { useEffect, useState, useRef, useCallback } from "react";

const MIN_LEFT_WIDTH = 275;
const MAX_LEFT_WIDTH = 800;
const DEFAULT_LEFT_WIDTH = 300;

interface ReportLayoutProps {
  results: ResultSummary[];
  selectedResultId?: string;
  onResultClick: (id: string) => void;
  loading: boolean;
  rightPannel: React.ReactNode;
  error?: string | null;
}

const ReportLayout: React.FC<ReportLayoutProps> = ({
  results,
  selectedResultId,
  onResultClick,
  loading,
  rightPannel,
  error = null,
}) => {
  const [leftWidth, setLeftWidth] = useState<number>(DEFAULT_LEFT_WIDTH);

  const draggingRef = useRef<boolean>(false);
  const startXRef = useRef<number>(0);
  const startWidthRef = useRef<number>(leftWidth);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (e.pointerType === "mouse" && (e as any).button !== 0) return;
      draggingRef.current = true;
      startXRef.current = e.clientX;
      startWidthRef.current = leftWidth;

      try {
        (e.target as Element).setPointerCapture?.(e.pointerId);
      } catch (err) {
        // ignore
      }

      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
      e.preventDefault();
    },
    [leftWidth]
  );

  const onPointerMove = useCallback((ev: PointerEvent) => {
    if (!draggingRef.current) return;
    const dx = ev.clientX - startXRef.current;
    const newWidth = Math.round(startWidthRef.current + dx);
    const clamped = Math.max(
      MIN_LEFT_WIDTH,
      Math.min(MAX_LEFT_WIDTH, newWidth)
    );
    setLeftWidth(clamped);
  }, []);

  const onPointerUp = useCallback(
    (ev?: PointerEvent) => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      startWidthRef.current = leftWidth;
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      try {
        (ev?.target as Element)?.releasePointerCapture?.(
          (ev as any)?.pointerId
        );
      } catch (err) {
        // ignore
      }
    },
    [leftWidth]
  );

  useEffect(() => {
    const pm = (e: PointerEvent) => onPointerMove(e);
    const pu = (e: PointerEvent) => onPointerUp(e);
    window.addEventListener("pointermove", pm);
    window.addEventListener("pointerup", pu);
    window.addEventListener("pointercancel", pu);
    return () => {
      window.removeEventListener("pointermove", pm);
      window.removeEventListener("pointerup", pu);
      window.removeEventListener("pointercancel", pu);
    };
  }, [onPointerMove, onPointerUp]);

  const onDividerDoubleClick = useCallback(() => {
    setLeftWidth(DEFAULT_LEFT_WIDTH);
  }, []);

  return (
    <Box sx={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Left Panel - Results List */}
      <Box
        sx={{
          width: leftWidth,
          minWidth: MIN_LEFT_WIDTH,
          maxWidth: MAX_LEFT_WIDTH,
          borderRight: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h5">Results</Typography>
        </Box>
        <Box sx={{ flex: 1, overflow: "auto", padding: 1 }}>
          {loading && (
            <Box sx={{ p: 2 }}>
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} height={60} sx={{ mb: 1 }} />
              ))}
            </Box>
          )}
          {error && (
            <Box sx={{ p: 2 }}>
              <Alert severity="error">{error}</Alert>
            </Box>
          )}
          {!loading && !error && results.length === 0 && (
            <Box sx={{ p: 2 }}>
              <Typography color="text.secondary">No results found</Typography>
            </Box>
          )}
          {!loading && !error && results.length > 0 && (
            <List>
              {results.map((result) => (
                <ListItemButton
                  key={result.id}
                  onClick={() => onResultClick(result.id)}
                  selected={result.id === selectedResultId}
                  sx={{
                    elevation: 1,
                    boxShadow: result.id === selectedResultId ? 3 : 0,
                    borderRadius: 2,
                    mb: 1,
                  }}
                >
                  <ListItemText
                    primary={result.sample_name}
                    secondary={
                      <Stack direction="column" justifyContent="flex-start">
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography
                            component="span"
                            variant="body2"
                            color="text.secondary"
                          >
                            Algorithm:
                          </Typography>
                          <Typography
                            component="span"
                            variant="body2"
                            color="text.secondary"
                            fontWeight={"bold"}
                          >
                            {result.algorithm_name}
                          </Typography>
                        </Stack>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography
                            component="span"
                            variant="body2"
                            color="text.secondary"
                          >
                            Created At:
                          </Typography>
                          <Typography
                            component="span"
                            variant="caption"
                            color="text.secondary"
                            fontWeight={"bold"}
                          >
                            {formatDateTime(result.created_at)}
                          </Typography>
                        </Stack>
                      </Stack>
                    }
                  />
                </ListItemButton>
              ))}
            </List>
          )}
        </Box>
      </Box>

      {/* Divider */}
      <Box
        role="separator"
        aria-orientation="vertical"
        onPointerDown={onPointerDown}
        onDoubleClick={onDividerDoubleClick}
        sx={{
          width: 6,
          cursor: "col-resize",
          display: "flex",
          alignItems: "stretch",
          justifyContent: "center",
          userSelect: "none",
          touchAction: "none",
          bgcolor: "transparent",
          "&:hover > div": {
            bgcolor: "primary.main",
          },
        }}
        title="Drag to resize (double-click to reset)"
      >
        <Box
          sx={{
            width: "100%",
            bgcolor: "divider",
            borderRadius: 1,
            alignSelf: "stretch",
          }}
        />
      </Box>

      {/* Right Panel - Blank */}
      <Box
        sx={{
          flex: 1,
          bgcolor: "grey.50",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {rightPannel}
      </Box>
    </Box>
  );
};

export default ReportLayout;
