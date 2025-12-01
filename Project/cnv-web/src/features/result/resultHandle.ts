// resultHandle.ts
import React from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux"; // Import Redux hooks
import { resultAPI } from "@/services";
import { ResultSummary, ResultDto } from "@/types/result";
import { Algorithm } from "@/types/algorithm";
// Import Redux actions và selector
import { setResults, clearSelection } from "@/utils/appSlice";
import { RootState } from "@/utils/store";

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
  removeResults: (ids: string[]) => Promise<void>; // Cập nhật type từ Set<string> thành string[]
  getAll: () => Promise<ResultSummary[]>;
  setAlgo: (al: Algorithm) => void;
  setSelectedResultId: (id: string | null) => void;
  selectedResultIds: string[];
}

// ---------- internal hook ----------
export function useInternalResultHandle(): UseSampleHandleReturn {
  const dispatch = useDispatch();

  // Lấy results từ Redux thay vì useState local
  // Lưu ý: Đảm bảo type Result trong Redux khớp với ResultSummary hoặc ép kiểu
  const results = useSelector(
    (state: RootState) => state.app.results
  ) as unknown as ResultSummary[];
  const selectedResultIds = useSelector(
    (state: RootState) => state.app.selectedResults
  ) as string[];

  // Các state local khác vẫn giữ nguyên (file upload, logic UI tạm thời)
  const [binFile, setBinFile] = useState<File | null>(null);
  const [segmentFile, setSegmentFile] = useState<File | null>(null);
  const [createdAt, setCreatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [algo, setAlgo] = useState<Algorithm | null>(null);
  const [resultDtos, setResultDtos] = useState<ResultDto[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<string | null>(null);

  const fetchDtosFromSummaries = useCallback(
    async (summaries: ResultSummary[]) => {
      const promises = summaries.map(async (s) => {
        const id = s.id;
        if (id === undefined || id === null) return null;
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
    },
    []
  );

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const all = (await resultAPI.getAll()) ?? [];

      // THAY ĐỔI QUAN TRỌNG: Dispatch lên Redux
      dispatch(setResults(all as any[])); // Ép kiểu nếu type Redux chưa khớp hoàn toàn

      const allDtos = await fetchDtosFromSummaries(all as ResultSummary[]);
      setResultDtos(Array.isArray(allDtos) ? [...allDtos] : []);
    } catch (err) {
      console.error("Failed to refresh results", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchDtosFromSummaries, dispatch]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        await refresh();
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load results";
        setError(message);
      } finally {
        setLoading(false);
      }
    })();
  }, [refresh]); // Thêm refresh vào dep

  const save = useCallback(async () => {
    if (!binFile || !segmentFile || !algo) return;

    try {
      await resultAPI.create(
        binFile,
        segmentFile,
        algo.id,
        algo.parameters?.[0].id,
        createdAt || undefined
      );
      await refresh();
    } catch (err) {
      console.error("Failed to upload result file:", err);
      throw err;
    }
  }, [binFile, segmentFile, algo, createdAt, refresh]);

  const removeResults = useCallback(
    async (ids: string[]) => {
      // Nhận mảng string (từ Redux selectedResults)
      try {
        const promises = ids.map(async (id) => {
          if (!id) return;
          try {
            await resultAPI.delete(id);
          } catch (err) {
            console.error("delete failed", id, err);
          }
        });

        await Promise.all(promises);

        // Sau khi xóa xong, clear selection trong Redux và refresh lại list
        dispatch(clearSelection());
        await refresh();
      } catch (err) {
        console.error("Failed to delete samples", err);
        throw err;
      }
    },
    [refresh, dispatch]
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
    const found = resultDtos.find(
      (d) => String(d.id) === String(selectedResultId)
    );
    if (found) return found;
    const idx = results.findIndex(
      (r) => String(r.id) === String(selectedResultId)
    );
    if (idx >= 0 && resultDtos[idx]) return resultDtos[idx];
    return null;
  }, [selectedResultId, resultDtos, results]);

  return {
    results, // Trả về từ Redux selector
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
    selectedResultIds,
  };
}

// ---------- Context + Provider ----------
const ResultContext = React.createContext<UseSampleHandleReturn | undefined>(
  undefined
);

type ResultProviderProps = {
  children?: React.ReactNode;
  store?: UseSampleHandleReturn;
};

export function ResultProvider(props: ResultProviderProps) {
  const internal = useInternalResultHandle();
  const storeToUse = props.store ?? internal;
  return React.createElement(
    ResultContext.Provider,
    { value: storeToUse },
    props.children ?? null
  );
}

export default function useResultHandle(): UseSampleHandleReturn {
  const ctx = React.useContext(ResultContext);
  if (!ctx)
    throw new Error("useResultHandle must be used within a ResultProvider");
  return ctx;
}
