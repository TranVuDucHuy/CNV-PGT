/**
 * ParamDialog Component
 * Dialog để thêm/sửa từng parameter của algorithm
 */

"use client";

import React, { useState, useEffect } from 'react';
// Legacy local type to avoid coupling; component is currently unused
type AlgorithmParam = {
  name: string;
  type: 'string' | 'integer' | 'float' | 'boolean';
  default_value?: string | number | boolean;
  required: boolean;
  description?: string;
};
import { X } from 'lucide-react';

interface ParamDialogProps {
  open: boolean;
  param?: AlgorithmParam | null;
  onClose: () => void;
  onSave: (param: AlgorithmParam) => void;
}

export default function ParamDialog({ open, param, onClose, onSave }: ParamDialogProps) {
  const [formData, setFormData] = useState<AlgorithmParam>({
    name: '',
    type: 'string',
    default_value: '',
    required: false,
    description: '',
  });

  useEffect(() => {
    if (param) {
      setFormData(param);
    } else {
      setFormData({
        name: '',
        type: 'string',
        default_value: '',
        required: false,
        description: '',
      });
    }
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
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
              onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="string">String</option>
              <option value="integer">Integer</option>
              <option value="float">Float</option>
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
                value={String(formData.default_value)}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  default_value: e.target.value === 'true' 
                })}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">-- None --</option>
                <option value="true">True</option>
                <option value="false">False</option>
              </select>
            ) : (
              <input
                type={formData.type === 'integer' || formData.type === 'float' ? 'number' : 'text'}
                step={formData.type === 'float' ? 'any' : undefined}
                value={String(formData.default_value || '')}
                onChange={(e) => {
                  let value: string | number = e.target.value;
                  if (formData.type === 'integer') {
                    value = parseInt(value) || 0;
                  } else if (formData.type === 'float') {
                    value = parseFloat(value) || 0;
                  }
                  setFormData({ ...formData, default_value: value });
                }}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`e.g., ${formData.type === 'integer' ? '100' : formData.type === 'float' ? '0.5' : 'default_value'}`}
              />
            )}
          </div>

          {/* Required Checkbox */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="required"
              checked={formData.required}
              onChange={(e) => setFormData({ ...formData, required: e.target.checked })}
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label htmlFor="required" className="ml-2 text-sm font-medium">
              Required Parameter
            </label>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Describe this parameter..."
            />
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
