// ViewPane.tsx
"use client";

import React from "react";
import { Box, Checkbox, Stack, Typography, IconButton } from "@mui/material";
import { Edit3 } from "lucide-react";
import { useViewHandle } from "./viewHandle";
import MUIAccordionPane from "@/components/MUIAccordionPane";

export default function ViewPane() {
  const { checked, toggle } = useViewHandle();

  const headerRight = (
    <IconButton onClick={(e) => e.stopPropagation()} title="Edit" size="small" sx={{ bgcolor: "#3B82F6", color: "#fff", "&:hover": { bgcolor: "#2563EB" } }}>
      <Edit3 size={16} />
    </IconButton>
  );

  return (
    <MUIAccordionPane title="View" defaultExpanded headerRight={headerRight}>
      <Box>
        <Stack spacing={1}>
          {(Object.keys(checked) as Array<keyof typeof checked>).map((key) => {
            const label = key.replace(/([A-Z])/g, " $1").replace(/^./, (c) => c.toUpperCase());
            return (
              <Box key={key} sx={{ display: "flex", alignItems: "center" }}>
                <Checkbox checked={checked[key]} onChange={() => toggle(key)} size="small" />
                <Typography variant="body2">{label}</Typography>
              </Box>
            );
          })}
        </Stack>
      </Box>
    </MUIAccordionPane>
  );
}
