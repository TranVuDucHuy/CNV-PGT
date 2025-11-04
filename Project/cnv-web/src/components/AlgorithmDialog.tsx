/**
 * AlgorithmDialog Component
 * Dialog để upload thuật toán (.zip) theo backend hiện tại
 */

"use client";

import React, { useState, useEffect } from 'react';
import { X, CheckCircle } from 'lucide-react';
import { algorithmAPI } from '@/services';

interface AlgorithmDialogProps {
  open: boolean;
  algorithm?: null; // Backend chưa hỗ trợ edit; giữ prop để tương thích API
  onClose: () => void;
  onSuccess: () => void;
}

export default function AlgorithmDialog({ open, onClose, onSuccess }: AlgorithmDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [showSuccessAnnouncement, setShowSuccessAnnouncement] = useState(false);

  useEffect(() => {
    if (open) {
      setFile(null);
      setShowSuccessAnnouncement(false);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a .zip file to upload');
      return;
    }
    setLoading(true);
    try {
      await algorithmAPI.upload(file);
      setShowSuccessAnnouncement(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  if (showSuccessAnnouncement) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center max-w-md">
          <CheckCircle size={64} className="text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Uploaded!</h2>
          <p className="text-gray-600 mb-2">Algorithm has been uploaded successfully.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg m-4">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">Upload Algorithm (.zip)</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" disabled={loading}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium mb-1">Select file</label>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-2">
              The zip must contain <code>metadata.json</code> and referenced module files.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-60"
              disabled={loading || !file}
            >
              {loading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
