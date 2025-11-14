import { useCallback, useEffect, useState } from "react";
import { Sample } from "@/services"; // adjust path if needed
import { SampleSummary } from "@/types/sample";
import { sampleAPI } from "@/services"; // your provided API wrapper

export interface UseSampleHandleReturn {
  samples: SampleSummary[];
  isOpen: boolean;
  files: File[] | null;
  loading: boolean;
  error: string | null;
  open: () => void;
  close: () => void;
  setFile: (f: File[] | null) => void;
  save: () => Promise<void>;
  saveManyFiles: () => Promise<void>;
  refresh: () => Promise<void>;
  removeSamples: (ids: Set<string>) => Promise<void>;
  getAll: () => Promise<SampleSummary[]>
}

export default function useSampleHandle(initial: Sample[] = []): UseSampleHandleReturn {
  const [samples, setSamples] = useState<SampleSummary[]>(initial);
  const [isOpen, setIsOpen] = useState(false);
  const [files, setFileState] = useState<File[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const open = useCallback(() => {
    setFileState(null);
    setIsOpen(true);
  }, []);

  useEffect(() => {
    loadSampleSummaries();
  }, []);

  const loadSampleSummaries = async () => {
    try {
      setLoading(true);
      setError(null);
      refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load algorithms';
      setError(message);
      console.error('Failed to load algorithms:', err);
    } finally {
      setLoading(false);
    }
  };

  const close = useCallback(() => setIsOpen(false), []);

  const setFile = useCallback((f: File[] | null) => {
    console.log(f);
    setFileState(f);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const all = await sampleAPI.getAll();
      setSamples(all as SampleSummary[]);
    } catch (err) {
      console.error("Failed to refresh samples", err);
    }
  }, []);

  const save = useCallback(async () => {
    if (!files || files.length != 1) return;

    try {
      setIsOpen(false);
      await sampleAPI.create(files[0]); // chỉ gọi API create với file
      await refresh();
      
    } catch (err) {
      console.error("Failed to upload sample file:", err);
      throw err;
    } finally {
    }
  }, [files, refresh]);

  const saveManyFiles = useCallback(async () => {
    console.log(files);
    if (!files || files.length < 2) return;

    try {
      setIsOpen(false);
      console.log("start saving");
      await sampleAPI.createMany(files)
      await refresh();
      
    } catch (err) {
      console.error("Failed to upload sample file:", err);
      throw err;
    } finally {
    }
  }, [files]);

  const removeSamples = useCallback(async (ids: Set<string>) => {
    try {
      console.log("start removing");
      const promises = Array.from(ids).map(async (id) => {
      
        if (Number.isNaN(id)) {
          console.warn("skip invalid id", id);
          return;
        }

        try {
          await sampleAPI.delete(id);
          console.log("deleted", id);
          ids.delete(id); // ✅ xóa phần tử khỏi Set ngay khi thành công
        } catch (err) {
          console.error("delete failed", id, err);
        }
      });

      await Promise.all(promises); // chờ tất cả xóa xong
      console.log("all removed");
      await refresh();
    } catch (err) {
      console.error("Failed to delete samples", err);
    } finally {
    }
  }, [samples, refresh]);

  const getAll = useCallback(async () => {
    try {
      const sampleSummaries = await sampleAPI.getAll();
      return sampleSummaries ?? [];
    } catch (err) {
      console.error("Failed to load all samples");
      throw err;
    }
  }, []);

  return {
    samples,
    isOpen,
    files,
    loading,
    error,
    open,
    close,
    setFile,
    save,
    saveManyFiles,
    refresh,
    removeSamples,
    getAll
  };
}
