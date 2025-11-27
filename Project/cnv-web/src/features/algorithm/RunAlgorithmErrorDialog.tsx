/**
 * RunAlgorithmErrorDialog
 * Hiển thị lỗi khi chạy algorithm thất bại
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface Props {
  open: boolean;
  errorMessage: string;
  onClose: () => void;
  onRetry: () => void;
}

export default function RunAlgorithmErrorDialog({ open, errorMessage, onClose, onRetry }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md m-4 p-6">
        <div className="flex items-center gap-3 mb-4">
          <AlertCircle className="text-red-500" size={32} />
          <h3 className="text-lg font-semibold text-red-600">Error Running Algorithm</h3>
        </div>
        
        <p className="text-gray-700 mb-4 whitespace-pre-wrap">{errorMessage}</p>
        
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            Close
          </button>
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    </div>
  );
}
