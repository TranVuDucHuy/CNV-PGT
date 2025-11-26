/**
 * AlgorithmDetail Component
 * Dialog to create/register an Algorithm with metadata and optional ZIP upload.
 */

"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { X, Plus, Minus, CheckCircle, AlertCircle } from 'lucide-react';
import { Algorithm, AlgorithmMetadata, AlgorithmParameterCreateRequest } from '@/types/algorithm';
import { algorithmAPI } from '@/services';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  mode?: 'create' | 'edit';
  initialAlgorithm?: Algorithm;
  onSaveValues?: (values: Record<string, any>) => void;
}

export default function AlgorithmDetail({ open, onClose, onSuccess, mode = 'create', initialAlgorithm, onSaveValues }: Props) {
  const [name, setName] = useState('');
  const [version, setVersion] = useState('');
  const [description, setDescription] = useState('');
  const [referencesRequired, setReferencesRequired] = useState<number>(0);
  const [params, setParams] = useState<AlgorithmParameterCreateRequest[]>([]);
  const [initialParams, setInitialParams] = useState<AlgorithmParameterCreateRequest[]>([]);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  // params are edited inline now; no dialog/editing index needed
  const [showSuccessAnnouncement, setShowSuccessAnnouncement] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    // Reset common state
    setLoading(false);
    setShowSuccessAnnouncement(false);
    setErrorMessage(null);

    if (mode === 'edit' && initialAlgorithm) {
      // Prefill read-only fields
      setName(initialAlgorithm.name || '');
      setVersion(initialAlgorithm.version || '');
      setDescription(initialAlgorithm.description || '');
      setReferencesRequired(initialAlgorithm.references_required || 0);
      setZipFile(null);

      // Build params from backend data
      // Backend format: {param_name: {type, default, value}}
      const targetParam = initialAlgorithm.parameters?.find(p => p.id === initialAlgorithm.last_parameter_id);
      const backendParams = targetParam?.value || {};
      
      const baseSchema = Object.keys(backendParams).map((paramName) => {
        const paramData = backendParams[paramName];
        return {
          name: paramName,
          type: paramData.type || 'string',
          default: paramData.default ?? '',
          value: paramData.value ?? '',
        } as AlgorithmParameterCreateRequest;
      });
      
      setParams(baseSchema);
      setInitialParams(baseSchema.map(p => ({ ...p })));
    } else {
      // Create mode: empty fields
      setName('');
      setVersion('');
      setDescription('');
      setReferencesRequired(0);
      setParams([]);
      setInitialParams([]);
      setZipFile(null);
    }
  }, [open, mode, initialAlgorithm]);

  const handleCloseAll = () => {
    setErrorMessage(null);
    onClose();
  };

  const metadata: AlgorithmMetadata = useMemo(() => ({
    name: name.trim(),
    version: version.trim(),
    description: description.trim() || undefined,
    references_required: referencesRequired,
    parameters: params,
  }), [name, version, description, referencesRequired, params]);

  const canSubmit = name.trim() && version.trim();
  const isEdit = mode === 'edit';

  const isParamEmpty = (p: AlgorithmParameterCreateRequest) => {
    if (!p.name || !String(p.name).trim()) return true;
    const field = isEdit ? p.value : p.default;
    return field === '' || field === null || field === undefined;
  };

  const hasEmptyParam = params.length > 0 && params.some(isParamEmpty);

  const isRowDirty = (p: AlgorithmParameterCreateRequest, idx: number) => {
    const base = initialParams[idx];
    if (!base) {
      // new row -> dirty if any field not empty
      return Boolean(p.name || p.default || p.value);
    }
    if (isEdit) {
      return String(p.value ?? '') !== String(base.value ?? '');
    }
    // create mode: compare name/type/default
    return p.name !== base.name || p.type !== base.type || String(p.default ?? '') !== String(base.default ?? '');
  };

  // Inline param helpers
  const addParam = () => {
    const newParam = { name: '', type: 'string', default: '', value: '' } as AlgorithmParameterCreateRequest;
    setParams(prev => [...prev, newParam]);
    setInitialParams(prev => [...prev, { ...newParam }]);
  };

  const [selectedParamIndex, setSelectedParamIndex] = useState<number | null>(null);

  const deleteSelectedParam = () => {
    if (selectedParamIndex === null) return;
    setParams(prev => prev.filter((_, i) => i !== selectedParamIndex));
    setSelectedParamIndex(null);
    setInitialParams(prev => prev.filter((_, i) => i !== selectedParamIndex));
  };

  const updateParam = (index: number, field: keyof AlgorithmParameterCreateRequest, value: any) => {
    setParams(prev => prev.map((p, i) => i === index ? { ...p, [field]: value } : p));
  };

  const deleteParam = (index: number) => {
    setParams(prev => prev.filter((_, i) => i !== index));
    setInitialParams(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    if (isEdit) {
      try {
        setLoading(true);
        // Prepare parameters theo format backend: {param_name: {type, default, value}}
        const backendParams: Record<string, any> = {};
        params.forEach(p => {
          backendParams[p.name] = {
            type: p.type,
            default: p.default,
            value: p.value,
          };
        });
        
        // Gọi API update parameters
        const response = await algorithmAPI.updateParameters(
          initialAlgorithm!.id,
          backendParams
        );
        
        // Cập nhật values (chỉ giữ value thôi, không cần type/default)
        const values: Record<string, any> = params.reduce((acc, p) => {
          acc[p.name] = p.value;
          return acc;
        }, {} as Record<string, any>);
        
        if (onSaveValues) {
          onSaveValues(values);
        }
        
        setShowSuccessAnnouncement(true);
        setTimeout(() => {
          onSuccess();
          handleCloseAll();
        }, 800);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update parameters';
        setErrorMessage(message);
      } finally {
        setLoading(false);
      }
      return;
    }
    let registeredAlgorithmId: string | null = null;
    try {
      setLoading(true);
      // Values are always default during registration
      const payload: AlgorithmMetadata = {
        ...metadata,
        parameters: params.map(p => ({ ...p, value: p.default })),
      };
      const res = await algorithmAPI.register(payload);
      registeredAlgorithmId = res.algorithm_id;
      
      const values: Record<string, any> = params.reduce((acc, p) => {
        acc[p.name] = p.default;
        return acc;
      }, {} as Record<string, any>);
      
      if (onSaveValues) {
        onSaveValues(values);
      }

      if (zipFile) {
        try {
          const uploadRes = await algorithmAPI.uploadZip(res.algorithm_id, zipFile);
          // Upload thành công - exe_class đã được cập nhật ở backend
          console.log('Upload successful, exe_class:', uploadRes.exe_class);
        } catch (uploadErr) {
          // Upload failed - delete the registered algorithm
          try {
            await algorithmAPI.delete(res.algorithm_id);
          } catch (deleteErr) {
            console.error('Failed to delete algorithm after upload error:', deleteErr);
          }
          // Surface upload error to UI
          const msg = uploadErr instanceof Error ? uploadErr.message : String(uploadErr);
          setErrorMessage(msg || 'ZIP upload failed');
          return;
        }
      }

      setShowSuccessAnnouncement(true);
      setTimeout(() => {
        onSuccess();
        handleCloseAll();
      }, 1200);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create algorithm';
      setErrorMessage(message);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  if (showSuccessAnnouncement) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center max-w-md">
          <CheckCircle size={64} className="text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2">{isEdit ? 'Saved!' : 'Saved!'}</h2>
          <p className="text-gray-600 mb-2">
            {isEdit
              ? 'Parameters have been saved.'
              : `Algorithm has been registered${zipFile ? ' and uploaded' : ''} successfully.`}
          </p>
        </div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 text-center max-w-md">
          <AlertCircle size={56} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold mb-2 text-red-600">Error</h2>
          <p className="text-gray-700 mb-4 whitespace-pre-wrap">{errorMessage}</p>
          <div className="flex justify-center gap-2">
            <button onClick={() => setErrorMessage(null)} className="px-4 py-2 border rounded">Close</button>
            <button onClick={handleCloseAll} className="px-4 py-2 bg-gray-600 text-white rounded">Close Dialog</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-40 mb-0">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl m-4">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold">New Algorithm</h2>
          <button onClick={handleCloseAll} className="text-gray-500 hover:text-gray-700" disabled={loading}>
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
                disabled={isEdit}
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
                disabled={isEdit}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4"> 
            <div>
              <label className="block text-sm font-medium mb-1">References Required (minimum)</label>
              <input
                type="number"
                value={referencesRequired}
                onChange={(e) => setReferencesRequired(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                placeholder="0"
                min="0"
                disabled={isEdit}
              />
              <p className="text-xs text-gray-500 mt-1">Number of reference samples required for this algorithm</p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Module ZIP (optional)</label>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
                disabled={isEdit}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              rows={2}
              placeholder="Describe the algorithm..."
              disabled={isEdit}
            />
          </div>

          

          {/* Parameters */}
          <div className="border rounded p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Algorithm Params</h3>
              {!isEdit && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={addParam}
                    title="Add parameter"
                    className="p-1 bg-green-500 hover:bg-green-600 text-white rounded"
                  >
                    <Plus size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteSelectedParam()}
                    title="Delete selected"
                    className="p-1 bg-red-500 hover:bg-red-600 text-white rounded"
                  >
                    <Minus size={16} />
                  </button>
                </div>
              )}
            </div>

            <div className="overflow-x-auto overflow-y-scroll h-36 relative pr-2" style={{ scrollbarGutter: 'stable' }}>
                <table className="w-full text-sm table-fixed border-collapse">
                  <colgroup>
                    <col style={{ width: '45%' }} />
                    <col style={{ width: '25%' }} />
                    <col style={{ width: '30%' }} />
                  </colgroup>
                  <thead className="bg-gray-100 sticky top-0 z-10">
                    <tr>
                      <th className="text-left px-3 py-2">Name</th>
                      <th className="text-left px-3 py-2">Type</th>
                      <th className="text-left px-3 py-2">{isEdit ? 'Value' : 'Default'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {params.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="px-3 py-6 text-center text-sm text-gray-500">No parameters yet.</td>
                      </tr>
                    ) : (
                      params.map((p, idx) => {
                        const isSelected = selectedParamIndex === idx;
                        const isDirtyRow = isRowDirty(p, idx);
                        const invalidName = !p.name || !String(p.name).trim();
                        const invalidField = isEdit ? (p.value === '' || p.value === null || p.value === undefined) : (p.default === '' || p.default === null || p.default === undefined);
                        return (
                        <tr
                          key={idx}
                          role="button"
                          onClick={() => setSelectedParamIndex(isSelected ? null : idx)}
                          aria-pressed={isSelected}
                          className={`border-b transition-colors ${isSelected ? 'bg-blue-50 ring-1 ring-blue-300' : isDirtyRow ? 'bg-yellow-50' : 'bg-white'}`}
                        >
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={p.name}
                              onChange={(e) => updateParam(idx, 'name', e.target.value)}
                              className={`w-full border rounded px-2 py-1 ${invalidName ? 'border-red-400' : ''}`}
                              disabled={isEdit}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <select
                              value={p.type}
                              onChange={(e) => {
                                const t = e.target.value;
                                // reset default to sensible empty for new type
                                let def: any = '';
                                if (t === 'boolean') { def = ''; }
                                if (t === 'number') { def = ''; }
                                updateParam(idx, 'type', t);
                                updateParam(idx, 'default', def);
                              }}
                              className={`w-full border rounded px-2 py-1 ${invalidField && !isEdit ? 'border-red-400' : ''}`}
                              disabled={isEdit}
                            >
                              <option value="string">String</option>
                              <option value="number">Number</option>
                              <option value="boolean">Boolean</option>
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            {isEdit ? (
                              p.type === 'boolean' ? (
                                <select
                                  value={String(p.value ?? '')}
                                  onChange={(e) => updateParam(idx, 'value', e.target.value === 'true' ? true : e.target.value === 'false' ? false : '')}
                                  className={`w-full border rounded px-2 py-1 ${invalidField ? 'border-red-400' : ''}`}
                                >
                                  <option value="">{`-- Default: ${String(p.default ?? '')} --`}</option>
                                  <option value="true">True</option>
                                  <option value="false">False</option>
                                </select>
                              ) : (
                                <input
                                  type={p.type === 'number' ? 'number' : 'text'}
                                  value={String(p.value ?? '')}
                                  onChange={(e) => updateParam(idx, 'value', p.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                                  placeholder={String(p.default ?? '')}
                                  className={`w-full border rounded px-2 py-1 ${invalidField ? 'border-red-400' : ''}`}
                                />
                              )
                            ) : (
                              p.type === 'boolean' ? (
                                <select
                                  value={String(p.default ?? '')}
                                  onChange={(e) => updateParam(idx, 'default', e.target.value === 'true' ? true : e.target.value === 'false' ? false : '')}
                                  className={`w-full border rounded px-2 py-1 ${invalidField ? 'border-red-400' : ''}`}
                                >
                                  <option value="">-- None --</option>
                                  <option value="true">True</option>
                                  <option value="false">False</option>
                                </select>
                              ) : (
                                <input
                                  type={p.type === 'number' ? 'number' : 'text'}
                                  value={String(p.default ?? '')}
                                  onChange={(e) => updateParam(idx, 'default', p.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                                  className={`w-full border rounded px-2 py-1 ${invalidField ? 'border-red-400' : ''}`}
                                />
                              )
                            )}
                          </td>
                        </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
          </div>



          {hasEmptyParam && (
            <p className="text-sm text-red-600">Please fill all parameter {isEdit ? 'values' : 'defaults'} before submitting.</p>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleCloseAll}
              className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-60"
              disabled={loading || !canSubmit || hasEmptyParam}
            >
              {loading ? 'Saving...' : isEdit ? 'Save' : 'OK'}
            </button>
          </div>
        </form>
      </div>

      {/* Param dialog removed - params are edited inline */}
    </div>
  );
}
