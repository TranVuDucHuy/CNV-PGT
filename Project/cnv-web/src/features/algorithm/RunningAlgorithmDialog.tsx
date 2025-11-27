/**
 * RunningAlgorithmDialog
 * Hiển thị trạng thái đang chạy algorithm
 */

import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  open: boolean;
  sampleName: string;
  algorithmName: string;
  algorithmVersion: string;
  parameters: Record<string, any>;
}

export default function RunningAlgorithmDialog({
  open,
  sampleName,
  algorithmName,
  algorithmVersion,
  parameters,
}: Props) {
  if (!open) return null;

  const paramEntries = Object.entries(parameters || {});

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl m-4">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Loader2 className="animate-spin text-blue-500" size={32} />
            <h3 className="text-xl font-semibold">Running Algorithm</h3>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-sm font-medium text-gray-600">Sample:</span>
              <p className="text-base font-medium">{sampleName}</p>
            </div>

            <div>
              <span className="text-sm font-medium text-gray-600">Algorithm:</span>
              <p className="text-base font-medium">
                {algorithmName} <span className="text-gray-500">v{algorithmVersion}</span>
              </p>
            </div>

            {paramEntries.length > 0 && (
              <div>
                <span className="text-sm font-medium text-gray-600 mb-2 block">Parameters:</span>
                <div className="border rounded overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium">Name</th>
                        <th className="text-left px-3 py-2 font-medium">Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paramEntries.map(([key, paramData]) => {
                        // paramData có thể là {type, default, value} hoặc trực tiếp value
                        const displayValue = typeof paramData === 'object' && paramData !== null && 'value' in paramData
                          ? String(paramData.value ?? paramData.default ?? '')
                          : String(paramData ?? '');
                        
                        return (
                          <tr key={key} className="border-t">
                            <td className="px-3 py-2 font-medium text-gray-700">{key}</td>
                            <td className="px-3 py-2 text-gray-600">{displayValue}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 text-sm text-gray-500 text-center">
            Please wait while the algorithm is running...
          </div>
        </div>
      </div>
    </div>
  );
}
