"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { resultAPI } from "@/services/result.api";
import { ResultSummary } from "@/types/result";
import ReportLayout from "./ReportLayout";

interface ReportPageLayoutProps {
  children: React.ReactNode;
}

const ReportPageLayout: React.FC<ReportPageLayoutProps> = ({ children }) => {
  const { id } = useParams();

  const [results, setResults] = useState<ResultSummary[]>([]);
  const [selectedResultId, setSelectedResultId] = useState<
    string | undefined
  >();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

  useEffect(() => {
    setSelectedResultId(id as string | undefined);
    const fetchResults = async () => {
      console.log("Fetching results...");
      try {
        setLoading(true);
        setError(null);
        const data = await resultAPI.getAll();
        if (data) {
          setResults(data);
        }
      } catch (err: any) {
        setError(err.message || "Failed to fetch results");
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, []);

  const handleResultClick = (id: string) => {
    setSelectedResultId(id);
    router.push(`/result/${id}`);
  };

  return (
    <ReportLayout
      results={results}
      loading={loading}
      error={error}
      onResultClick={handleResultClick}
      rightPannel={children}
      selectedResultId={selectedResultId}
    />
  );
};

export default ReportPageLayout;
