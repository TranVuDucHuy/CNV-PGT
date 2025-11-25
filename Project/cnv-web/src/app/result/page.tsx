import { Typography } from "@mui/material";

// Export metadata to change title to "Result"

export const metadata = {
  title: "Results",
};

const ResultPage = () => {
  return (
    <Typography variant="h6" color="text.secondary">
      Select a result to view details
    </Typography>
  );
};

export default ResultPage;
