import { Box, Alert, Skeleton, Typography, Paper, Chip, Divider, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Stack, Button, Menu, MenuItem, ListItemIcon, ListItemText, SxProps, Theme } from "@mui/material";
import IosShareIcon from "@mui/icons-material/IosShare";
import DescriptionIcon from "@mui/icons-material/Description";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdf";
import GridOnIcon from "@mui/icons-material/GridOn";
import { CycleReportResponse } from "@/types/result";
import { useState } from "react";

interface CycleReportProps {
  loading: boolean;
  error: string | null;
  report: CycleReportResponse | null;
  exportToDocx: (report: CycleReportResponse) => void;
  exportToXlsx: (report: CycleReportResponse) => void;
  exportToPdf: (report: CycleReportResponse) => void;
  sx?: SxProps<Theme>;
}

export const CycleReport: React.FC<CycleReportProps> = ({ loading, error, report, exportToDocx, exportToXlsx, exportToPdf, sx }) => {
  const [exportAnchorEl, setExportAnchorEl] = useState<null | HTMLElement>(null);

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportAnchorEl(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportAnchorEl(null);
  };

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
          <Skeleton variant="rectangular" height={300} sx={{ mb: 2 }} />
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
                Cycle Report
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

          {/* Cycle Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Cycle Details
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: 2,
                mb: 2,
              }}
            >
              <Box>
                <Typography variant="body2">Flowcell ID</Typography>
                <Typography variant="body1">{report.flowcell_id}</Typography>
              </Box>
              <Box>
                <Typography variant="body2">Cycle ID</Typography>
                <Typography variant="body1">{report.cycle_id}</Typography>
              </Box>
            </Box>

            {/* <Typography variant="h6" gutterBottom>
              Embryo Overview
            </Typography> */}
            {/* <Divider sx={{ mb: 2 }} /> */}

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ pl: 0, pr: 1 }}>
                      <Typography variant="body2">Embryo ID</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">Cell Type</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">Call</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">Aberration Codes</Typography>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {report.embryos.map((embryo, index) => {
                    const aberrationCodes = embryo.abberations.map((a) => a.code).join(", ");
                    return (
                      <TableRow key={index}>
                        <TableCell sx={{ pl: 0, pr: 1 }}>
                          <Typography variant="body1">{embryo.embryo_id}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1">{embryo.cell_type}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={embryo.call} size="small" color={embryo.call.toLowerCase() === "normal" ? "success" : embryo.call.toLowerCase() === "abnormal" ? "error" : "warning"} variant="outlined" sx={{ fontWeight: "normal" }} />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1">
                            {aberrationCodes || (
                              <Typography variant="body2" color="text.secondary">
                                None
                              </Typography>
                            )}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          {/* Embryo Overview Table */}
          {/* <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}> */}

          {/* </Paper> */}

          {/* Aberration Details Table */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Aberration Details
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {report.embryos.some((e) => e.abberations.length > 0) ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ pl: 0, pr: 1 }}>
                        <Typography variant="body2">Embryo ID</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Aberration</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Mosaic</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Size (Mbp)</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Assessment</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">Diseases</Typography>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {report.embryos.flatMap((embryo) =>
                      embryo.abberations.map((aberration, aberrationIndex) => (
                        <TableRow key={`${embryo.embryo_id}-${aberrationIndex}`}>
                          <TableCell sx={{ pl: 0, pr: 1 }}>
                            <Typography variant="body1">{embryo.embryo_id}</Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={aberration.code} size="small" variant="outlined" sx={{ fontWeight: "normal" }} />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{(aberration.mosaic * 100).toFixed(0)}%</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{aberration.size != null ? aberration.size.toFixed(1) : "N/A"}</Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body1">{aberration.assessment || "Unknown"}</Typography>
                          </TableCell>
                          <TableCell>
                            {aberration.diseases && aberration.diseases.length > 0 ? (
                              <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                                {aberration.diseases.map((disease, idx) => (
                                  <Typography key={idx} variant="body1">
                                    {disease};
                                  </Typography>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="body1">No related disease detected</Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="text.secondary">No aberrations detected</Typography>
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
            No cycle report generated
          </Typography>
        </Box>
      )}
    </Box>
  );
};
