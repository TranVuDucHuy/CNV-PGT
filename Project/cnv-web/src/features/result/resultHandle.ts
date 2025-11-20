import { useCallback, useEffect, useState } from "react";
import { resultAPI } from "@/services"; // your provided API wrapper
import { ResultSummary, ResultDto, ReferenceGenome } from "@/types/result";
import { Algorithm } from '@/types/algorithm';

export interface UseSampleHandleReturn {
  results: ResultSummary[];
  binFile: File | null;
  segmentFile: File | null;
  loading: boolean;
  error: string | null;
  algo: Algorithm | null;
  resultDtos: ResultDto[];
  setBinFile: (f: File | null) => void;
  setSegmentFile: (f: File | null) => void;
  save: () => Promise<void>;
  refresh: () => Promise<void>;
  removeResults: (ids: Set<string>) => Promise<void>;
  getAll: () => Promise<ResultSummary[]>;
  setAlgo: (al: Algorithm) => void;
}

export default function useResultHandle(initial: ResultSummary[] = []): UseSampleHandleReturn {
  const [results, setResults] = useState<ResultSummary[]>(initial);
  const [binFile, setBinFile] = useState<File | null>(null);
  const [segmentFile, setSegmentFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [algo, setAlgo] = useState<Algorithm | null>(null);
  const [resultDtos, setResultDtos] = useState<ResultDto[]>([]);

  useEffect(() => {
    // await refresh and properly handle loading
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await refresh();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to load algorithms";
        setError(message);
        console.error("Failed initial load:", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []); // run once

  const fetchDtosFromSummaries = useCallback(async (summaries: ResultSummary[]) => {
    // map over the passed-in summaries (avoid relying on state)
    const promises = summaries.map(async (s) => {
      const id = s.id;
      if (id === undefined || id === null) {
        console.warn("skip invalid id", id);
        return null;
      }
      // ensure numeric check if needed, or just call by string id
      // if (isNaN(Number(id))) {
      //   // if id must be numeric, skip or handle otherwise
      //   console.warn("skip non-numeric id", id);
      //   return null;
      // }
      try {
        const dto = await resultAPI.getById(String(id));
        return dto as ResultDto;
      } catch (err) {
        console.error("Failed to fetch dto for id", id, err);
        return null;
      }
    });

    const maybeDtos = await Promise.all(promises);
    // filter out nulls
    return maybeDtos.filter((d): d is ResultDto => d !== null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const all = (await resultAPI.getAll()) ?? [];
      setResults(all as ResultSummary[]);

      // generate DTOs based on the freshly-fetched `all` variable
      const allDtos = await fetchDtosFromSummaries(all as ResultSummary[]);
      setResultDtos(allDtos);
      //return all;
    } catch (err) {
      console.error("Failed to refresh results", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchDtosFromSummaries]);

  const save = useCallback(async () => {
    if (!binFile || !segmentFile || !algo) return;

    try {
      await resultAPI.create(binFile, segmentFile, algo.id, algo.parameters?.[0].id);
      await refresh();
    } catch (err) {
      console.error("Failed to upload result file:", err);
      throw err;
    }
  }, [binFile, segmentFile, algo, refresh]);

  const removeResults = useCallback(async (ids: Set<string>) => {
    try {
      console.log("start removing");
      const promises = Array.from(ids).map(async (id) => {
        if (!id || isNaN(Number(id))) {
          console.warn("skip invalid id", id);
          return;
        }
        try {
          await resultAPI.delete(id);
          console.log("deleted", id);
          ids.delete(id);
          refresh()
        } catch (err) {
          console.error("delete failed", id, err);
        }
      });

      await Promise.all(promises);
      console.log("all removed");
      await refresh();
    } catch (err) {
      console.error("Failed to delete samples", err);
      throw err;
    }
  }, [refresh]);

  const getAll = useCallback(async () => {
    try {
      const resultSummaries = await resultAPI.getAll();
      return resultSummaries ?? [];
    } catch (err) {
      console.error("Failed to load all samples");
      throw err;
    }
  }, []);

  return {
    results,
    binFile,
    segmentFile,
    loading,
    error,
    algo,
    resultDtos,
    setBinFile,
    setSegmentFile,
    save,
    refresh,
    removeResults,
    getAll,
    setAlgo,
  };
}
