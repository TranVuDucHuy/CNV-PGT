// resultHandle.ts
import React from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { resultAPI } from "@/services"; // your provided API wrapper
import { ResultSummary, ResultDto } from "@/types/result";
import { Algorithm } from "@/types/algorithm";

export interface UseSampleHandleReturn {
  results: ResultSummary[];
  binFile: File | null;
  segmentFile: File | null;
  createdAt: string | null;
  loading: boolean;
  error: string | null;
  algo: Algorithm | null;
  resultDtos: ResultDto[];
  selectedResultId: string | null;
  selectedResultDto: ResultDto | null;
  setBinFile: (f: File | null) => void;
  setSegmentFile: (f: File | null) => void;
  setCreatedAt: (date: string | null) => void;
  save: () => Promise<void>;
  refresh: () => Promise<void>;
  removeResults: (ids: Set<string>) => Promise<void>;
  getAll: () => Promise<ResultSummary[]>;
  setAlgo: (al: Algorithm) => void;
  setSelectedResultId: (id: string | null) => void;
}

// ---------- internal hook (uses React hooks) ----------
export function useInternalResultHandle(initial: ResultSummary[] = []): UseSampleHandleReturn {
  const [results, setResults] = useState<ResultSummary[]>(initial);
  const [binFile, setBinFile] = useState<File | null>(null);
  const [segmentFile, setSegmentFile] = useState<File | null>(null);
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [algo, setAlgo] = useState<Algorithm | null>(null);
  const [resultDtos, setResultDtos] = useState<ResultDto[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);

  const fetchDtosFromSummaries = useCallback(async (summaries: ResultSummary[]) => {
    const promises = summaries.map(async (s) => {
      const id = s.id;
      if (id === undefined || id === null) {
        console.warn("skip invalid id", id);
        return null;
      }
      try {
        const dto = await resultAPI.getById(String(id));
        return dto as ResultDto;
      } catch (err) {
        console.error("Failed to fetch dto for id", id, err);
        return null;
      }
    });

    const maybeDtos = await Promise.all(promises);
    return maybeDtos.filter((d): d is ResultDto => d !== null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const all = (await resultAPI.getAll()) ?? [];
      setResults(all as ResultSummary[]);

      const allDtos = await fetchDtosFromSummaries(all as ResultSummary[]);
      setResultDtos(Array.isArray(allDtos) ? [...allDtos] : []);
    } catch (err) {
      console.error("Failed to refresh results", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchDtosFromSummaries]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load results";
        setError(message);
        console.error("Failed initial load:", err);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const save = useCallback(async () => {
    if (!binFile || !segmentFile || !algo) return;

    try {
      await resultAPI.create(binFile, segmentFile, algo.id, algo.parameters?.[0].id, createdAt || undefined);
      await refresh();
    } catch (err) {
      console.error("Failed to upload result file:", err);
      throw err;
    }
  }, [binFile, segmentFile, algo, createdAt, refresh]);

  const removeResults = useCallback(
    async (ids: Set<string>) => {
      try {
        const promises = Array.from(ids).map(async (id) => {
          if (!id) {
            console.warn("skip invalid id", id);
            return;
          }
          try {
            await resultAPI.delete(id);
            ids.delete(id);
          } catch (err) {
            console.error("delete failed", id, err);
          }
        });

        await Promise.all(promises);
        await refresh();
      } catch (err) {
        console.error("Failed to delete samples", err);
        throw err;
      }
    },
    [refresh]
  );

  const getAll = useCallback(async () => {
    try {
      const resultSummaries = await resultAPI.getAll();
      return resultSummaries ?? [];
    } catch (err) {
      console.error("Failed to load all samples");
      throw err;
    }
  }, []);

  const selectedResultDto = useMemo(() => {
    if (!selectedResultId) return null;
    const found = resultDtos.find((d) => String(d.id) === String(selectedResultId));
    if (found) return found;
    const idx = results.findIndex((r) => String(r.id) === String(selectedResultId));
    if (idx >= 0 && resultDtos[idx]) return resultDtos[idx];
    return null;
  }, [selectedResultId, resultDtos, results]);

  return {
    results,
    binFile,
    segmentFile,
    createdAt,
    loading,
    error,
    algo,
    resultDtos,
    selectedResultId,
    selectedResultDto,
    setBinFile,
    setSegmentFile,
    setCreatedAt,
    save,
    refresh,
    removeResults,
    getAll,
    setAlgo,
    setSelectedResultId,
  };
}

// ---------- Context + Provider (keeps file as .ts by using React.createElement) ----------
const ResultContext = React.createContext<UseSampleHandleReturn | undefined>(undefined);

type ResultProviderProps = {
  children?: React.ReactNode;
  /** optional prebuilt store (mostly for tests) */
  store?: UseSampleHandleReturn;
};

export function ResultProvider(props: ResultProviderProps) {
  // call the internal hook (must be called unconditionally inside component)
  const internal = useInternalResultHandle();
  const storeToUse = props.store ?? internal;

  // return Provider via React.createElement so file can be .ts (no JSX)
  return React.createElement(ResultContext.Provider, { value: storeToUse }, props.children ?? null);
}

// consumer hook (use this in components)
export default function useResultHandle(): UseSampleHandleReturn {
  const ctx = React.useContext(ResultContext);
  if (!ctx) throw new Error("useResultHandle must be used within a ResultProvider");
  return ctx;
}
