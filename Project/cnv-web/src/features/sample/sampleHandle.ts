import { useCallback, useState } from "react";
import { Sample } from "@/services"; // adjust path if needed
import { sampleAPI } from "@/services"; // your provided API wrapper

export interface UseSampleHandleReturn {
  samples: Sample[];
  isOpen: boolean;
  file: File | null;
  open: () => void;
  close: () => void;
  setFile: (f: File | null) => void;
  save: () => Promise<void>;
  refresh: () => Promise<void>;
  removeLast: () => Promise<void>;
}

export default function useSampleHandle(initial: Sample[] = []): UseSampleHandleReturn {
  const [samples, setSamples] = useState<Sample[]>(initial);
  const [isOpen, setIsOpen] = useState(false);
  const [file, setFileState] = useState<File | null>(null);

  const open = useCallback(() => {
    setFileState(null);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => setIsOpen(false), []);

  const setFile = useCallback((f: File | null) => setFileState(f), []);

  const refresh = useCallback(async () => {
    try {
      const all = await sampleAPI.getAll();
      setSamples(all as Sample[]);
    } catch (err) {
      console.error("Failed to refresh samples", err);
    }
  }, []);

  const save = useCallback(async () => {
    if (!file) return;

    try {
      await sampleAPI.create(file); // chỉ gọi API create với file
      await refresh();
      setIsOpen(false);
    } catch (err) {
      console.error("Failed to upload sample file:", err);
      throw err;
    }
  }, [file, refresh]);

  const removeLast = useCallback(async () => {
    if (!samples.length) return;
    const last = samples[samples.length - 1];
    try {
      await sampleAPI.delete(Number(last.id)); // nếu id là string, không cần Number
      await refresh();
    } catch (err) {
      console.error("Failed to delete last sample", err);
    }
  }, [samples, refresh]);

  return {
    samples,
    isOpen,
    file,
    open,
    close,
    setFile,
    save,
    refresh,
    removeLast,
  };
}
