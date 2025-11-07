/**
 * AlgorithmDetail Component
 * Dialog to create/register an Algorithm with metadata and optional ZIP upload.
 */

"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { X, Plus, Trash2, CheckCircle } from 'lucide-react';
import { AlgorithmMetadata, AlgorithmParameterCreateRequest } from '@/types/algorithm';
import ParamDialog from '@/components/ParamDialog';
import { algorithmAPI } from '@/services';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void; // called after successful create (and optional upload)
}

export default function AlgorithmDetail({ open, onClose, onSuccess }: Props) {
  const [name, setName] = useState('');
  const [version, setVersion] = useState('');
  const [description, setDescription] = useState('');
  const [params, setParams] = useState<AlgorithmParameterCreateRequest[]>([]);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [paramDialogOpen, setParamDialogOpen] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [showSuccessAnnouncement, setShowSuccessAnnouncement] = useState(false);

  useEffect(() => {
    if (open) {
      setName('');
      setVersion('');
      setDescription('');
      setParams([]);
      setZipFile(null);
      setLoading(false);
      setEditingIndex(null);
      setShowSuccessAnnouncement(false);
    }
  }, [open]);

  const metadata: AlgorithmMetadata = useMemo(() => ({
    name: name.trim(),
    version: version.trim(),
    description: description.trim() || undefined,
    parameters: params,
  }), [name, version, description, params]);

  const canSubmit = name.trim() && version.trim();

  const handleSaveParam = (param: AlgorithmParameterCreateRequest) => {
    if (editingIndex === null) {
      setParams(prev => [...prev, param]);
    } else {
      setParams(prev => prev.map((p, i) => i === editingIndex ? param : p));
    }
  };

  const handleEditParam = (index: number) => {
    setEditingIndex(index);
    setParamDialogOpen(true);
  };

  const handleDeleteParam = (index: number) => {
    setParams(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      setLoading(true);
      const res = await algorithmAPI.register(metadata);
      if (zipFile) {
        await algorithmAPI.uploadZip(res.algorithm_id, zipFile);
      }
      setShowSuccessAnnouncement(true);
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create algorithm';
      alert(message);
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
          <h2 className="text-2xl font-bold mb-2">Saved!</h2>
          <p className="text-gray-600 mb-2">Algorithm has been registered{zipFile ? ' and uploaded' : ''} successfully.</p>
        </div>
      </div>
    );
  }

  const currentEditingParam = editingIndex !== null ? params[editingIndex] : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl m-4">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">New Algorithm</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" disabled={loading}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name <span className="text-red-500">*</span></label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., MyAlgorithm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Version <span className="text-red-500">*</span></label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., 1.0.0"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Describe the algorithm..."
            />
          </div>

          {/* Parameters */}
          <div className="border rounded p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Algorithm Params</h3>
              <button
                type="button"
                onClick={() => { setEditingIndex(null); setParamDialogOpen(true); }}
                className="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded flex items-center gap-1"
              >
                <Plus size={16} /> Add
              </button>
            </div>

            {params.length === 0 ? (
              <div className="text-sm text-gray-500">No parameters yet.</div>
            ) : (
              <ul className="space-y-2">
                {params.map((p, idx) => (
                  <li key={idx} className="flex items-center justify-between border rounded px-3 py-2 bg-gray-50">
                    <div>
                      <div className="font-medium">{p.name} <span className="text-xs text-gray-500">({p.type})</span></div>
                      <div className="text-xs text-gray-600">default: {String(p.default ?? '')} · value: {String(p.value ?? '')}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button type="button" className="text-blue-600 hover:underline" onClick={() => handleEditParam(idx)}>Edit</button>
                      <button type="button" className="text-red-600 hover:text-red-700" onClick={() => handleDeleteParam(idx)}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Optional ZIP */}
          <div>
            <label className="block text-sm font-medium mb-1">Module ZIP (optional)</label>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setZipFile(e.target.files?.[0] || null)}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">If provided, the ZIP will be uploaded after registering the metadata.</p>
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
              disabled={loading || !canSubmit}
            >
              {loading ? 'Saving...' : 'OK'}
            </button>
          </div>
        </form>
      </div>

      {/* Param Dialog */}
      <ParamDialog
        open={paramDialogOpen}
        param={currentEditingParam}
        onClose={() => setParamDialogOpen(false)}
        onSave={(p) => { handleSaveParam(p); setParamDialogOpen(false); }}
      />
    </div>
  );
}
