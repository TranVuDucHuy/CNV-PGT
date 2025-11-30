// components/CenterDialog.tsx
"use client";
import React, { ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

export type CenterDialogProps = {
  open: boolean;
  title?: ReactNode;
  children?: ReactNode;
  onClose?: () => void;
  onConfirm?: () => void;
  confirmLabel?: string;
  cancelLabel?: string;
  showFooter?: boolean;
  confirmDisabled?: boolean;
  className?: string;
  disableBackdropClose?: boolean;
};

export default function CenterDialog({
  open,
  title,
  children,
  onClose,
  onConfirm,
  confirmLabel = "OK",
  cancelLabel = "Cancel",
  showFooter = true,
  confirmDisabled = false,
  className = "",
  disableBackdropClose = false,
}: CenterDialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  const node = (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-9999 flex items-center justify-center"
    >
      <div
        className="absolute inset-0 bg-black/40"
        onMouseDown={(e) => {
          if (!disableBackdropClose) onClose?.();
        }}
      />

      <div
        onMouseDown={(e) => e.stopPropagation()}
        className={`relative w-full max-w-md mx-4 bg-white rounded-lg shadow-2xl p-6 ${className}`}
      >
        <div className="flex items-start justify-between mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button
            type="button"
            aria-label="Close dialog"
            onClick={() => onClose?.()}
            className="p-1 rounded hover:bg-gray-100"
          >
            ✕
          </button>
        </div>

        <div className="mb-4">{children}</div>

        {showFooter && (
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => onClose?.()}
              className="px-3 py-2 rounded border hover:bg-gray-50"
            >
              {cancelLabel}
            </button>
            <button
              type="button"
              onClick={() => onConfirm?.()}
              disabled={confirmDisabled}
              className={`px-3 py-2 rounded bg-green-600 text-white hover:bg-green-700 ${
                confirmDisabled ? "opacity-60 cursor-not-allowed" : ""
              }`}
            >
              {confirmLabel}
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(node, document.body);
}
