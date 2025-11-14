import React, { useEffect, useState } from "react";
import { DnaIcon } from "lucide-react";

type Props = {
  promise: Promise<any>;
  onFinish?: (success: boolean) => void;
  onDelayDone?: (success: boolean) => void; // <-- new prop
  keepOpenAfterFinish?: boolean;
  autoCloseDelay?: number;
};

export default function OperatingDialog({
  promise,
  onFinish,
  onDelayDone,
  keepOpenAfterFinish = true,
  autoCloseDelay = 1000,
}: Props) {
  const [status, setStatus] = useState<"pending" | "success" | "error">("pending");
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    let mounted = true;
    setStatus("pending");
    setVisible(true);

    promise
      .then(() => {
        if (!mounted) return;
        setStatus("success");
        onFinish?.(true);
      })
      .catch(() => {
        if (!mounted) return;
        setStatus("error");
        onFinish?.(false);
      });

    return () => {
      mounted = false;
    };
  }, [promise, onFinish]);

  useEffect(() => {
    if (status === "success" || status === "error") {
      // always run the delay effect so caller can be notified via onDelayDone
      const success = status === "success";
      const timer = setTimeout(() => {
        try {
          onDelayDone?.(success);
        } finally {
          if (!keepOpenAfterFinish) setVisible(false);
        }
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [status, keepOpenAfterFinish, autoCloseDelay, onDelayDone]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" aria-hidden="true" />

      <div
        role="dialog"
        aria-modal="true"
        className="relative z-10 w-[min(90%,480px)] rounded-2xl bg-white p-6 shadow-2xl"
      >
        <div className="flex items-center gap-4">
          <div className="shrink-0">
            
            {status === "pending" && (
              <DnaIcon className="h-8 w-8 animate-spin text-indigo-500" />
            )}




            {status === "success" && (
              <div className="h-8 w-8 flex items-center justify-center rounded-full bg-green-100">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 00-1.414-1.414L7 12.172 4.707 9.879a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l9-9z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}

            {status === "error" && (
              <div className="h-8 w-8 flex items-center justify-center rounded-full bg-red-100">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-9V6a1 1 0 112 0v3a1 1 0 11-2 0zm0 4a1 1 0 112 0 1 1 0 11-2 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold">
              {status === "pending" && "Operating"}
              {status === "success" && "Done"}
              {status === "error" && "Error"}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {status === "pending" && "Vui lòng chờ trong khi tác vụ đang được thực hiện..."}
              {status === "success" && "Tác vụ đã hoàn tất thành công."}
              {status === "error" && "Đã xảy ra lỗi khi thực hiện tác vụ."}
            </p>
          </div>
        </div>

        {(status === "success" || status === "error") && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => setVisible(false)}
              className="rounded-md px-4 py-2 text-sm font-medium"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
