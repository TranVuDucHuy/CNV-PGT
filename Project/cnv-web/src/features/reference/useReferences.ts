/**
 * Custom Hook: useReferences
 * Quản lý state của reference samples (local state)
 */

import { useEffect, useState } from 'react';

// Singleton store for reference IDs with subscription support
const listeners = new Set<() => void>();
let referenceIdsInternal = new Set<string>();

// Khởi tạo từ localStorage nếu có (để persist qua reload)
if (typeof window !== 'undefined') {
  const stored = localStorage.getItem('referenceIds');
  if (stored) {
    try {
      referenceIdsInternal = new Set(JSON.parse(stored));
    } catch (e) {
      console.warn('[Reference] Failed to load from localStorage:', e);
    }
  }
}

function notify() {
  listeners.forEach((l) => {
    try {
      l();
    } catch (e) {
      // ignore listener errors
    }
  });
  // Persist to localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('referenceIds', JSON.stringify(Array.from(referenceIdsInternal)));
  }
}

export function addReferences(ids: Set<string>) {
  let changed = false;
  const addedIds: string[] = [];
  ids.forEach((id) => {
    if (!referenceIdsInternal.has(id)) {
      referenceIdsInternal.add(id);
      changed = true;
      addedIds.push(id);
    }
  });
  if (changed) {
    console.log('[Reference] Added samples with IDs:', addedIds);
    notify();
  }
}

export function removeReferences(ids: Set<string>) {
  let changed = false;
  ids.forEach((id) => {
    if (referenceIdsInternal.has(id)) {
      referenceIdsInternal.delete(id);
      changed = true;
    }
  });
  if (changed) notify();
}

export function syncWithSamples(availableSampleIds: Set<string>) {
  const next = new Set<string>();
  referenceIdsInternal.forEach((id) => {
    if (availableSampleIds.has(id)) next.add(id);
  });
  const eq = next.size === referenceIdsInternal.size && Array.from(next).every((v) => referenceIdsInternal.has(v));
  if (!eq) {
    referenceIdsInternal = next;
    notify();
  }
}

export function getReferenceIds(): Set<string> {
  return new Set(referenceIdsInternal);
}

export function subscribeReferences(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function useReferencesStore() {
  const [tick, setTick] = useState(0);
  
  useEffect(() => {
    const cb = () => setTick((t) => t + 1);
    const unsub = subscribeReferences(cb);
    return () => {
      unsub();
    };
  }, []);
  
  return {
    referenceIds: getReferenceIds(),
    addReferences,
    removeReferences,
    syncWithSamples,
  };
}
