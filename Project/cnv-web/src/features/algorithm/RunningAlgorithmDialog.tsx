/**
 * RunningAlgorithmDialog
 * Hiển thị trạng thái đang chạy algorithm
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Stack,
  Typography,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  CircularProgress,
} from '@mui/material';

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
  const paramEntries = Object.entries(parameters || {});

  return (
    <Dialog open={open} maxWidth="sm" fullWidth disableEscapeKeyDown>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1.5, fontWeight: 600 }}>
        <CircularProgress size={24} />
        Running Algorithm
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Stack spacing={2.5}>
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Sample:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
              {sampleName}
            </Typography>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
              Algorithm:
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500, mt: 0.5 }}>
              {algorithmName}{' '}
              <Typography component="span" variant="caption" color="text.secondary">
                v{algorithmVersion}
              </Typography>
            </Typography>
          </Box>

          {paramEntries.length > 0 && (
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600, display: 'block', mb: 1 }}>
                Parameters:
              </Typography>
              <Paper variant="outlined">
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#F3F4F6' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paramEntries.map(([key, paramData]) => {
                      const displayValue = typeof paramData === 'object' && paramData !== null && 'value' in paramData
                        ? String(paramData.value ?? paramData.default ?? '')
                        : String(paramData ?? '');

                      return (
                        <TableRow key={key}>
                          <TableCell sx={{ fontWeight: 500 }}>{key}</TableCell>
                          <TableCell>{displayValue}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </Paper>
            </Box>
          )}

          <Typography variant="caption" color="text.secondary" sx={{ textAlign: 'center', display: 'block', pt: 1 }}>
            Please wait while the algorithm is running...
          </Typography>
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
