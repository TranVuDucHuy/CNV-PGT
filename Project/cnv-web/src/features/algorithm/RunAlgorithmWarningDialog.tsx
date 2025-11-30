/**
 * RunAlgorithmWarningDialog
 * Hiển thị cảnh báo khi algorithm chưa đủ điều kiện chạy
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
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  AlertTitle,
} from '@mui/material';
import { AlertTriangle, AlertCircle } from 'lucide-react';

interface Props {
  open: boolean;
  onClose: () => void;
  referencesRequired: number;
  onUploadModule?: () => void;
}

export default function RunAlgorithmWarningDialog({ open, onClose, referencesRequired, onUploadModule }: Props) {
  return (
    <Dialog open={open} maxWidth="sm" fullWidth onClose={onClose}>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontWeight: 600, fontSize: '1.1rem' }}>
        <AlertTriangle color="#EA580C" size={24} />
        Cannot Run Algorithm
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>Missing Requirements</AlertTitle>
          Algorithm requires uploaded module and {referencesRequired} reference{referencesRequired !== 1 ? 's' : ''} sample to run.
        </Alert>

        <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
          Please ensure:
        </Typography>
        <List dense sx={{ ml: 1 }}>
          <ListItem>
            <ListItemIcon>
              <AlertCircle size={16} />
            </ListItemIcon>
            <ListItemText
              primary="Algorithm module (ZIP file) has been uploaded"
              primaryTypographyProps={{ variant: 'body2' }}
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <AlertCircle size={16} />
            </ListItemIcon>
            <ListItemText
              primary={`At least ${referencesRequired} reference sample${referencesRequired !== 1 ? 's are' : ' is'} selected in the Reference pane`}
              primaryTypographyProps={{ variant: 'body2' }}
            />
          </ListItem>
        </List>
      </DialogContent>

      <DialogActions sx={{ gap: 1, p: 2 }}>
        <Button onClick={onClose}>Close</Button>
        {onUploadModule && (
          <Button
            onClick={() => {
              onUploadModule();
              onClose();
            }}
            variant="contained"
          >
            Upload Module
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
