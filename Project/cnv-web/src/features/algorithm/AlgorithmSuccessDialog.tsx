/**
 * AlgorithmSuccessDialog
 * Hiển thị thông báo khi chạy algorithm thành công
 */

import React from "react";
import { Dialog, DialogContent, DialogActions, Button, Typography } from "@mui/material";
import { CheckCircle } from "lucide-react";

interface Props {
  open: boolean;
  sampleName: string;
  algorithmName: string;
  onClose: () => void;
}

export default function AlgorithmSuccessDialog({ open, sampleName, algorithmName, onClose }: Props) {
  return (
    <Dialog open={open} maxWidth="xs" fullWidth onClose={onClose}>
      <DialogContent sx={{ textAlign: "left", py: 3, display: "flex", alignItems: "center", gap: 2 }}>
        <CheckCircle size={32} color="#10B981" style={{ flexShrink: 0 }} />

        <div>
          <Typography variant="body1" sx={{ fontWeight: 600, fontSize: 18 }}>
            Done
          </Typography>

          <Typography variant="body1">Tác vụ đã hoàn tất thành công.</Typography>
        </div>
      </DialogContent>

      <DialogActions sx={{ justifyContent: "flex-end", pt: 0, pb: 2, pr: 2 }}>
        <Button onClick={onClose} sx={{ color: "#6a7282" }} className="rounded-md px-4 py-2 text-sm font-medium">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
