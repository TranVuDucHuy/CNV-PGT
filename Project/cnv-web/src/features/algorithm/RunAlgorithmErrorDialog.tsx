/**
 * RunAlgorithmErrorDialog
 * Hiển thị lỗi khi chạy algorithm thất bại
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  AlertTitle,
} from '@mui/material';
import { AlertTriangle } from 'lucide-react';

interface Props {
  open: boolean;
  errorMessage: string;
  onClose: () => void;
  onRetry: () => void;
}

export default function RunAlgorithmErrorDialog({ open, errorMessage, onClose, onRetry }: Props) {
  return (
    <Dialog open={open} maxWidth="sm" fullWidth onClose={onClose}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontWeight: 600, color: '#EF4444' }}>
        <AlertTriangle size={24} color="#EF4444" />
        Error Running Algorithm
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          <AlertTitle>Algorithm Execution Failed</AlertTitle>
        </Alert>

        <Typography
          variant="body2"
          sx={{
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            p: 1.5,
            bgcolor: '#F3F4F6',
            borderRadius: 1,
            border: '1px solid #E5E7EB',
          }}
        >
          {errorMessage}
        </Typography>
      </DialogContent>

      <DialogActions sx={{ gap: 1, p: 2 }}>
        <Button onClick={onClose}>Close</Button>
        <Button onClick={onRetry} variant="contained">
          Retry
        </Button>
      </DialogActions>
    </Dialog>
  );
}
