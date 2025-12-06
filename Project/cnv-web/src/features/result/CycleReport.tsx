import { Box, Alert, Skeleton, Typography, Paper, Chip, Divider, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, SxProps, Theme } from "@mui/material";
import { CycleReportResponse } from "@/types/result";

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
