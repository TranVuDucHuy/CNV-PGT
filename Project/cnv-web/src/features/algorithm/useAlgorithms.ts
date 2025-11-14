/**
 * Custom Hook: useAlgorithms
 * Quản lý tất cả logic liên quan đến algorithms
 */

import { useState, useEffect } from 'react';
import { algorithmAPI } from '@/services';
import { Algorithm } from '@/types/algorithm';

export function useAlgorithms() {
  const [algorithms, setAlgorithms] = useState<Algorithm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastParameterIds, setLastParameterIds] = useState<Record<string, string>>({});
  const [lastValues, setLastValues] = useState<Record<string, Record<string, any>>>({});

  // Load algorithms khi hook được khởi tạo
  useEffect(() => {
    loadAlgorithms();
  }, []);

  const loadAlgorithms = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await algorithmAPI.getAll();
      setAlgorithms(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load algorithms';
      setError(message);
      console.error('Failed to load algorithms:', err);
    } finally {
      setLoading(false);
    }
  };

  // Backend hiện tại không hỗ trợ update algorithm, bỏ qua

  const deleteAlgorithm = async (id: string) => {
    if (!confirm('Are you sure you want to delete this algorithm?')) {
      return false;
    }
    
    try {
      await algorithmAPI.delete(id);
      setAlgorithms(algorithms.filter(a => a.id !== id));
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete algorithm';
      alert(message);
      return false;
    }
  };

  const recordParameterId = (algorithmId: string, parameterId: string) => {
    setLastParameterIds(prev => ({ ...prev, [algorithmId]: parameterId }));
  };

  const recordLastValues = (algorithmId: string, values: Record<string, any>) => {
    setLastValues(prev => ({ ...prev, [algorithmId]: values }));
  };

  return {
    algorithms,
    loading,
    error,
    loadAlgorithms,
    deleteAlgorithm,
    lastParameterIds,
    lastValues,
    recordParameterId,
    recordLastValues,
  };
}
