// ViewPane.tsx
"use client";

import React from "react";
import {
  Box,
  Checkbox,
  Stack,
  Typography,
  IconButton,
  Button,
} from "@mui/material";
import { Edit3 } from "lucide-react";
import { useViewHandle } from "./viewHandle";
import MUIAccordionPane from "@/components/MUIAccordionPane";

import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/utils/store";
import { setViewOption } from "@/utils/appSlice";

export default function ViewPane() {
  const checked = useSelector((state: RootState) => state.app.viewChecked);
  const dispatch = useDispatch()
  const headerRight = (
    <Button
      onClick={(e) => e.stopPropagation()}
      title="Edit"
      size="small"
      sx={{
        minWidth: 0,
        p: 0.5,
        border: 2,
        borderColor: "#3B82F6",
        bgcolor: "transparent",
        color: "#3B82F6",
        "& svg": { color: "#3B82F6" },
        "&:hover": { bgcolor: "#3B82F6", "& svg": { color: "#fff" } },
      }}
    >
      <Edit3 size={16} />
    </Button>
  );

  return (
    <MUIAccordionPane title="View" defaultExpanded headerRight={headerRight}>
      <Box>
        <Stack spacing={1}>
          {(Object.keys(checked) as Array<keyof typeof checked>).map((key) => {
            const label = key
              .replace(/([A-Z])/g, " $1")
              .replace(/^./, (c) => c.toUpperCase());
            return (
              <Box key={key} sx={{ display: "flex", alignItems: "center" }}>
                <Checkbox
                  checked={checked[key]}
                  onChange={(event, check) => {
                      dispatch(setViewOption({key: key, value: check}))
                    }
                  }
                  size="small"
                />
                <Typography variant="body2">{label}</Typography>
              </Box>
            );
          })}
          {/* <Typography variant="caption" color="textSecondary">
            Select which components to display in the content pane.
          </Typography> */}
        </Stack>
      </Box>
    </MUIAccordionPane>
  );
}
