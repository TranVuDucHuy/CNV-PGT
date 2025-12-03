import React, { useMemo, useState, useRef } from "react";
import html2canvas from "html2canvas";
import {
  ComposedChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Line,
} from "recharts";
import {
  Box,
  Paper,
  SxProps,
  Theme,
  Typography,
  useTheme,
  Button,
  Stack,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  Divider,
  Slider
} from "@mui/material";
import { X } from "lucide-react";

// --- TYPES (Giữ nguyên) ---
import { Chromosome, SampleBin, SampleSegment } from "@/types/result";

// --- CONSTANTS ---
const CHROMOSOME_ORDER: Chromosome[] = [
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
  "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
  "21", "22", "X", "Y",
];

const HG19_LENGTHS: Record<string, number> = {
  "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276, "5": 180915260,
  "6": 171115067, "7": 159138663, "8": 146364022, "9": 141213431, "10": 135534747,
  "11": 135006516, "12": 133851895, "13": 115169878, "14": 107349540, "15": 102531392,
  "16": 90354753, "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
  "21": 48129895, "22": 51304566, X: 155270560, Y: 59373566, MT: 16569,
};

const WINDOW_SIZE = 4;

interface CNVChartProps {
  bins: SampleBin[];
  segments: SampleSegment[];
  title?: string;
  sx?: SxProps<Theme>;
}

// --- HELPER ---
const processSegments = (segments: SampleSegment[], offsetMap?: Record<string, number>) => {
  const segNormal: any[] = [];
  const segGain: any[] = [];
  const segLoss: any[] = [];

  if (!segments) return { normal: [], gain: [], loss: [] };

  segments.forEach((s) => {
    const currentOffset = offsetMap ? (offsetMap[s.chromosome] || 0) : 0;
    const startX = currentOffset + s.start;
    const endX = currentOffset + s.end;

    let targetArray = segNormal;
    if (s.copy_number >= 2.3) targetArray = segGain;
    else if (s.copy_number <= 1.7) targetArray = segLoss;

    targetArray.push({ x: startX, y: s.copy_number });
    targetArray.push({ x: endX, y: s.copy_number });
    targetArray.push({ x: null, y: null });
  });

  return { normal: segNormal, gain: segGain, loss: segLoss };
};

const MainDot = (props: any) => {
  const { cx, cy } = props;
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
  // Giảm kích thước dot nếu xem full chart để đỡ rối
  const r = props.isFullView ? 1 : 2; 
  return <circle cx={cx} cy={cy} r={r} fill="#888888" opacity={0.7} />;
};

const DetailDot = (props: any) => {
  const { cx, cy } = props;
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
  return <circle cx={cx} cy={cy} r={3} fill="#ff9800" opacity={0.8} stroke="none" />;
};

const CNVChart: React.FC<CNVChartProps> = ({ 
  bins = [], 
  segments = [], 
  title, 
  sx 
}) => {
  const theme = useTheme();
  
  // State
  const [selectedChr, setSelectedChr] = useState<Chromosome | null>(null);
  const [isFullView, setIsFullView] = useState<boolean>(false); // State mới: Check xem có đang xem Full Genome không
  const [windowStartIndex, setWindowStartIndex] = useState<number>(0);
  
  const chartContainerRef = useRef<HTMLDivElement>(null);

  const handleExportImage = async (fileName: string) => {
    if (!chartContainerRef.current) return;
    try {
      const canvas = await html2canvas(chartContainerRef.current, {
        backgroundColor: "#ffffff",
        scale: 2,
        ignoreElements: (element) => element.hasAttribute("data-html2canvas-ignore"),
      });
      const link = document.createElement("a");
      link.href = canvas.toDataURL("image/png");
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const handleDropdownChange = (event: SelectChangeEvent) => {
    const val = event.target.value;
    if (val === "WINDOW") {
      setSelectedChr(null);
      setIsFullView(false);
    } else if (val === "FULL") {
      setSelectedChr(null);
      setIsFullView(true);
    } else {
      setSelectedChr(val as Chromosome);
      setIsFullView(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedChr(null);
  };

  // Xác định giá trị hiển thị cho Select
  const currentSelectValue = selectedChr ? selectedChr : (isFullView ? "FULL" : "WINDOW");

  // --- 1. DATA MAIN CHART ---
  const { mainChartData, xTicks, xLines, xDomain } = useMemo(() => {
    if (selectedChr) return { mainChartData: null, xTicks: [], xLines: [], xDomain: [0, 0] };
    if (!bins || !segments) return { mainChartData: null, xTicks: [], xLines: [], xDomain: [0, 0] };

    // Logic: Nếu Full View thì lấy hết, ngược lại thì cắt theo window
    const visibleChromosomes = isFullView 
        ? CHROMOSOME_ORDER 
        : CHROMOSOME_ORDER.slice(windowStartIndex, windowStartIndex + WINDOW_SIZE);
    
    let globalOffset = 0;
    const offsets: Record<string, number> = {};
    const ticks: { value: number; label: string }[] = [];
    const lines: number[] = [];
    let minX = 0;
    let maxX = 0;
    let firstVisibleFound = false;

    CHROMOSOME_ORDER.forEach((chr) => {
      offsets[chr] = globalOffset;
      const length = HG19_LENGTHS[chr] || 100000000;
      
      if (visibleChromosomes.includes(chr)) {
        if (!firstVisibleFound) {
          minX = globalOffset;
          firstVisibleFound = true;
        }
        maxX = globalOffset + length;
        
        // Chỉ hiện label tick nếu không quá dày đặc (Full view thì có thể cần cân nhắc, nhưng ở đây cứ hiện hết)
        ticks.push({ value: globalOffset + length / 2, label: chr });
        lines.push(globalOffset + length); 
      }
      globalOffset += length;
    });

    const visibleBins = bins
      .filter((b) => visibleChromosomes.includes(b.chromosome))
      .map((b) => ({
        x: (offsets[b.chromosome] || 0) + b.start,
        y: b.copy_number,
        raw: b,
      }));

    const visibleSegmentsRaw = segments.filter((s) => visibleChromosomes.includes(s.chromosome));
    const processedSegments = processSegments(visibleSegmentsRaw, offsets);

    return {
      mainChartData: { bins: visibleBins, segments: processedSegments },
      xTicks: ticks,
      xLines: lines,
      xDomain: [minX, maxX],
    };
  }, [bins, segments, windowStartIndex, selectedChr, isFullView]);

  // --- 2. DATA DETAIL CHART ---
  const detailChartData = useMemo(() => {
    if (!selectedChr) return null;
    if (!bins || !segments) return null;

    const chrBins = bins.filter((b) => b.chromosome === selectedChr).map(b => ({
        x: b.start, y: b.copy_number, raw: b
    }));
    const chrSegments = segments.filter((s) => s.chromosome === selectedChr);
    const pSegments = processSegments(chrSegments);
    const domainMax = HG19_LENGTHS[selectedChr] || 100000000;
    return { bins: chrBins, segments: pSegments, domainMax };
  }, [selectedChr, bins, segments]);

  return (
    <Paper 
        elevation={3} 
        sx={{ width: "100%", display: 'flex', flexDirection: 'column', height: 'fit-content', ...sx }}
    >
      {/* --- HEADER --- */}
      <Box sx={{ p: 2, pb: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 160 }}>
                <InputLabel id="chr-select-label">View</InputLabel>
                <Select
                    labelId="chr-select-label"
                    value={currentSelectValue}
                    label="View"
                    onChange={handleDropdownChange}
                    // SỬA: Thêm MenuProps để giới hạn chiều cao dropdown
                    MenuProps={{
                        PaperProps: {
                            sx: {
                                maxHeight: 300, // Giới hạn chiều cao danh sách xổ xuống
                            },
                        },
                    }}
                >
                    <MenuItem value="WINDOW">Overview (Windowed)</MenuItem>
                    <MenuItem value="FULL">Overview (Full Genome)</MenuItem>
                    <Divider />
                    {CHROMOSOME_ORDER.map(chr => (
                        <MenuItem key={chr} value={chr}>Chromosome {chr}</MenuItem>
                    ))}
                </Select>
            </FormControl>

            {title && <Typography variant="h6" sx={{ fontWeight: "bold" }}>{title}</Typography>}
        </Stack>

        <Box>
            <Button 
                variant="outlined" 
                size="small"
                onClick={() => handleExportImage(selectedChr ? `Chr_${selectedChr}_CNV.png` : `Genomic_CNV.png`)}
                sx={{ textTransform: 'none' }}
            >
                Export PNG
            </Button>
        </Box>
      </Box>

      {/* --- CONTENT --- */}
      <Box sx={{ p: 2 }} ref={chartContainerRef}>
        
        {/* --- MAIN CHART (Windowed OR Full) --- */}
        {!selectedChr && mainChartData && (
            <>
                <Box sx={{ width: "100%", height: 250 }}>
                    <ResponsiveContainer>
                        <ComposedChart margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
                            <XAxis
                                dataKey="x" type="number" 
                                domain={xDomain as [number, number]}
                                ticks={xTicks.map((t) => t.value)}
                                tickFormatter={(val) => {
                                    const tick = xTicks.find((t) => t.value === val);
                                    return tick ? tick.label : "";
                                }}
                                allowDataOverflow interval={0} 
                                // Nếu Full view thì font bé lại chút để đỡ chồng chéo
                                tick={{ fontSize: isFullView ? 10 : 12, fontWeight: 'bold' }}
                            />
                            <YAxis dataKey="y" domain={[0, 4]} allowDataOverflow={false} label={{ value: "CN", angle: -90, position: "insideLeft" }} />
                            {xLines.map((xVal, idx) => (<ReferenceLine key={`v-${idx}`} x={xVal} stroke="#d0d0d0" strokeDasharray="5 5" />))}
                            <ReferenceLine y={2} stroke="gray" />
                            
                            {/* Truyền prop isFullView vào MainDot để chỉnh kích thước điểm */}
                            <Scatter name="Bins" data={mainChartData.bins} shape={<MainDot isFullView={isFullView} />} isAnimationActive={false} />
                            <Line type="step" data={mainChartData.segments.gain} dataKey="y" stroke="#FF0000" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                            <Line type="step" data={mainChartData.segments.loss} dataKey="y" stroke="#0000FF" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                            <Line type="step" data={mainChartData.segments.normal} dataKey="y" stroke="#333333" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                {/* --- SLIDER (Chỉ hiện khi KHÔNG PHẢI Full View) --- */}
                {!isFullView && (
                    <Stack 
                        spacing={2} 
                        direction="row" 
                        alignItems="center" 
                        data-html2canvas-ignore="true"
                        sx={{ px: 4, pt: 1, pb: 0.5 }} 
                    >
                        <Typography variant="caption" sx={{ minWidth: 35, textAlign: 'right' }}>Chr {CHROMOSOME_ORDER[0]}</Typography>
                        
                        <Slider
                            value={windowStartIndex}
                            min={0}
                            max={CHROMOSOME_ORDER.length - WINDOW_SIZE}
                            step={1}
                            onChange={(_, val) => setWindowStartIndex(val as number)}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(val) => `Chr ${CHROMOSOME_ORDER[val]}`}
                            marks={false} 
                            sx={{
                                color: 'primary.main',
                                height: 16, 
                                padding: 0, 
                                '& .MuiSlider-thumb': {
                                    height: 16, width: 16,
                                    backgroundColor: '#fff',
                                    border: '2px solid currentColor',
                                    borderRadius: '4px', 
                                    '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': { boxShadow: 'inherit' },
                                    '&::before': { display: 'none' },
                                },
                                '& .MuiSlider-track': { border: 'none', borderRadius: 0, height: 16 },
                                '& .MuiSlider-rail': { opacity: 0.3, backgroundColor: '#bfbfbf', borderRadius: 0, height: 16 },
                            }}
                        />
                        
                        <Typography variant="caption" sx={{ minWidth: 35 }}>Chr {CHROMOSOME_ORDER[CHROMOSOME_ORDER.length - 1]}</Typography>
                    </Stack>
                )}
                
                <Typography variant="caption" align="center" display="block" sx={{ mt: 0.5, color: 'text.secondary' }}>
                    {isFullView 
                        ? "Showing Full Genome (1-22, X, Y)" 
                        : `Showing: Chr ${CHROMOSOME_ORDER[windowStartIndex]} - ${CHROMOSOME_ORDER[windowStartIndex + WINDOW_SIZE - 1]}`
                    }
                </Typography>
            </>
        )}

        {/* --- DETAIL CHART --- */}
        {selectedChr && detailChartData && (
            <Box sx={{ position: 'relative' }}>
                <Box sx={{ position: 'absolute', right: 0, top: -10, zIndex: 10 }} data-html2canvas-ignore="true">
                     <Button startIcon={<X size={16}/>} variant="text" color="error" size="small" onClick={handleCloseDetail}>
                        Close View
                    </Button>
                </Box>

                 <Typography variant="h6" align="center" sx={{ color: theme.palette.primary.main, mb: 1 }}>
                    Chromosome {selectedChr} Detail
                </Typography>

                <Box sx={{ width: "100%", height: 250 }}>
                    <ResponsiveContainer>
                    <ComposedChart margin={{ top: 5, right: 30, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d0d0d0" />
                        <XAxis
                            dataKey="x" type="number"
                            domain={[0, detailChartData.domainMax]}
                            tickFormatter={(val) => `${(val / 1000000).toFixed(0)}Mb`}
                            allowDataOverflow
                            tick={{ fontSize: 11 }}
                            label={{ value: "Position (bp)", position: "insideBottom", offset: -10 }}
                        />
                        <YAxis dataKey="y" domain={[0, 4]} tick={{ fontSize: 11 }} label={{ value: "CN", angle: -90, position: "insideLeft" }} />
                        <Tooltip
                            cursor={{ strokeDasharray: "3 3" }}
                            content={({ active, payload }) => {
                                if (active && payload?.[0]?.payload?.raw) {
                                    const d = payload[0].payload.raw;
                                    return (
                                        <Paper sx={{ p: 1, border: "1px solid #ccc", opacity: 0.95 }}>
                                            <Typography variant="subtitle2">Chr {d.chromosome}</Typography>
                                            <Divider sx={{ my: 0.5 }} />
                                            <Typography variant="caption" display="block"><strong>Start:</strong> {d.start.toLocaleString()}</Typography>
                                            <Typography variant="caption" display="block"><strong>End:</strong> {d.end.toLocaleString()}</Typography>
                                            <Typography variant="body2" display="block" sx={{ mt: 0.5, color: 'primary.main' }}>
                                                <strong>CN: {d.copy_number.toFixed(3)}</strong>
                                            </Typography>
                                        </Paper>
                                    );
                                }
                                return null;
                            }}
                        />
                        <ReferenceLine y={1} stroke="lightblue" strokeDasharray="3 3"/>
                        <ReferenceLine y={2} stroke="gray" strokeWidth={1} />
                        <ReferenceLine y={3} stroke="pink" strokeDasharray="3 3"/>

                        <Scatter name="Bins" data={detailChartData.bins} shape={<DetailDot />} isAnimationActive={false} />
                        <Line type="step" data={detailChartData.segments.gain} dataKey="y" stroke="#FF0000" strokeWidth={3} dot={false} connectNulls={false} isAnimationActive={false} />
                        <Line type="step" data={detailChartData.segments.loss} dataKey="y" stroke="#0000FF" strokeWidth={3} dot={false} connectNulls={false} isAnimationActive={false} />
                        <Line type="step" data={detailChartData.segments.normal} dataKey="y" stroke="#333333" strokeWidth={3} dot={false} connectNulls={false} isAnimationActive={false} />
                    </ComposedChart>
                    </ResponsiveContainer>
                </Box>
            </Box>
        )}
      </Box>
    </Paper>
  );
};

export default CNVChart;