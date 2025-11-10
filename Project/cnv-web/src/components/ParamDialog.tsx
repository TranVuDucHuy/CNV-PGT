/**
 * ParamDialog Component
 * Dialog để thêm/sửa từng parameter của algorithm theo backend (name, type, default, value)
 */

"use client";

import React, { useState, useEffect } from 'react';
import { AlgorithmParameterCreateRequest } from '@/types/algorithm';
import { X } from 'lucide-react';

interface ParamDialogProps {
  open: boolean;
  param?: AlgorithmParameterCreateRequest | null;
  onClose: () => void;
  onSave: (param: AlgorithmParameterCreateRequest) => void;
}

export default function ParamDialog({ open, param, onClose, onSave }: ParamDialogProps) {
  const [formData, setFormData] = useState<AlgorithmParameterCreateRequest>({
    name: '',
    type: 'string',
    default: '',
    value: ''
  });

  useEffect(() => {
    if (param) setFormData(param);
    else setFormData({ name: '', type: 'string', default: '', value: '' });
  }, [param, open]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      alert('Parameter name is required!');
      return;
    }

    onSave(formData);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">
            {param ? 'Edit Parameter' : 'Add Parameter'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Parameter Name */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Parameter Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., window_size"
              required
            />
          </div>

          {/* Parameter Type */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Type <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="string">String</option>
              <option value="number">Number</option>
              <option value="boolean">Boolean</option>
            </select>
          </div>

          {/* Default Value */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Default Value
            </label>
            {formData.type === 'boolean' ? (
              <select
                value={String(formData.default)}
                onChange={(e) => setFormData({ ...formData, default: e.target.value === 'true' })}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- None --</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            ) : (
              <input
                type={formData.type === 'number' ? 'number' : 'text'}
                step={formData.type === 'number' ? 'any' : undefined}
                value={String(formData.default ?? '')}
                onChange={(e) => {
                  const v = e.target.value;
                  let value: any = v;
                  if (formData.type === 'number') {
                    value = v === '' ? '' : Number(v);
                  }
                  setFormData({ ...formData, default: value });
                }}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={formData.type === 'number' ? 'e.g., 0.5' : 'default value'}
              />
            )}
          </div>

          {/* Runtime Value */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Current Value
            </label>
            {formData.type === 'boolean' ? (
              <select
                value={String(formData.value)}
                onChange={(e) => setFormData({ ...formData, value: e.target.value === 'true' })}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- None --</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            ) : (
              <input
                type={formData.type === 'number' ? 'number' : 'text'}
                step={formData.type === 'number' ? 'any' : undefined}
                value={String(formData.value ?? '')}
                onChange={(e) => {
                  const v = e.target.value;
                  let value: any = v;
                  if (formData.type === 'number') {
                    value = v === '' ? '' : Number(v);
                  }
                  setFormData({ ...formData, value });
                }}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={formData.type === 'number' ? 'e.g., 0.5' : 'value'}
              />
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              {param ? 'Update' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
