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

export const CycleReport: React.FC<CycleReportProps> = ({
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
            <Stack
              direction="row"
              alignItems="center"
              justifyContent={"space-between"}
            >
              <Typography variant="h5" gutterBottom>
                Cycle Report
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
          </Box>

          {/* Cycle Information */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Cycle Information
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
                <Typography variant="body1">{report.flowcell_id}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Cycle ID
                </Typography>
                <Typography variant="body1">{report.cycle_id}</Typography>
              </Box>
            </Box>
          </Paper>

          {/* Embryo Overview Table */}
          <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom>
              Embryo Overview
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <strong>Embryo ID</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Cell Type</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Call</strong>
                    </TableCell>
                    <TableCell>
                      <strong>Aberration Codes</strong>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {report.embryos.map((embryo, index) => {
                    const aberrationCodes = embryo.abberations
                      .map((a) => a.code)
                      .join(", ");
                    return (
                      <TableRow key={index}>
                        <TableCell>{embryo.embryo_id}</TableCell>
                        <TableCell>{embryo.cell_type}</TableCell>
                        <TableCell>
                          <Chip
                            label={embryo.call}
                            size="small"
                            color={
                              embryo.call.toLowerCase().includes("normal")
                                ? "success"
                                : embryo.call.toLowerCase().includes("abnormal")
                                ? "error"
                                : "warning"
                            }
                          />
                        </TableCell>
                        <TableCell>
                          {aberrationCodes || (
                            <Typography color="text.secondary">None</Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

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
                      <TableCell>
                        <strong>Embryo ID</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Aberration</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Mosaic</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Size (Mbp)</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Diseases</strong>
                      </TableCell>
                      <TableCell>
                        <strong>Assessment</strong>
                      </TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {report.embryos.flatMap((embryo) =>
                      embryo.abberations.map((aberration, aberrationIndex) => (
                        <TableRow
                          key={`${embryo.embryo_id}-${aberrationIndex}`}
                        >
                          <TableCell>{embryo.embryo_id}</TableCell>
                          <TableCell>
                            <Chip label={aberration.code} size="small" />
                          </TableCell>
                          <TableCell>
                            {(aberration.mosaic * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell>
                            {aberration.size != null
                              ? aberration.size.toFixed(2)
                              : "N/A"}
                          </TableCell>
                          <TableCell>
                            {aberration.diseases &&
                            aberration.diseases.length > 0
                              ? aberration.diseases.join(", ")
                              : "N/A"}
                          </TableCell>
                          <TableCell>
                            {aberration.assessment || "N/A"}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
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
            No cycle report generated
          </Typography>
        </Box>
      )}
    </Box>
  );
};
