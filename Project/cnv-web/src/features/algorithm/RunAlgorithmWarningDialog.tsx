/**
 * RunAlgorithmWarningDialog
 * Hiển thị cảnh báo khi algorithm chưa đủ điều kiện chạy
 */

import React from 'react';
import { X, AlertCircle } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
  referencesRequired: number;
  onUploadModule?: () => void;
}

export default function RunAlgorithmWarningDialog({ open, onClose, referencesRequired, onUploadModule }: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md m-4">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <AlertCircle className="text-orange-500" size={24} />
            Cannot Run Algorithm
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={20} />
          </button>
        </div>

        <div className="p-6">
          <p className="text-gray-700 mb-4">
            Algorithm requires uploaded module and {referencesRequired} reference{referencesRequired !== 1 ? 's' : ''} sample to run.
          </p>
          <p className="text-sm text-gray-600">
            Please ensure:
          </p>
          <ul className="list-disc list-inside text-sm text-gray-600 mt-2 space-y-1">
            <li>Algorithm module (ZIP file) has been uploaded</li>
            <li>At least {referencesRequired} reference sample{referencesRequired !== 1 ? 's are' : ' is'} selected in the Reference pane</li>
          </ul>
        </div>

        <div className="flex justify-end gap-2 p-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Close
          </button>
          {onUploadModule && (
            <button
              onClick={() => {
                onUploadModule();
                onClose();
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Upload Module
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
