/**
 * Selection Store
 * Lưu trữ và chia sẻ thông tin sample và algorithm được chọn giữa các component
 */

import { useEffect, useState } from 'react';
import { Algorithm } from '@/types/algorithm';
import { SampleSummary } from '@/types/sample';

// Singleton store
const listeners = new Set<() => void>();

interface SelectionState {
  selectedSampleId: string | null;
  selectedSample: SampleSummary | null;
  selectedAlgorithmId: string | null;
  selectedAlgorithm: Algorithm | null;
}

let state: SelectionState = {
  selectedSampleId: null,
  selectedSample: null,
  selectedAlgorithmId: null,
  selectedAlgorithm: null,
};

function notify() {
  listeners.forEach((listener) => {
    try {
      listener();
    } catch (e) {
      // ignore
    }
  });
}

export function setSelectedSample(sample: SampleSummary | null) {
  state = {
    ...state,
    selectedSampleId: sample?.id || null,
    selectedSample: sample,
  };
  notify();
}

export function setSelectedAlgorithm(algorithm: Algorithm | null) {
  state = {
    ...state,
    selectedAlgorithmId: algorithm?.id || null,
    selectedAlgorithm: algorithm,
  };
  notify();
}

export function getSelectionState(): SelectionState {
  return { ...state };
}

export function subscribeSelection(callback: () => void) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}

export function useSelectionStore() {
  const [currentState, setCurrentState] = useState<SelectionState>(getSelectionState());

  useEffect(() => {
    const unsubscribe = subscribeSelection(() => {
      setCurrentState(getSelectionState());
    });
    return () => {
      unsubscribe();
    };
  }, []);

  return {
    selectedSampleId: currentState.selectedSampleId,
    selectedSample: currentState.selectedSample,
    selectedAlgorithmId: currentState.selectedAlgorithmId,
    selectedAlgorithm: currentState.selectedAlgorithm,
    setSelectedSample,
    setSelectedAlgorithm,
  };
}
