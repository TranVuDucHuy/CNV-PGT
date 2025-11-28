import {
  Box,
  Alert,
  Skeleton,
  Typography,
  Paper,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  SxProps,
  Theme,
} from "@mui/material";
import IosShareIcon from "@mui/icons-material/IosShare";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import GridOnIcon from "@mui/icons-material/GridOn";
import { ResultReportResponse } from "@/types/result";
import { useState } from "react";

interface ResultReport {
  loading: boolean;
  error: string | null;
  report: ResultReportResponse | null;
  exportToDocx: (report: ResultReportResponse) => void;
  exportToXlsx: (report: ResultReportResponse) => void;
  exportToPdf: (report: ResultReportResponse) => void;
  sx?: SxProps<Theme>;
}

export const ResultReport: React.FC<ResultReport> = ({
  loading,
  error,
  report,
  exportToDocx,
  exportToXlsx,
  exportToPdf,
  sx,
}) => {
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(
    null
  );
  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportAnchorEl(event.currentTarget);
  };

  // Handle export menu close
  const handleExportClose = () => {
    setExportAnchorEl(null);
  };

  // Export handlers
  const handleExportExcel = () => {
    if (report) {
      exportToXlsx(report);
    }
    handleExportClose();
  };

  const handleExportWord = async () => {
    if (report) {
      await exportToDocx(report);
    }
    handleExportClose();
  };

  const handleExportPDF = async () => {
    if (report) {
      await exportToPdf(report);
    }
    handleExportClose();
  };
  const exportMenuOpen = Boolean(exportAnchorEl);
  return (
    <Box
      sx={{
        flex: 1,
        bgcolor: "grey.50",
        overflow: "auto",
        p: 2,
        ...sx,
      }}
    >
      {loading && (
        <Box>
          <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
          <Skeleton variant="rectangular" height={300} />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && !error && report && (
        <Box>
          <Box sx={{ ml: 1 }}>
            <Stack
              direction="row"
              alignItems="center"
              justifyContent={"space-between"}
            >
              <Typography variant="h5" gutterBottom>
                Result Report
              </Typography>
              <Box>
                <Button
                  variant="contained"
                  sx={{
                    ml: 2,
                    backgroundColor: "green",
                    "&:hover": { backgroundColor: "darkgreen" },
                    fontWeight: "bold",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  onClick={handleExportClick}
                >
                  <IosShareIcon sx={{ mr: 1 }} />
                  Export
                </Button>
                <Menu
                  anchorEl={exportAnchorEl}
                  open={exportMenuOpen}
                  onClose={handleExportClose}
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
                  <MenuItem onClick={handleExportExcel}>
                    <ListItemIcon>
                      <GridOnIcon sx={{ color: "#1D6F42" }} />
                    </ListItemIcon>
                    <ListItemText>
                      <Typography sx={{ fontWeight: 500 }}>
                        Export to Excel
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        .xlsx file
                      </Typography>
                    </ListItemText>
                  </MenuItem>
                  <MenuItem onClick={handleExportWord}>
                    <ListItemIcon>
                      <DescriptionIcon sx={{ color: "#2B579A" }} />
                    </ListItemIcon>
                    <ListItemText>
                      <Typography sx={{ fontWeight: 500 }}>
                        Export to Word
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        .docx file
                      </Typography>
                    </ListItemText>
                  </MenuItem>
                  <MenuItem onClick={handleExportPDF}>
                    <ListItemIcon>
                      <PictureAsPdfIcon sx={{ color: "#D32F2F" }} />
                    </ListItemIcon>
                    <ListItemText>
                      <Typography sx={{ fontWeight: 500 }}>
                        Export to PDF
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        .pdf file
                      </Typography>
                    </ListItemText>
                  </MenuItem>
                </Menu>
              </Box>
            </Stack>
            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
              ID: {report.result_id}
            </Typography>{" "}
          </Box>

          {/* Sample Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Sample Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: 2,
              }}
            >
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Flowcell ID
                </Typography>
                <Typography variant="body1">
                  {report.sample.flowcell_id}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Cycle ID
                </Typography>
                <Typography variant="body1">
                  {report.sample.cycle_id}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Embryo ID
                </Typography>
                <Typography variant="body1">
                  {report.sample.embryo_id}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Cell Type
                </Typography>
                <Typography variant="body1">
                  {report.sample.cell_type}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Reference Genome
                </Typography>
                <Typography variant="body1">
                  {report.sample.reference_genome}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Date
                </Typography>
                <Typography variant="body1">
                  {new Date(report.sample.date).toLocaleDateString()}
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* Algorithm Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Algorithm Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 2,
                mb: 2,
              }}
            >
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Name
                </Typography>
                <Typography variant="body1">{report.algorithm.name}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Version
                </Typography>
                <Typography variant="body1">
                  {report.algorithm.version}
                </Typography>
              </Box>
            </Box>

            {report.algorithm.parameters.length > 0 && (
              <>
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Parameters
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Default</TableCell>
                        <TableCell>Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {report.algorithm.parameters.map((param, index) => (
                        <TableRow key={index}>
                          <TableCell>{param.name}</TableCell>
                          <TableCell>{param.type}</TableCell>
                          <TableCell>{JSON.stringify(param.default)}</TableCell>
                          <TableCell>
                            <strong>{JSON.stringify(param.value)}</strong>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
          </Paper>

          {/* Aberration Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Aberration Analysis
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* Aberration Summary */}
            {report.aberration.aberration_summary &&
              report.aberration.aberration_summary.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Summary
                  </Typography>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                    {report.aberration.aberration_summary.map(
                      (summary, index) => (
                        <Chip
                          key={index}
                          label={summary}
                          color="primary"
                          variant="outlined"
                        />
                      )
                    )}
                  </Box>
                </Box>
              )}

            {/* Aberration Segments */}
            {report.aberration.aberration_segments.length > 0 && (
              <>
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Aberration Segments (
                  {report.aberration.aberration_segments.length})
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Chromosome</TableCell>
                        <TableCell>Start</TableCell>
                        <TableCell>End</TableCell>
                        <TableCell>Size (bp)</TableCell>
                        <TableCell>Copy Number</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Mosaicism</TableCell>
                        <TableCell>Code</TableCell>
                        <TableCell>Assessment</TableCell>
                        <TableCell>Annotation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {report.aberration.aberration_segments.map(
                        (segment, index) => (
                          <TableRow key={index}>
                            <TableCell>{segment.chromosome}</TableCell>
                            <TableCell>
                              {segment.start.toLocaleString()}
                            </TableCell>
                            <TableCell>
                              {segment.end.toLocaleString()}
                            </TableCell>
                            <TableCell>
                              {segment.size.toLocaleString()}
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={segment.copy_number.toFixed(2)}
                                size="small"
                                color={
                                  segment.copy_number < 2
                                    ? "error"
                                    : segment.copy_number > 2
                                    ? "warning"
                                    : "success"
                                }
                              />
                            </TableCell>
                            <TableCell>{segment.type}</TableCell>
                            <TableCell>
                              {(segment.mosaicism * 100).toFixed(1)}%
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={segment.aberration_code}
                                size="small"
                              />
                            </TableCell>
                            <TableCell>{segment.assessment}</TableCell>
                            <TableCell>
                              {segment.annotation_for_segment || "-"}
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {report.aberration.aberration_segments.length === 0 && (
              <Typography color="text.secondary">
                No aberrations detected
              </Typography>
            )}
          </Paper>
        </Box>
      )}

      {!loading && !error && !report && (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
          }}
        >
          <Typography variant="h6" color="text.secondary">
            No result selected
          </Typography>
        </Box>
      )}
    </Box>
  );
};
