import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  typography: {
    // Use IBM Plex Sans as primary UI font
    fontFamily: "'IBM Plex Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif",
    // Style 1: CNV Analysis Dashboard (Heading 1)
    h1: {
      fontSize: '28px',
      fontWeight: 700,
      lineHeight: 1.25,
      letterSpacing: '-0.5px',
      color: '#111827', // Tailwind gray-900
    },
    // Style 2: Pane Titles & Dialog Bar Titles (Heading 2)
    h2: {
      fontSize: '20px',
      fontWeight: 600,
      lineHeight: 1.3,
      letterSpacing: '-0.25px',
      color: '#111827', // Tailwind gray-900
    },
    // Style 3: Pane content headings (Heading 3)
    h3: {
      fontSize: '16px',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    // Style 4: Labels, placeholders (Heading 4 / subtitle)
    h4: {
      fontSize: '14px',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    // Defaults for body text
    body1: {
      fontSize: '14px',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '13px',
      lineHeight: 1.4,
    },
  },
});

export default theme;
