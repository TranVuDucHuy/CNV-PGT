import { Button, Typography, Container } from "@mui/material";

export default function Super() {
  return (
    <Container sx={{ textAlign: "center", mt: 8 }}>
      <Typography variant="h3" gutterBottom>
        🚀 Next.js + Material UI + TypeScript
      </Typography>
      <Button variant="contained" color="primary">
        Hello MUI
      </Button>
    </Container>
  );
}
