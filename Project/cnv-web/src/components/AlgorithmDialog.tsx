/**
 * AlgorithmDialog Component
 * Dialog chính để Add/Edit Algorithm với đầy đủ workflow
 */

"use client";

import React, { useState, useEffect } from 'react';
import { Algorithm, AlgorithmParam } from '@/types/algorithm';
import { algorithmAPI } from '@/services';
import ParamDialog from './ParamDialog';
import { X, Plus, Edit3, Trash2, FolderOpen, CheckCircle, AlertCircle } from 'lucide-react';

interface AlgorithmDialogProps {
  open: boolean;
  algorithm?: Algorithm | null;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AlgorithmDialog({ 
  open, 
  algorithm, 
  onClose, 
  onSuccess 
}: AlgorithmDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    module_path: '',
    parameters: [] as AlgorithmParam[],
  });

  const [paramDialogOpen, setParamDialogOpen] = useState(false);
  const [editingParam, setEditingParam] = useState<AlgorithmParam | null>(null);
  const [editingParamIndex, setEditingParamIndex] = useState<number | null>(null);
  
  const [validationStatus, setValidationStatus] = useState<{
    validated: boolean;
    isValid: boolean;
    message: string;
  }>({
    validated: false,
    isValid: false,
    message: '',
  });

  const [loading, setLoading] = useState(false);
  const [showSuccessAnnouncement, setShowSuccessAnnouncement] = useState(false);

  // Reset form khi mở/đóng dialog
  useEffect(() => {
    if (open) {
      if (algorithm) {
        setFormData({
          name: algorithm.name,
          description: algorithm.description || '',
          module_path: algorithm.module_path || '',
          parameters: algorithm.parameters || [],
        });
        setValidationStatus({
          validated: !!algorithm.module_path,
          isValid: algorithm.is_usable,
          message: algorithm.is_usable ? 'Module is valid' : 'Module path not validated',
        });
      } else {
        setFormData({
          name: '',
          description: '',
          module_path: '',
          parameters: [],
        });
        setValidationStatus({
          validated: false,
          isValid: false,
          message: '',
        });
      }
      setShowSuccessAnnouncement(false);
    }
  }, [open, algorithm]);

  // Handle Add/Edit Parameter
  const handleSaveParam = (param: AlgorithmParam) => {
    if (editingParamIndex !== null) {
      // Edit existing param
      const newParams = [...formData.parameters];
      newParams[editingParamIndex] = param;
      setFormData({ ...formData, parameters: newParams });
    } else {
      // Add new param
      setFormData({
        ...formData,
        parameters: [...formData.parameters, param],
      });
    }
    setEditingParam(null);
    setEditingParamIndex(null);
  };

  // Handle Edit Parameter
  const handleEditParam = (index: number) => {
    setEditingParam(formData.parameters[index]);
    setEditingParamIndex(index);
    setParamDialogOpen(true);
  };

  // Handle Delete Parameter
  const handleDeleteParam = (index: number) => {
    if (confirm('Are you sure you want to delete this parameter?')) {
      const newParams = formData.parameters.filter((_, i) => i !== index);
      setFormData({ ...formData, parameters: newParams });
    }
  };

  // Handle Validate Module Path
  const handleValidateModule = async () => {
    if (!formData.module_path.trim()) {
      alert('Please enter a module path first!');
      return;
    }

    setLoading(true);
    try {
      const result = await algorithmAPI.validateModule(formData.module_path);
      setValidationStatus({
        validated: true,
        isValid: result.valid,
        message: result.message,
      });
    } catch (error) {
      setValidationStatus({
        validated: true,
        isValid: false,
        message: error instanceof Error ? error.message : 'Validation failed',
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle Browse Module Path (Giả lập - trong thực tế cần file picker)
  const handleBrowseModule = () => {
    const path = prompt('Enter module path:', formData.module_path);
    if (path !== null) {
      setFormData({ ...formData, module_path: path });
      setValidationStatus({ validated: false, isValid: false, message: '' });
    }
  };

  // Handle Submit
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.name.trim()) {
      alert('Algorithm name is required!');
      return;
    }

    // Warning nếu chưa validate module
    if (formData.module_path && !validationStatus.validated) {
      if (!confirm('Module path has not been validated. Continue anyway?')) {
        return;
      }
    }

    setLoading(true);
    try {
      if (algorithm?.id) {
        // Update existing algorithm
        await algorithmAPI.update(algorithm.id, formData);
      } else {
        // Create new algorithm
        await algorithmAPI.create(formData);
      }

      // Show success announcement
      setShowSuccessAnnouncement(true);
      
      // Auto close after 2 seconds
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 2000);

    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to save algorithm');
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  // Success Announcement Overlay
  if (showSuccessAnnouncement) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center max-w-md">
          <CheckCircle size={64} className="text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">Success!</h2>
          <p className="text-gray-600 mb-2">
            Algorithm "{formData.name}" has been saved successfully.
          </p>
          {validationStatus.isValid && (
            <div className="flex items-center justify-center gap-2 text-green-600 font-medium">
              <CheckCircle size={20} />
              <span>Marked as Usable ✓</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl m-4 max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
            <h2 className="text-2xl font-bold">
              {algorithm ? 'Edit Algorithm' : 'Add Algorithm'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
              disabled={loading}
            >
              <X size={24} />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Algorithm Name */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Algorithm Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., WisecondorX"
                required
              />
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
                placeholder="Describe what this algorithm does..."
              />
            </div>

            {/* Module Path */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Module Path (Optional)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formData.module_path}
                  onChange={(e) => {
                    setFormData({ ...formData, module_path: e.target.value });
                    setValidationStatus({ validated: false, isValid: false, message: '' });
                  }}
                  className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="/path/to/algorithm/module.py"
                />
                <button
                  type="button"
                  onClick={handleBrowseModule}
                  className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 flex items-center gap-2"
                  title="Browse"
                >
                  <FolderOpen size={20} />
                </button>
                <button
                  type="button"
                  onClick={handleValidateModule}
                  disabled={!formData.module_path || loading}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Validate
                </button>
              </div>
              
              {/* Validation Status */}
              {validationStatus.validated && (
                <div className={`mt-2 flex items-center gap-2 text-sm ${
                  validationStatus.isValid ? 'text-green-600' : 'text-red-600'
                }`}>
                  {validationStatus.isValid ? (
                    <CheckCircle size={16} />
                  ) : (
                    <AlertCircle size={16} />
                  )}
                  <span>{validationStatus.message}</span>
                </div>
              )}
            </div>

            {/* Parameters Section */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm font-medium">
                  Algorithm Parameters
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setEditingParam(null);
                    setEditingParamIndex(null);
                    setParamDialogOpen(true);
                  }}
                  className="flex items-center gap-1 px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  <Plus size={16} />
                  Add Param
                </button>
              </div>

              {/* Parameters List */}
              {formData.parameters.length === 0 ? (
                <div className="border border-dashed border-gray-300 rounded p-4 text-center text-gray-500">
                  No parameters added yet. Click "Add Param" to add one.
                </div>
              ) : (
                <div className="border border-gray-300 rounded divide-y">
                  {formData.parameters.map((param, index) => (
                    <div
                      key={index}
                      className="p-3 hover:bg-gray-50 flex items-start justify-between"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{param.name}</span>
                          <span className="text-xs bg-gray-200 px-2 py-1 rounded">
                            {param.type}
                          </span>
                          {param.required && (
                            <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                              Required
                            </span>
                          )}
                        </div>
                        {param.default_value !== undefined && param.default_value !== '' && (
                          <div className="text-sm text-gray-600 mt-1">
                            Default: {String(param.default_value)}
                          </div>
                        )}
                        {param.description && (
                          <div className="text-sm text-gray-500 mt-1">
                            {param.description}
                          </div>
                        )}
                      </div>
                      <div className="flex gap-1 ml-2">
                        <button
                          type="button"
                          onClick={() => handleEditParam(index)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Edit3 size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteParam(index)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end gap-2 pt-4 border-t">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="px-6 py-2 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : algorithm ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Param Dialog */}
      <ParamDialog
        open={paramDialogOpen}
        param={editingParam}
        onClose={() => {
          setParamDialogOpen(false);
          setEditingParam(null);
          setEditingParamIndex(null);
        }}
        onSave={handleSaveParam}
      />
    </>
  );
}
