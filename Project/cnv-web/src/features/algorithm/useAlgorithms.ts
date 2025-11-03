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

  const addAlgorithm = async (data: any) => {
    try {
      const newAlgorithm = await algorithmAPI.create(data);
      setAlgorithms([...algorithms, newAlgorithm]);
      return newAlgorithm;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create algorithm';
      throw new Error(message);
    }
  };

  const updateAlgorithm = async (id: number, data: any) => {
    try {
      const updated = await algorithmAPI.update(id, data);
      setAlgorithms(algorithms.map(a => a.id === id ? updated : a));
      return updated;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update algorithm';
      throw new Error(message);
    }
  };

  const deleteAlgorithm = async (id: number) => {
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

  return {
    algorithms,
    loading,
    error,
    loadAlgorithms,
    addAlgorithm,
    updateAlgorithm,
    deleteAlgorithm,
  };
}
