// components/DraggableWindow.tsx
"use client";
import React from "react";
import { X } from "lucide-react";

type Rect = { top: number; left: number; width: number; height: number };

type Props = {
  id: string;
  title: string;
  initial?: Partial<Rect>;
  minWidth?: number;
  minHeight?: number;
  containerRef: React.RefObject<HTMLElement | null>;
  onClose?: () => void;
  children?: React.ReactNode;
  onBringToFront?: () => void;
  zIndex?: number;
};

type ResizeHandle =
  | "left"
  | "right"
  | "top"
  | "bottom"
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right"
  | null;

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(v, b));

export default function DraggableWindow({
  id,
  title,
  initial = {},
  minWidth = 240,
  minHeight = 120,
  containerRef,
  onClose,
  children,
  onBringToFront,
  zIndex = 1,
}: Props) {
  const [rect, setRect] = React.useState<Rect>({
    top: initial.top ?? 20,
    left: initial.left ?? 20,
    width: initial.width ?? 740,
    height: initial.height ?? 360,
  });

  const rectRef = React.useRef(rect);
  React.useEffect(() => { rectRef.current = rect; }, [rect]);

  const draggingRef = React.useRef(false);
  const resizingRef = React.useRef<ResizeHandle>(null);

  const dragStart = React.useRef({ x: 0, y: 0, left: 0, top: 0 });
  const resizeStart = React.useRef({ x: 0, y: 0, left: 0, top: 0, width: 0, height: 0 });

  const rafRef = React.useRef<number | null>(null);
  const pendingRef = React.useRef<Partial<Rect> | null>(null);

  const getContainerBounds = React.useCallback(() => {
    const c = containerRef?.current;
    if (!c) return null;
    return c.getBoundingClientRect();
  }, [containerRef]);

  const commitPending = React.useCallback(() => {
    if (!pendingRef.current) return;
    const next = { ...rectRef.current, ...pendingRef.current };
    pendingRef.current = null;
    rafRef.current = null;
    setRect(next);
  }, []);

  const scheduleUpdate = React.useCallback((update: Partial<Rect>) => {
    pendingRef.current = { ...(pendingRef.current ?? {}), ...update };
    if (rafRef.current == null) {
      rafRef.current = requestAnimationFrame(commitPending);
    }
  }, [commitPending]);

  // ----------- Dragging -----------  
  const onHeaderPointerDown = (e: React.PointerEvent) => {
    const target = e.target as HTMLElement;
    // Nếu nhấn vào button/icon, không drag
    if (target.closest("button")) return;

    if (e.pointerType === "mouse" && e.button !== 0) return;
    try { (e.currentTarget as Element).setPointerCapture(e.pointerId); } catch {}
    draggingRef.current = true;
    dragStart.current = { x: e.clientX, y: e.clientY, left: rectRef.current.left, top: rectRef.current.top };
    onBringToFront?.();
    document.body.style.userSelect = "none";
    e.preventDefault();
  };

  React.useEffect(() => {
    const onPointerMove = (ev: PointerEvent) => {
      if (draggingRef.current) {
        const { x, y, left, top } = dragStart.current;
        const dx = ev.clientX - x;
        const dy = ev.clientY - y;
        const container = getContainerBounds();
        if (!container) return;
        const newLeft = clamp(left + dx, 0, container.width - rectRef.current.width);
        const newTop = clamp(top + dy, 0, container.height - rectRef.current.height);
        scheduleUpdate({ left: newLeft, top: newTop });
      }
    };
    const onPointerUp = () => {
      draggingRef.current = false;
      resizingRef.current = null;
      document.body.style.userSelect = "";
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      pendingRef.current = null;
      document.body.style.userSelect = "";
    };
  }, [getContainerBounds, scheduleUpdate]);

  // ----------- Resizing -----------  
  const onResizerPointerDown = (handle: ResizeHandle) => (e: React.PointerEvent) => {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    try { (e.currentTarget as Element).setPointerCapture(e.pointerId); } catch {}
    resizingRef.current = handle;
    const r = rectRef.current;
    resizeStart.current = { x: e.clientX, y: e.clientY, left: r.left, top: r.top, width: r.width, height: r.height };
    onBringToFront?.();
    document.body.style.userSelect = "none";
    e.stopPropagation();
    e.preventDefault();
  };

  React.useEffect(() => {
    const onPointerMove = (ev: PointerEvent) => {
      const handle = resizingRef.current;
      if (!handle) return;
      const { x, y, left, top, width, height } = resizeStart.current;
      const dx = ev.clientX - x;
      const dy = ev.clientY - y;
      const container = getContainerBounds();
      if (!container) return;

      let newLeft = left, newTop = top, newW = width, newH = height;

      if (handle.includes("left")) {
        const proposedLeft = clamp(left + dx, 0, left + width - minWidth);
        newLeft = proposedLeft;
        newW = width - (proposedLeft - left);
      }
      if (handle.includes("right")) newW = clamp(width + dx, minWidth, container.width - left);
      if (handle.includes("top")) {
        const proposedTop = clamp(top + dy, 0, top + height - minHeight);
        newTop = proposedTop;
        newH = height - (proposedTop - top);
      }
      if (handle.includes("bottom")) newH = clamp(height + dy, minHeight, container.height - top);

      newLeft = clamp(newLeft, 0, container.width - newW);
      newTop = clamp(newTop, 0, container.height - newH);
      newW = clamp(newW, minWidth, container.width - newLeft);
      newH = clamp(newH, minHeight, container.height - newTop);

      scheduleUpdate({ left: newLeft, top: newTop, width: newW, height: newH });
    };
    const onPointerUp = () => {
      resizingRef.current = null;
      document.body.style.userSelect = "";
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("pointercancel", onPointerUp);
      resizingRef.current = null;
      document.body.style.userSelect = "";
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      pendingRef.current = null;
    };
  }, [getContainerBounds, minWidth, minHeight, scheduleUpdate]);

  // ----------- Render -----------  
  const style: React.CSSProperties = {
    position: "absolute",
    top: rect.top,
    left: rect.left,
    width: rect.width,
    height: rect.height,
    boxShadow: "0 10px 30px rgba(0,0,0,0.18)",
    border: "1px solid rgba(0,0,0,0.08)",
    background: "#fff",
    display: "flex",
    flexDirection: "column",
    zIndex,
    overflow: "hidden",
    borderRadius: 6,
    userSelect: "none",
  };

  const EDGE = 12;
  const resizerCommon: React.CSSProperties = { position: "absolute", zIndex: 20 };

  return (
    <div style={style} onPointerDown={() => onBringToFront?.()}>
      {/* Header */}
      <div
        onPointerDown={onHeaderPointerDown}
        style={{
          height: 36,
          background: "#f3f4f6",
          borderBottom: "1px solid rgba(0,0,0,0.06)",
          cursor: "grab",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 10px",
          flexShrink: 0,
        }}
      >
        <div style={{ fontWeight: 600, fontSize: 13 }}>{title}</div>
        <div>
          <button
            aria-label="close"
            onClick={(ev) => { ev.stopPropagation(); onClose?.(); }}
            style={{
              width: 28,
              height: 28,
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              borderRadius: 4,
              border: "none",
              background: "transparent",
              cursor: "pointer",
            }}
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        <div style={{ width: "100%", height: "100%", overflow: "auto" }}>{children}</div>
      </div>

      {/* Resizers */}
      <div onPointerDown={onResizerPointerDown("left")} style={{ ...resizerCommon, left: 0, top: EDGE, bottom: EDGE, width: EDGE, cursor: "ew-resize" }} />
      <div onPointerDown={onResizerPointerDown("right")} style={{ ...resizerCommon, right: 0, top: EDGE, bottom: EDGE, width: EDGE, cursor: "ew-resize" }} />
      <div onPointerDown={onResizerPointerDown("top")} style={{ ...resizerCommon, top: 0, left: EDGE, right: EDGE, height: EDGE, cursor: "ns-resize" }} />
      <div onPointerDown={onResizerPointerDown("bottom")} style={{ ...resizerCommon, bottom: 0, left: EDGE, right: EDGE, height: EDGE, cursor: "ns-resize" }} />
      <div onPointerDown={onResizerPointerDown("top-left")} style={{ ...resizerCommon, top: 0, left: 0, width: EDGE, height: EDGE, cursor: "nwse-resize" }} />
      <div onPointerDown={onResizerPointerDown("top-right")} style={{ ...resizerCommon, top: 0, right: 0, width: EDGE, height: EDGE, cursor: "nesw-resize" }} />
      <div onPointerDown={onResizerPointerDown("bottom-left")} style={{ ...resizerCommon, bottom: 0, left: 0, width: EDGE, height: EDGE, cursor: "nesw-resize" }} />
      <div onPointerDown={onResizerPointerDown("bottom-right")} style={{ ...resizerCommon, bottom: 0, right: 0, width: EDGE, height: EDGE, cursor: "nwse-resize" }} />
    </div>
  );
}
