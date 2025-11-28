import React, { useMemo } from 'react';
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
} from 'recharts';
import { Box, Paper, Typography, useTheme } from '@mui/material';

// --- TYPES ---
import { Chromosome, SampleBin, SampleSegment } from '@/types/result';

// --- CONSTANTS ---
const CHROMOSOME_ORDER: Chromosome[] = [
  "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
  "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
  "21", "22", "X", "Y"
];

const HG19_LENGTHS: Record<string, number> = {
  "1": 249250621, "2": 243199373, "3": 198022430, "4": 191154276, "5": 180915260,
  "6": 171115067, "7": 159138663, "8": 146364022, "9": 141213431, "10": 135534747,
  "11": 135006516, "12": 133851895, "13": 115169878, "14": 107349540, "15": 102531392,
  "16": 90354753, "17": 81195210, "18": 78077248, "19": 59128983, "20": 63025520,
  "21": 48129895, "22": 51304566, "X": 155270560, "Y": 59373566, "MT": 16569
};

interface CNVChartProps {
  bins: SampleBin[];
  segments: SampleSegment[];
  title?: string;
}

// --- HELPER COMPONENTS ---
const CustomDot = (props: any) => {
  const { cx, cy } = props;
  // Chỉ vẽ nếu tọa độ hợp lệ
  if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
  return <circle cx={cx} cy={cy} r={1.5} fill="#888888" opacity={0.6} />;
};

const CNVChart: React.FC<CNVChartProps> = ({ bins, segments, title }) => {
  const theme = useTheme();

  const { processedBins, processedSegments, xTicks, xLines, xDomainMax } = useMemo(() => {
    let currentOffset = 0;
    const offsets: Record<string, number> = {};
    const ticks: { value: number; label: string }[] = [];
    const lines: number[] = [];

    CHROMOSOME_ORDER.forEach((chr) => {
      offsets[chr] = currentOffset;
      const length = HG19_LENGTHS[chr] || 100000000;
      ticks.push({ value: currentOffset + length / 2, label: chr });
      currentOffset += length;
      lines.push(currentOffset);
    });

    // --- Bins ---
    const pBins = bins
      .filter(b => CHROMOSOME_ORDER.includes(b.chromosome))
      .map(b => ({
        x: (offsets[b.chromosome] || 0) + b.start,
        y: b.copy_number,
        raw: b
      }));

    // --- Segments ---
    const segNormal: any[] = [];
    const segGain: any[] = [];
    const segLoss: any[] = [];

    segments
      .filter(s => CHROMOSOME_ORDER.includes(s.chromosome))
      .forEach(s => {
        const startX = (offsets[s.chromosome] || 0) + s.start;
        const endX = (offsets[s.chromosome] || 0) + s.end;
        
        let targetArray = segNormal;
        if (s.copy_number >= 2.3) targetArray = segGain;
        else if (s.copy_number <= 1.7) targetArray = segLoss;

        targetArray.push({ x: startX, y: s.copy_number });
        targetArray.push({ x: endX, y: s.copy_number });
        targetArray.push({ x: null, y: null });
      });

    return {
      processedBins: pBins,
      processedSegments: { normal: segNormal, gain: segGain, loss: segLoss },
      xTicks: ticks,
      xLines: lines,
      xDomainMax: currentOffset
    };
  }, [bins, segments]);

  return (
    // SỬA: Bỏ Box cứng width/height, dùng width/height 100%
    // Container bên ngoài (ContentPane) sẽ quyết định chiều cao
    <Box sx={{ width: '100%', height: '100%', minHeight: 0 }}> 
      {title && (
        <Typography variant="h6" align="center" gutterBottom sx={{ fontWeight: 'bold', mb: 1 }}>
          {title}
        </Typography>
      )}
      
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#e0e0e0" />
          
          <XAxis
            dataKey="x"
            type="number"
            domain={[0, xDomainMax]}
            ticks={xTicks.map(t => t.value)}
            tickFormatter={(val) => {
              const tick = xTicks.find(t => t.value === val);
              return tick ? tick.label : '';
            }}
            allowDataOverflow
            interval={0}
            tick={{ fontSize: 10 }}
            height={40} // Thêm height cho trục X để không bị cắt chữ
          />
          
          <YAxis
            dataKey="y"
            domain={[0, 4]}
            allowDataOverflow={false}
            width={40}
            tick={{ fontSize: 10 }}
          />

          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                if (data.raw) {
                   return (
                      <Paper sx={{ p: 1, border: '1px solid #ccc', zIndex: 9999 }}>
                         <Typography variant="caption" display="block">Chr: {data.raw.chromosome}</Typography>
                         <Typography variant="caption" display="block">Pos: {data.raw.start}</Typography>
                         <Typography variant="caption" display="block">CN: {data.raw.copy_number.toFixed(2)}</Typography>
                      </Paper>
                   )
                }
              }
              return null;
            }}
          />

          {xLines.map((xVal, idx) => (
            <ReferenceLine key={`v-${idx}`} x={xVal} stroke="#d0d0d0" strokeWidth={1} />
          ))}

          <ReferenceLine y={1} stroke="lightblue" strokeDasharray="3 3" />
          <ReferenceLine y={2} stroke="gray" strokeWidth={1} />
          <ReferenceLine y={3} stroke="pink" strokeDasharray="3 3" />

          <Scatter
            name="Bins"
            data={processedBins}
            shape={<CustomDot />}
            isAnimationActive={false}
          />

          <Line type="linear" data={processedSegments.normal} dataKey="y" stroke="#333333" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
          <Line type="linear" data={processedSegments.gain} dataKey="y" stroke="#FF0000" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
          <Line type="linear" data={processedSegments.loss} dataKey="y" stroke="#0000FF" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />

        </ComposedChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default CNVChart;