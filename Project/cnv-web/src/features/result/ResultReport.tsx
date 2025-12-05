import { Box, Alert, Skeleton, Typography, Paper, Chip, Divider, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Stack, Button, Menu, MenuItem, ListItemIcon, ListItemText, SxProps, Theme } from "@mui/material";
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

export const ResultReport: React.FC<ResultReport> = ({ loading, error, report, exportToDocx, exportToXlsx, exportToPdf, sx }) => {
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);
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
            <Stack direction="row" alignItems="center" justifyContent={"flex-end"} marginBottom={3}>
              {/* <Typography variant="h5" gutterBottom>
                Result Report
              </Typography> */}
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
                      <Typography sx={{ fontWeight: 500 }}>Export to Excel</Typography>
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
                      <Typography sx={{ fontWeight: 500 }}>Export to Word</Typography>
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
                      <Typography sx={{ fontWeight: 500 }}>Export to PDF</Typography>
                      <Typography variant="caption" color="text.secondary">
                        .pdf file
                      </Typography>
                    </ListItemText>
                  </MenuItem>
                </Menu>
              </Box>
            </Stack>
          </Box>

          {/* Sample Details */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Sample Details
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "repeat(2, 1fr)",
                gap: 2,
              }}
            >
              <Box>
                <Typography variant="body2">Flowcell ID</Typography>
                <Typography variant="body1">{report.sample.flowcell_id}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Cell Type</Typography>
                <Typography variant="body1">{report.sample.cell_type}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Cycle ID</Typography>
                <Typography variant="body1">{report.sample.cycle_id}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Reference Genome</Typography>
                <Typography variant="body1">{report.sample.reference_genome}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Embryo ID</Typography>
                <Typography variant="body1">{report.sample.embryo_id}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Date</Typography>
                <Typography variant="body1">{new Date(report.sample.date).toLocaleDateString()}</Typography>
              </Box>
            </Box>
          </Paper>

          {/* Algorithm Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Algorithm Details
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
                <Typography variant="body2">Name</Typography>
                <Typography variant="body1">{report.algorithm.name}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Version</Typography>
                <Typography variant="body1">{report.algorithm.version}</Typography>
              </Box>
            </Box>

            {report.algorithm.parameters.length > 0 && (
              <>
                <TableContainer>
                  <Table size="small" sx={{ tableLayout: "fixed" }}>
                    <colgroup>
                      <col style={{ width: "50%" }} />
                      <col style={{ width: "50%" }} />
                    </colgroup>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ pl: 0, pr: 1 }}>
                          <Typography variant="body2">Parameter</Typography>
                        </TableCell>
                        <TableCell sx={{ pl: 1, pr: 0 }}>
                          <Typography variant="body2">Value</Typography>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {report.algorithm.parameters.map((param, index) => (
                        <TableRow key={index}>
                          <TableCell sx={{ pl: 0, pr: 1 }}>
                            <Typography variant="body1">{param.name}</Typography>
                          </TableCell>
                          <TableCell sx={{ pl: 1, pr: 0 }}>
                            <Typography variant="body1">{JSON.stringify(param.value)}</Typography>
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
              Aberration Details
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* Aberration Summary */}
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2, mb: 3 }}>
              <Box>
                <Typography variant="body2">Aberration Summary</Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                  {report.aberration.aberration_summary && report.aberration.aberration_summary.length > 0 ? (
                    report.aberration.aberration_summary.map((summary, index) => <Chip key={index} label={summary} size="small" variant="outlined" />)
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      No summary
                    </Typography>
                  )}
                </Box>
              </Box>
              {report.aberration.aberration_segments.length > 0 && (
                <Box>
                  <Typography variant="body2">Number of Regions</Typography>
                  <Typography variant="body1">{report.aberration.aberration_segments.length}</Typography>
                </Box>
              )}
            </Box>

            {/* Aberration Segments */}
            {report.aberration.aberration_segments.length > 0 && (
              <>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ pl: 0 }}>
                          <Typography variant="body2">Chromosome</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Start</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">End</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Size (bp)</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Copy Number</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Type</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Mosaicism</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">Aberration</Typography>
                        </TableCell>
                        {/* <TableCell>
                          <Typography variant="body2">Assessment</Typography>
                        </TableCell> */}
                        {/* <TableCell>
                          <Typography variant="body2">Annotation</Typography>
                        </TableCell> */}
                        <TableCell>
                          <Typography variant="body2">Man Change</Typography>
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {report.aberration.aberration_segments.map((segment, index) => (
                        <TableRow key={index}>
                          <TableCell sx={{ pl: 0 }}>
                            <Typography variant="body1">{segment.chromosome}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{segment.start.toLocaleString()}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{segment.end.toLocaleString()}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{segment.size.toLocaleString()}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={segment.copy_number.toFixed(2)} size="small" color={segment.copy_number < 1.7 ? "error" : segment.copy_number > 2.3 ? "warning" : "success"} variant="outlined" sx={{ fontWeight: "normal" }} />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{segment.type}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{(segment.mosaicism * 100).toFixed(0)}%</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={segment.aberration_code} size="small" variant="outlined" sx={{ fontWeight: "normal" }} />
                          </TableCell>
                          {/* <TableCell>
                            <Typography variant="body1">{segment.assessment}</Typography>
                          </TableCell> */}
                          {/* <TableCell>
                            <Typography variant="body1">{segment.annotation_for_segment || "-"}</Typography>
                          </TableCell> */}
                          <TableCell>
                            <Typography variant="body1">{segment.man_change ? "Yes" : "No"}</Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {report.aberration.aberration_segments.length === 0 && <Typography color="text.secondary">No aberrations detected</Typography>}
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
          <Typography variant="body1" color="text.secondary">
            No result selected
          </Typography>
        </Box>
      )}
    </Box>
  );
};
