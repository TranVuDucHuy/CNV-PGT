// dashboard.tsx
"use client";

import React, { useRef, useState, useCallback, useEffect } from "react";
import { Typography } from "@mui/material";
import SamplePane from "@/features/sample/SamplePane";
import AlgorithmPane from "@/features/algorithm/AlgorithmPane";
import ResultPane from "@/features/result/ResultPane";
import ViewPane from "@/features/view/ViewPane";
// import ContentPane from "@/features/content/ContentPane";
// import { ViewProvider } from "@/features/view/viewHandle";
import { ResultProvider } from "@/features/result/resultHandle";
import ReferencePane from "@/features/reference/ReferencePane";
import useSampleHandle from "@/features/sample/sampleHandle";
import TiledContentPane from "@/features/content/TiledContentPane";
import { Provider } from "react-redux";
import { store } from "@/utils/store"; // Import store của bạn
import colors from "@/theme/colors";

const MIN_LEFT_WIDTH = 0; // px - min width of left pane
const MAX_LEFT_WIDTH = 360; // px - max width of left pane
const DEFAULT_LEFT_WIDTH = 320; // px - initial (matches w-60 ~ 240px)

const DashboardView: React.FC = () => {
  const { samples, refresh } = useSampleHandle();

  // width of left pane in pixels
  const [leftWidth, setLeftWidth] = useState<number>(DEFAULT_LEFT_WIDTH);
  // dragging state
  const draggingRef = useRef<boolean>(false);
  const startXRef = useRef<number>(0);
  const startWidthRef = useRef<number>(leftWidth);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // handler start drag
  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      // only left mouse or touch
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

  // move
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

  // end drag
  const onPointerUp = useCallback(
    (ev?: PointerEvent) => {
      if (!draggingRef.current) return;
      draggingRef.current = false;
      startWidthRef.current = leftWidth;
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      try {
        // if pointer capture was set, release for all elements (best-effort)
        (ev?.target as Element)?.releasePointerCapture?.(
          (ev as any)?.pointerId
        );
      } catch (err) {
        // ignore
      }
    },
    [leftWidth]
  );

  // attach global listeners while mounted
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

  // double-click divider to reset to default
  const onDividerDoubleClick = useCallback(() => {
    setLeftWidth(DEFAULT_LEFT_WIDTH);
  }, []);

  return (
    <div className="flex flex-col h-screen font-sans">
      {/* Menu Bar */}
      <nav
        className="px-4 py-3 flex items-center"
        style={{ backgroundColor: colors.primary1 }}
      >
        <Typography
          variant="h1"
          component="h1"
          sx={{ color: "primary1.contrastText" }}
        >
          CNV Analysis Dashboard
        </Typography>
      </nav>

      {/* Split Pane */}
      <div ref={containerRef} className="flex flex-1" style={{ minHeight: 0 }}>
        <Provider store={store}>
            <ResultProvider>
              {/* Left Pane - resizable */}
              <div
                className=" border-gray-300 p-2.5 max-h-screen overflow-y-scroll space-y-3"
                style={{
                  width: leftWidth,
                  minWidth: MIN_LEFT_WIDTH,
                  maxWidth: MAX_LEFT_WIDTH,
                  height: "100%",
                  scrollbarGutter: "stable",
                  backgroundColor: colors.background1,
                }}
              >
                {/* <ContentPane /> */}
                <SamplePane />
                <ReferencePane samples={samples} onRefresh={refresh} />
                <AlgorithmPane />
                <ResultPane />
                <ViewPane />
              </div>

              {/* Divider / Resizer */}
              <div
                role="separator"
                aria-orientation="vertical"
                onPointerDown={onPointerDown}
                onDoubleClick={onDividerDoubleClick}
                className="relative"
                style={{
                  width: 6, // hit area
                  cursor: "col-resize",
                  display: "flex",
                  alignItems: "stretch",
                  justifyContent: "center",
                  userSelect: "none",
                  touchAction: "none",
                  background: "transparent",
                }}
                title="Drag to resize left pane (double-click to reset)"
              >
                {/* thin visible bar centered in the hit area */}
                <div
                  style={{
                    width: 2,
                    background: "rgba(0,0,0,0.08)",
                    borderRadius: 2,
                    alignSelf: "stretch",
                    margin: "6px 0",
                  }}
                />
              </div>

              {/* Right Pane - Content Area */}
              <div className="flex-1 bg-gray-100 flex min-w-0">
                <div
                  id="contentArea"
                  className="w-full h-full bg-white flex flex-col min-w-0"
                >
                  <TiledContentPane />
                </div>
              </div>
            </ResultProvider>
        </Provider>
      </div>
    </div>
  );
};

export default DashboardView;
