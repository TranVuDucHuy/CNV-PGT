import React, { useState } from "react";
import { IconButton, Menu, MenuItem, ListItemIcon, ListItemText, Typography } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";

export interface ExportAction {
  id: string;
  label: string;
  subLabel?: string;
  icon?: React.ReactNode;
  onClick: () => void;
}

interface ExportMenuButtonProps {
  actions: ExportAction[];
  size?: "small" | "medium" | "large";
}

export const ExportMenuButton: React.FC<ExportMenuButtonProps> = ({ actions, size = "small" }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleActionClick = (action: ExportAction) => {
    action.onClick();
    handleClose();
  };

  if (actions.length === 0) {
    return null;
  }

  return (
    <>
      <IconButton onClick={handleClick} size={size}>
        <DownloadIcon />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        slotProps={{
          paper: {
            elevation: 3,
            sx: {
              minWidth: 200,
              mt: 0.5,
              borderRadius: 2,
            },
          },
        }}
      >
        {actions.map((action) => (
          <MenuItem key={action.id} onClick={() => handleActionClick(action)}>
            {action.icon && <ListItemIcon>{action.icon}</ListItemIcon>}
            <ListItemText>
              <Typography sx={{ fontWeight: 500 }}>{action.label}</Typography>
              {action.subLabel && (
                <Typography variant="caption" color="text.secondary">
                  {action.subLabel}
                </Typography>
              )}
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};
