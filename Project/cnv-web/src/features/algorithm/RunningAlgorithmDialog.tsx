/**
 * RunningAlgorithmDialog
 * Hiển thị trạng thái đang chạy algorithm
 */

import React from "react";
import { Dialog, DialogTitle, DialogContent, Box, Stack, Typography, Table, TableHead, TableBody, TableRow, TableCell, CircularProgress, Button, Divider, TableContainer } from "@mui/material";

interface Props {
  open: boolean;
  sampleName: string;
  algorithmName: string;
  algorithmVersion: string;
  parameters: Record<string, any>;
}

export default function RunningAlgorithmDialog({ open, sampleName, algorithmName, algorithmVersion, parameters }: Props) {
  const paramEntries = Object.entries(parameters || {});

  return (
    <Dialog open={open} maxWidth="sm" fullWidth disableEscapeKeyDown>
      <DialogTitle sx={{ fontWeight: 600, pb: 0 }}>
        <Typography variant="h3" sx={{ fontWeight: 600 }}>
          Running Algorithm...
        </Typography>
      </DialogTitle>
      <Divider sx={{ mt: 2, mx: 3 }} />

      <DialogContent sx={{ pb: 4 }}>
        <Stack spacing={2.5}>
          <Box>
            <Typography variant="body2">Sample</Typography>
            <Typography variant="body1">{sampleName}</Typography>
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 2,
              mb: 2,
            }}
          >
            <Box>
              <Typography variant="body2">Name</Typography>
              <Typography variant="body1">{algorithmName}</Typography>
            </Box>
            <Box>
              <Typography variant="body2">Version</Typography>
              <Typography variant="body1">{algorithmVersion}</Typography>
            </Box>
          </Box>

          {paramEntries.length > 0 && (
            <TableContainer>
              <Table size="small" sx={{ tableLayout: "fixed" }}>
                <colgroup>
                  <col style={{ width: "50%" }} />
                  <col style={{ width: "50%" }} />
                </colgroup>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ pl: 0, pr: 1 }}>
                      <Typography variant="body2">Parameter</Typography>
                    </TableCell>
                    <TableCell sx={{ pl: 1, pr: 0 }}>
                      <Typography variant="body2">Value</Typography>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paramEntries.map(([key, paramData]) => {
                    const displayValue = typeof paramData === "object" && paramData !== null && "value" in paramData ? String(paramData.value ?? paramData.default ?? "") : String(paramData ?? "");

                    return (
                      <TableRow key={key}>
                        <TableCell sx={{ pl: 0, pr: 1 }}>
                          <Typography variant="body1">{key}</Typography>
                        </TableCell>
                        <TableCell sx={{ pl: 1, pr: 0 }}>
                          <Typography variant="body1">{displayValue}</Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}
