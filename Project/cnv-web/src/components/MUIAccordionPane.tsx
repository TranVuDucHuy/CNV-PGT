"use client";

import React from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Stack,
  Typography,
} from "@mui/material";
import { ChevronRight } from "lucide-react";

type Props = {
  title: React.ReactNode;
  defaultExpanded?: boolean;
  headerRight?: React.ReactNode;
  children?: React.ReactNode;
};

export default function MUIAccordionPane({
  title,
  defaultExpanded = true,
  headerRight,
  children,
}: Props) {
  return (
    <Accordion
      defaultExpanded={defaultExpanded}
      disableGutters
      elevation={0}
      sx={{
        border: "1px solid",
        borderColor: "grey.300",
        borderRadius: 1,
        overflow: "hidden", // giữ border-radius
        bgcolor: "background2",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
      }}
    >
      <AccordionSummary
        expandIcon={<ChevronRight size={18} />}
        sx={{
          "& .MuiAccordionSummary-expandIconWrapper": {
            order: -1, // icon về bên trái
            mr: 1,
            transition: "transform 0.15s ease",
          },
          "&.Mui-expanded .MuiAccordionSummary-expandIconWrapper": {
            transform: "rotate(90deg)", // xoay khi mở
          },
          "& .MuiAccordionSummary-content": {
            my: 0.5,
          },
          bgcolor: "primary1.light",
          py: 1,
          px: 1.5,
          cursor: "pointer",
          alignItems: "center",
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1} sx={{ flex: 1 }}>
          <Typography
            variant="h2"
          >
            {title}
          </Typography>
        </Stack>

        {headerRight && (
          <Box
            component="span" // tránh button lồng button
            onClick={(e) => {
              e.stopPropagation(); // click bên trong không toggle Accordion
            }}
          >
            {/* Nếu dynamic (client-only), tránh SSR mismatch */}
            {typeof window !== "undefined" ? headerRight : null}
          </Box>
        )}
      </AccordionSummary>

      <AccordionDetails sx={{ p: 1.5, pr: 0.5 }}>{children}</AccordionDetails>
    </Accordion>
  );
}
