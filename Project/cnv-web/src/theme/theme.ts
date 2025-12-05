import { createTheme } from "@mui/material/styles";
import colors from "./colors";

const theme = createTheme({
  palette: {
    primary1: {
      main: colors.primary1,
      dark: colors.primary1Dark,
      light: colors.primary1Light,
      contrastText: colors.neutralWhite,
    },
    secondary: {
      main: colors.primary2,
      light: colors.primary2Light,
    },
    error: {
      main: colors.error,
    },
    success: {
      main: colors.success,
    },
  },
  typography: {
    // Use IBM Plex Sans as primary UI font
    fontFamily:
      "'IBM Plex Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif",
    // Style 1: CNV Analysis Dashboard (Heading 1)
    h1: {
      fontSize: "22px",
      fontWeight: 700,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
    // Style 2: Pane Titles (Heading 2)
    h2: {
      fontSize: "18px",
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
    // Style 3: Dialog Bar Titles (Heading 3)
    h3: {
      fontSize: "22px",
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
    // Style 4: View Bar Titles (Heading 4)
    h4: {
      fontSize: "16px",
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
    // Defaults for Labels, placeholders
    body1: {
      fontSize: "14px",
      fontWeight: 400,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
    // Defaults for Pane content
    body2: {
      fontSize: "15px",
      fontWeight: 600,
      lineHeight: 1.5,
      color: colors.primary1Dark,
    },
    // Caption style
    caption: {
      fontSize: "12px",
      fontWeight: 400,
      lineHeight: 1.5,
      color: colors.neutralBlack,
    },
  },
});

export default theme;
