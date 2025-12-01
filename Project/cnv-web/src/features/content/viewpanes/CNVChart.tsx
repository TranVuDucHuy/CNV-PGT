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
  ReferenceArea,
} from "recharts";
import {
  Box,
  Paper,
  SxProps,
  Theme,
  Typography,
  useTheme,
  Button,
  Collapse,
  Divider,
  Stack,
} from "@mui/material";

// --- TYPES ---
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
  return <circle cx={cx} cy={cy} r={1.5} fill="#888888" opacity={0.6} />;
};

const DetailDot = (props: any) => {
  const { cx, cy } = props;
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
  return <circle cx={cx} cy={cy} r={3} fill="#ff9800" opacity={0.8} stroke="none" />;
};

const CNVChart: React.FC<CNVChartProps> = ({ bins, segments, title, sx }) => {
  const theme = useTheme();
  const [selectedChr, setSelectedChr] = useState<Chromosome | null>(null);

  // --- REFS CHO EXPORT ẢNH ---
  const mainChartRef = useRef<HTMLDivElement>(null);
  const detailChartRef = useRef<HTMLDivElement>(null);

  // --- HÀM EXPORT ẢNH ---
  const handleExportImage = async (ref: React.RefObject<HTMLDivElement | null>, fileName: string) => {
    if (!ref.current) return;
    try {
        // html2canvas sẽ tự động bỏ qua các element có thuộc tính data-html2canvas-ignore
        const canvas = await html2canvas(ref.current, {
            backgroundColor: "#ffffff",
            scale: 2, // Tăng độ phân giải cho ảnh nét hơn
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

  // 1. DATA MAIN CHART
  const { mainChartData, xTicks, xLines, xDomainMax } = useMemo(() => {
    let currentOffset = 0;
    const offsets: Record<string, number> = {};
    const ticks: { value: number; label: string }[] = [];
    const lines: number[] = [];
    const regions: { chr: Chromosome; start: number; end: number }[] = [];

    CHROMOSOME_ORDER.forEach((chr) => {
      offsets[chr] = currentOffset;
      const length = HG19_LENGTHS[chr] || 100000000;
      regions.push({ chr, start: currentOffset, end: currentOffset + length });
      ticks.push({ value: currentOffset + length / 2, label: chr });
      currentOffset += length;
      lines.push(currentOffset);
    });

    const pBins = bins
      .filter((b) => CHROMOSOME_ORDER.includes(b.chromosome))
      .map((b) => ({
        x: (offsets[b.chromosome] || 0) + b.start,
        y: b.copy_number,
        raw: b,
      }));

    const pSegments = processSegments(
      segments.filter((s) => CHROMOSOME_ORDER.includes(s.chromosome)), 
      offsets
    );

    return {
      mainChartData: { bins: pBins, segments: pSegments, regions },
      xTicks: ticks,
      xLines: lines,
      xDomainMax: currentOffset,
    };
  }, [bins, segments]);

  // 2. DATA DETAIL CHART
  const detailChartData = useMemo(() => {
    if (!selectedChr) return null;
    const chrBins = bins.filter((b) => b.chromosome === selectedChr).map(b => ({
        x: b.start, y: b.copy_number, raw: b
    }));
    const chrSegments = segments.filter((s) => s.chromosome === selectedChr);
    const pSegments = processSegments(chrSegments);
    const domainMax = HG19_LENGTHS[selectedChr] || 100000000;
    return { bins: chrBins, segments: pSegments, domainMax };
  }, [selectedChr, bins, segments]);

  const handleChrClick = (chr: Chromosome) => {
    setSelectedChr((prev) => (prev === chr ? null : chr));
  };

  return (
    <Paper elevation={3} sx={{ width: "100%", display: 'flex', flexDirection: 'column', ...sx }}>
      
      {/* --- CHART 1: MAIN (WHOLE GENOME) --- */}
      <Box sx={{ p: 2, pb: 1, flexShrink: 0, position: 'relative' }} ref={mainChartRef}> 
        
        {/* FIX: Thêm data-html2canvas-ignore vào Box chứa nút để html2canvas bỏ qua nó */}
        <Box 
            sx={{ position: 'absolute', right: 10, top: 10, zIndex: 10 }}
            data-html2canvas-ignore="true"
        >
             <Button 
                variant="outlined" 
                size="small"
                onClick={() => handleExportImage(mainChartRef, `Whole_Genome_CNV_${new Date().toISOString().slice(0,10)}.png`)}
                sx={{ fontSize: '0.65rem', minWidth: 'auto', p: '2px 8px', textTransform: 'none' }}
             >
                Export PNG
             </Button>
        </Box>

        {title && (
          <Typography variant="h6" align="center" gutterBottom sx={{ fontWeight: "bold" }}>
            {title}
          </Typography>
        )}
        <Typography variant="caption" display="block" align="center" sx={{ mb: 1, color: 'text.secondary' }}>
           (Click on a chromosome column to view details)
        </Typography>

        <Box sx={{ width: "100%", height: 400, minHeight: 400 }}>
          <ResponsiveContainer>
            <ComposedChart margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e0e0e0" />
              <XAxis
                dataKey="x" type="number" domain={[0, xDomainMax]}
                ticks={xTicks.map((t) => t.value)}
                tickFormatter={(val) => {
                   const tick = xTicks.find((t) => t.value === val);
                   return tick ? tick.label : "";
                }}
                allowDataOverflow interval={0} tick={{ fontSize: 10 }}
                label={{ value: "Chromosome", position: "insideBottom", offset: -10 }}
              />
              <YAxis dataKey="y" domain={[0, 4]} allowDataOverflow={false} label={{ value: "CN", angle: -90, position: "insideLeft" }} />
              
              <Tooltip cursor={{ strokeDasharray: "3 3" }} content={() => null} /> 

              {mainChartData.regions.map((region) => {
                const isSelected = selectedChr === region.chr;
                return (
                  <ReferenceArea
                    key={region.chr} x1={region.start} x2={region.end}
                    fill={isSelected ? theme.palette.primary.main : "transparent"}
                    fillOpacity={isSelected ? 0.15 : 0}
                    stroke={isSelected ? theme.palette.primary.main : "none"}
                    strokeOpacity={1} strokeWidth={2}
                    onClick={() => handleChrClick(region.chr)}
                    style={{ cursor: "pointer" }}
                    ifOverflow="visible"
                  />
                );
              })}

              {xLines.map((xVal, idx) => (<ReferenceLine key={`v-${idx}`} x={xVal} stroke="#d0d0d0" />))}
              <ReferenceLine y={2} stroke="gray" />
              
              <Scatter name="Bins" data={mainChartData.bins} shape={<MainDot />} isAnimationActive={false} />
              <Line type="linear" data={mainChartData.segments.gain} dataKey="y" stroke="#FF0000" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
              <Line type="linear" data={mainChartData.segments.loss} dataKey="y" stroke="#0000FF" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
              <Line type="linear" data={mainChartData.segments.normal} dataKey="y" stroke="#333333" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </Box>
      </Box>

      {/* --- CHART 2: DETAIL (SINGLE CHROMOSOME) --- */}
      <Collapse in={Boolean(selectedChr)} timeout="auto" unmountOnExit>
        
        <Divider />

        {selectedChr && detailChartData && (
            <Box sx={{ 
                p: 2, 
                position: 'relative', 
                width: "100%", 
                boxSizing: "border-box", 
                flexShrink: 0,
                bgcolor: "#ffffff", 
                borderTop: "1px solid rgba(0,0,0,0.05)",
                borderBottomLeftRadius: 4, 
                borderBottomRightRadius: 4,
            }} ref={detailChartRef}>
                
                {/* FIX: Thêm data-html2canvas-ignore vào Box chứa các nút */}
                <Box 
                    sx={{ position: 'absolute', right: 5, top: 5, zIndex: 10 }}
                    data-html2canvas-ignore="true"
                >
                     <Stack direction="row" spacing={1}>
                        <Button 
                            variant="outlined" 
                            size="small"
                            onClick={() => handleExportImage(detailChartRef, `Chr_${selectedChr}_CNV.png`)}
                            sx={{ fontSize: '0.65rem', minWidth: 'auto', p: '2px 8px', textTransform: 'none', bgcolor: 'white' }}
                        >
                            Export PNG
                        </Button>
                        <Button 
                            variant="text" 
                            color="error" 
                            onClick={() => setSelectedChr(null)}
                            sx={{ fontSize: '0.65rem', minWidth: 'auto', p: '2px 6px', lineHeight: 1 }}
                        >
                            Close [x]
                        </Button>
                     </Stack>
                </Box>

                <Box sx={{ width: "100%", height: 200, minHeight: 200, mt: 1 }}>
                    <ResponsiveContainer>
                    <ComposedChart margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#d0d0d0" />
                        <XAxis
                            dataKey="x" type="number"
                            domain={[0, detailChartData.domainMax]}
                            tickFormatter={(val) => `${(val / 1000000).toFixed(0)}M`}
                            allowDataOverflow
                            tick={{ fontSize: 10 }}
                            label={{ value: "Pos (bp)", position: "insideBottom", offset: -5, fontSize: 9 }}
                        />
                        <YAxis 
                            dataKey="y" 
                            domain={[0, 4]} 
                            tick={{ fontSize: 10 }}
                            label={{ value: "CN", angle: -90, position: "insideLeft", fontSize: 10 }} 
                        />

                        <Tooltip
                            cursor={{ strokeDasharray: "3 3" }}
                            content={({ active, payload }) => {
                                if (active && payload?.[0]?.payload?.raw) {
                                    const d = payload[0].payload.raw;
                                    return (
                                        <Paper sx={{ p: 0.5, border: "1px solid #ccc", opacity: 0.9 }}>
                                            <Typography variant="caption" display="block"><strong>Pos:</strong> {d.start}-{d.end}</Typography>
                                            <Typography variant="caption" display="block"><strong>CN:</strong> {d.copy_number.toFixed(3)}</Typography>
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
                        
                        <Line type="linear" data={detailChartData.segments.gain} dataKey="y" stroke="#FF0000" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                        <Line type="linear" data={detailChartData.segments.loss} dataKey="y" stroke="#0000FF" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                        <Line type="linear" data={detailChartData.segments.normal} dataKey="y" stroke="#333333" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
                    </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                <Typography 
                    variant="caption" 
                    align="center" 
                    display="block" 
                    sx={{ fontWeight: "bold", color: theme.palette.primary.main, mb: 0.5 }}
                >
                    Chromosome {selectedChr} Detail
                </Typography>
            </Box>
        )}
      </Collapse>
    </Paper>
  );
};

export default CNVChart;