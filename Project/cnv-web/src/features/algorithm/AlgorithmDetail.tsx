/**
 * AlgorithmDetail Component
 * Dialog to create/register an Algorithm with metadata and optional ZIP upload.
 */

"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { X, Plus, Minus, Check as CheckIcon, AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Box,
  Stack,
  Typography,
  FormHelperText,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  CircularProgress,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Tooltip,
} from '@mui/material';
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
    setInitialParams(prev => prev.filter((_, i) => i !== selectedParamIndex));
    // Adjust selectedParamIndex after deletion
    setSelectedParamIndex(prev => {
      if (prev === null) return null;
      if (prev >= params.length - 1) return params.length - 2 >= 0 ? params.length - 2 : null;
      return prev;
    });
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
      <Dialog open={true} maxWidth="sm" fullWidth>
        <DialogContent sx={{ textAlign: 'center', py: 6 }}>
          <Box sx={{ mb: 2 }}>
            <CheckIcon size={64} color="#10B981" style={{ margin: '0 auto', display: 'block' }} />
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
            {isEdit ? 'Saved!' : 'Saved!'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {isEdit
              ? 'Parameters have been saved.'
              : `Algorithm has been registered${zipFile ? ' and uploaded' : ''} successfully.`}
          </Typography>
        </DialogContent>
      </Dialog>
    );
  }

  if (errorMessage) {
    return (
      <Dialog open={true} maxWidth="sm" fullWidth>
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <Box sx={{ mb: 2 }}>
            <AlertTriangle size={56} color="#EF4444" style={{ margin: '0 auto', display: 'block' }} />
          </Box>
          <Typography variant="h5" sx={{ fontWeight: 600, color: '#EF4444', mb: 2 }}>
            Error
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-wrap', mb: 3 }}>
            {errorMessage}
          </Typography>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', gap: 1, pb: 2 }}>
          <Button onClick={() => setErrorMessage(null)} variant="outlined">
            Close
          </Button>
          <Button onClick={handleCloseAll} variant="contained" color="inherit">
            Close Dialog
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} maxWidth="md" fullWidth onClose={handleCloseAll}>
      <DialogTitle sx={{ fontWeight: 600, fontSize: '1.25rem', pb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{isEdit ? 'Edit Algorithm' : 'New Algorithm'}</span>
        <button
          type="button"
          aria-label="Close dialog"
          onClick={handleCloseAll}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', borderRadius: '4px', color: 'inherit' }}
          onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F3F4F6')}
          onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
        >
          ✕
        </button>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 3, maxHeight: '64vh', overflow: 'auto', scrollbarGutter: 'stable' }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Basic Info - Name & Version */}
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 500 }}>
                Name <span style={{ color: '#EF4444' }}>*</span>
              </Typography>
              <TextField
                value={name}
                onChange={(e) => setName(e.target.value)}
                fullWidth
                required
                disabled={isEdit}
                inputProps={{ placeholder: 'e.g., MyAlgorithm' }}
                variant="outlined"
                size="small"
              />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 500 }}>
                Version <span style={{ color: '#EF4444' }}>*</span>
              </Typography>
              <TextField
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                fullWidth
                required
                disabled={isEdit}
                inputProps={{ placeholder: 'e.g., 1.0.0' }}
                variant="outlined"
                size="small"
              />
            </Box>
          </Stack>

          {/* References & Module ZIP */}
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 500 }}>
                References Required (minimum)
              </Typography>
              <TextField
                type="text"
                value={referencesRequired}
                onChange={(e) => setReferencesRequired(Math.max(0, parseInt(e.target.value) || 0))}
                fullWidth
                disabled={isEdit}
                inputProps={{ placeholder: '0' }}
                variant="outlined"
                size="small"
              />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 500 }}>
                Plug-in Module
              </Typography>
              <TextField
                type="file"
                inputProps={{ accept: '.zip' }}
                onChange={(e) => setZipFile((e.target as HTMLInputElement).files?.[0] || null)}
                fullWidth
                disabled={isEdit}
                variant="outlined"
                size="small"
                slotProps={{
                  input: {
                    style: { padding: 0 }
                  }
                }}
              />
              <style>{`
                input[type="file"]::file-selector-button {
                  display: none;
                }
              `}</style>
            </Box>
          </Stack>

          <Box>
            <Typography variant="body2" sx={{ mb: 0.5, fontWeight: 500 }}>
              Description
            </Typography>
            <TextField
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              multiline
              rows={2}
              fullWidth
              disabled={isEdit}
              inputProps={{ placeholder: 'Describe the algorithm...' }}
              variant="outlined"
              size="small"
            />
          </Box>

          {/* Parameters */}
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Algorithm Params
              </Typography>
              {!isEdit && (
                <Stack direction="row" spacing={1}>
                  <Tooltip title="Add parameter">
                    <Button
                      size="small"
                      onClick={addParam}
                      variant="contained"
                      sx={{ minWidth: 0, px: 1, bgcolor: '#10B981', '&:hover': { bgcolor: '#059669' } }}
                    >
                      <Plus size={14} />
                    </Button>
                  </Tooltip>
                  <Tooltip title="Delete selected">
                    <Button
                      size="small"
                      onClick={() => deleteSelectedParam()}
                      variant="contained"
                      disabled={selectedParamIndex === null}
                      sx={{ minWidth: 0, px: 1, bgcolor: '#EF4444', '&:hover': { bgcolor: '#DC2626' } }}
                    >
                      <Minus size={14} />
                    </Button>
                  </Tooltip>
                </Stack>
              )}
            </Box>

            <Paper variant="outlined">
              <Table size="small">
                <TableHead sx={{ bgcolor: '#F3F4F6', position: 'sticky', top: 0 }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>{isEdit ? 'Value' : 'Default'}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {params.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
                        No parameters yet.
                      </TableCell>
                    </TableRow>
                  ) : (
                    params.map((p, idx) => {
                      const isSelected = selectedParamIndex === idx;
                      const isDirtyRow = isRowDirty(p, idx);
                      const invalidName = !p.name || !String(p.name).trim();
                      const invalidField = isEdit ? (p.value === '' || p.value === null || p.value === undefined) : (p.default === '' || p.default === null || p.default === undefined);
                      const isEmpty = invalidName || invalidField;
                      const isFilled = !isEmpty;

                      // Determine background color
                      let bgColor = '#fff';
                      if (isSelected) {
                        bgColor = '#DBEAFE'; // light blue for selected
                      } else if (isEmpty) {
                        bgColor = '#FEE2E2'; // light red for empty
                      } else if (isFilled) {
                        bgColor = '#fff'; // white for filled
                      }

                      return (
                        <TableRow
                          key={idx}
                          onClick={() => setSelectedParamIndex(idx)}
                          role="button"
                          sx={{
                            cursor: 'pointer',
                            bgcolor: bgColor,
                            borderLeft: isSelected ? '3px solid' : 'none',
                            borderLeftColor: isSelected ? 'primary.main' : 'transparent',
                            '&:hover': { 
                              bgcolor: isSelected ? '#DBEAFE' : '#F3F4F6'
                            },
                          }}
                        >
                          <TableCell>
                            <TextField
                              size="small"
                              value={p.name}
                              onChange={(e) => updateParam(idx, 'name', e.target.value)}
                              disabled={isEdit}
                              error={invalidName}
                              fullWidth
                              variant="standard"
                              InputProps={{ disableUnderline: true }}
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              size="small"
                              value={p.type}
                              onChange={(e) => {
                                const t = e.target.value;
                                updateParam(idx, 'type', t);
                                updateParam(idx, 'default', '');
                              }}
                              disabled={isEdit}
                              variant="standard"
                              sx={{ width: '100%' }}
                            >
                              <MenuItem value="string">String</MenuItem>
                              <MenuItem value="number">Number</MenuItem>
                              <MenuItem value="boolean">Boolean</MenuItem>
                            </Select>
                          </TableCell>
                          <TableCell>
                            {isEdit ? (
                              p.type === 'boolean' ? (
                                <Select
                                  size="small"
                                  value={String(p.value ?? '')}
                                  onChange={(e) => updateParam(idx, 'value', e.target.value === 'true' ? true : e.target.value === 'false' ? false : '')}
                                  error={invalidField}
                                  variant="standard"
                                  sx={{ width: '100%' }}
                                >
                                  <MenuItem value="">{`-- Default: ${String(p.default ?? '')} --`}</MenuItem>
                                  <MenuItem value="true">True</MenuItem>
                                  <MenuItem value="false">False</MenuItem>
                                </Select>
                              ) : (
                                <TextField
                                  size="small"
                                  type={p.type === 'number' ? 'number' : 'text'}
                                  value={String(p.value ?? '')}
                                  onChange={(e) => updateParam(idx, 'value', p.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                                  placeholder={String(p.default ?? '')}
                                  error={invalidField}
                                  fullWidth
                                  variant="standard"
                                  InputProps={{ disableUnderline: true }}
                                />
                              )
                            ) : (
                              p.type === 'boolean' ? (
                                <Select
                                  size="small"
                                  value={String(p.default ?? '')}
                                  onChange={(e) => updateParam(idx, 'default', e.target.value === 'true' ? true : e.target.value === 'false' ? false : '')}
                                  error={invalidField}
                                  variant="standard"
                                  sx={{ width: '100%' }}
                                >
                                  <MenuItem value="">-- None --</MenuItem>
                                  <MenuItem value="true">True</MenuItem>
                                  <MenuItem value="false">False</MenuItem>
                                </Select>
                              ) : (
                                <TextField
                                  size="small"
                                  type={p.type === 'number' ? 'number' : 'text'}
                                  value={String(p.default ?? '')}
                                  onChange={(e) => updateParam(idx, 'default', p.type === 'number' ? (e.target.value === '' ? '' : Number(e.target.value)) : e.target.value)}
                                  fullWidth
                                  variant="standard"
                                  InputProps={{ disableUnderline: true }}
                                />
                              )
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </Paper>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button onClick={handleCloseAll} disabled={loading}>
          Cancel
        </Button>
        <Button
          type="submit"
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !canSubmit || hasEmptyParam}
        >
          {loading ? 'Saving...' : isEdit ? 'Save' : 'OK'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
