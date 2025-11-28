import React, { useMemo } from "react";
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
} from "@mui/material";

// --- TYPES (Theo yêu cầu của bạn) ---

import { Chromosome, SampleBin, SampleSegment } from "@/types/result";

// export interface ResultMinimal {
//     // Placeholder cho ResultMinimal nếu cần dùng
//     [key: string]: any;
// }

// --- CONSTANTS ---
// Thứ tự hiển thị nhiễm sắc thể trên trục X
const CHROMOSOME_ORDER: Chromosome[] = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "11",
  "12",
  "13",
  "14",
  "15",
  "16",
  "17",
  "18",
  "19",
  "20",
  "21",
  "22",
  "X",
  "Y",
];

// Độ dài tương đối của các NST (hg19) để tính toán offset hiển thị đẹp mắt
// Nếu dữ liệu thực tế lớn hơn, code sẽ tự động điều chỉnh based trên max end
const HG19_LENGTHS: Record<string, number> = {
  "1": 249250621,
  "2": 243199373,
  "3": 198022430,
  "4": 191154276,
  "5": 180915260,
  "6": 171115067,
  "7": 159138663,
  "8": 146364022,
  "9": 141213431,
  "10": 135534747,
  "11": 135006516,
  "12": 133851895,
  "13": 115169878,
  "14": 107349540,
  "15": 102531392,
  "16": 90354753,
  "17": 81195210,
  "18": 78077248,
  "19": 59128983,
  "20": 63025520,
  "21": 48129895,
  "22": 51304566,
  X: 155270560,
  Y: 59373566,
  MT: 16569,
};

interface CNVChartProps {
  bins: SampleBin[];
  segments: SampleSegment[];
  title?: string;
  sx?: SxProps<Theme>;
}

// --- HELPER COMPONENTS ---

// Custom shape cho điểm scatter để tối ưu hiệu năng hơn default circle của Recharts một chút
const CustomDot = (props: any) => {
  const { cx, cy } = props;
  return <circle cx={cx} cy={cy} r={1.5} fill="#888888" opacity={0.6} />;
};

const CNVChart: React.FC<CNVChartProps> = ({ bins, segments, title, sx }) => {
  const theme = useTheme();

  // 1. TÍNH TOÁN OFFSETS (Cộng dồn tọa độ trục X)
  // Để vẽ tất cả NST lên 1 trục, ta cần biết điểm bắt đầu của NST sau nằm ở đâu (bằng tổng độ dài các NST trước)
  const { processedBins, processedSegments, xTicks, xLines, xDomainMax } =
    useMemo(() => {
      let currentOffset = 0;
      const offsets: Record<string, number> = {};
      const ticks: { value: number; label: string }[] = [];
      const lines: number[] = []; // Vị trí kẻ vạch dọc phân chia NST

      CHROMOSOME_ORDER.forEach((chr) => {
        offsets[chr] = currentOffset;
        const length = HG19_LENGTHS[chr] || 100000000;

        // Label nằm giữa NST
        ticks.push({ value: currentOffset + length / 2, label: chr });

        currentOffset += length;
        // Vạch kẻ dọc nằm ở cuối NST
        lines.push(currentOffset);
      });

      // --- Xử lý Bins (Scatter points) ---
      const pBins = bins
        .filter((b) => CHROMOSOME_ORDER.includes(b.chromosome))
        .map((b) => ({
          x: (offsets[b.chromosome] || 0) + b.start,
          y: b.copy_number,
          raw: b, // Giữ data gốc để tooltip
        }));

      // --- Xử lý Segments (Lines) ---
      // Recharts Line chart cần dữ liệu liên tục. Để vẽ các đoạn rời rạc, ta dùng thủ thuật:
      // Thêm điểm null vào giữa các đoạn.
      // Phân loại segments để tô màu: Normal (đen), Gain (Đỏ), Loss (Xanh)
      const segNormal: any[] = [];
      const segGain: any[] = [];
      const segLoss: any[] = [];

      segments
        .filter((s) => CHROMOSOME_ORDER.includes(s.chromosome))
        .forEach((s) => {
          const startX = (offsets[s.chromosome] || 0) + s.start;
          const endX = (offsets[s.chromosome] || 0) + s.end;

          // Logic màu sắc dựa trên ảnh mẫu (ngưỡng tương đối)
          // > 2.5 là Gain (Đỏ), < 1.5 là Loss (Xanh), còn lại là bình thường
          let targetArray = segNormal;
          if (s.copy_number >= 2.3) targetArray = segGain;
          else if (s.copy_number <= 1.7) targetArray = segLoss;

          // Push điểm đầu và điểm cuối của segment
          targetArray.push({ x: startX, y: s.copy_number });
          targetArray.push({ x: endX, y: s.copy_number });
          // Push null để ngắt nét khi sang segment khác
          targetArray.push({ x: null, y: null });
        });

      return {
        processedBins: pBins,
        processedSegments: { normal: segNormal, gain: segGain, loss: segLoss },
        xTicks: ticks,
        xLines: lines,
        xDomainMax: currentOffset,
      };
    }, [bins, segments]);

  return (
    <Paper elevation={3} sx={{ p: 2, overflow: "auto", ...sx }}>
      {title && (
        <Typography
          variant="h6"
          align="center"
          gutterBottom
          sx={{ fontWeight: "bold", mb: 2 }}
        >
          {title}
        </Typography>
      )}

      <Box sx={{ width: "100%", height: 500 }}>
        <ResponsiveContainer>
          <ComposedChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            {/* --- GRID & AXES --- */}
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={true}
              vertical={false}
              stroke="#e0e0e0"
            />

            <XAxis
              dataKey="x"
              type="number"
              domain={[0, xDomainMax]}
              ticks={xTicks.map((t) => t.value)}
              tickFormatter={(val) => {
                const tick = xTicks.find((t) => t.value === val);
                return tick ? tick.label : "";
              }}
              allowDataOverflow
              interval={0} // Hiển thị tất cả label
              tick={{ fontSize: 10 }}
              label={{
                value: "Chromosome",
                position: "insideBottom",
                offset: -10,
              }}
            />

            <YAxis
              dataKey="y"
              domain={[0, 4]} // Theo ảnh mẫu: 0 -> 4
              allowDataOverflow={false}
              label={{
                value: "Copy number",
                angle: -90,
                position: "insideLeft",
              }}
            />

            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  // Ưu tiên hiển thị thông tin Segment nếu hover trúng
                  // Logic này tùy chỉnh dựa trên việc bạn muốn tooltip hiển thị gì
                  const data = payload[0].payload;
                  if (data.raw) {
                    // Đây là Bin
                    return (
                      <Paper sx={{ p: 1, border: "1px solid #ccc" }}>
                        <Typography variant="body2">
                          Chr: {data.raw.chromosome}
                        </Typography>
                        <Typography variant="body2">
                          Pos: {data.raw.start} - {data.raw.end}
                        </Typography>
                        <Typography variant="body2">
                          CN: {data.raw.copy_number.toFixed(2)}
                        </Typography>
                      </Paper>
                    );
                  }
                }
                return null;
              }}
            />

            {/* --- REFERENCE LINES (Các đường kẻ ngang/dọc) --- */}

            {/* Đường phân chia các nhiễm sắc thể */}
            {xLines.map((xVal, idx) => (
              <ReferenceLine
                key={`v-${idx}`}
                x={xVal}
                stroke="#d0d0d0"
                strokeWidth={1}
              />
            ))}

            {/* Đường Reference CN = 1, 2, 3 */}
            <ReferenceLine
              y={1}
              stroke="lightblue"
              strokeDasharray="3 3"
              label={{
                value: "1n",
                position: "right",
                fill: "gray",
                fontSize: 10,
              }}
            />
            <ReferenceLine
              y={2}
              stroke="gray"
              strokeWidth={1}
              label={{
                value: "2n",
                position: "right",
                fill: "gray",
                fontSize: 10,
              }}
            />
            <ReferenceLine
              y={3}
              stroke="pink"
              strokeDasharray="3 3"
              label={{
                value: "3n",
                position: "right",
                fill: "gray",
                fontSize: 10,
              }}
            />

            {/* --- DATA LAYERS --- */}

            {/* 1. BINS (Scatter Points) */}
            <Scatter
              name="Bins"
              data={processedBins}
              shape={<CustomDot />}
              isAnimationActive={false} // Tắt animation để render nhanh hơn với data lớn
            />

            {/* 2. SEGMENTS (Lines) */}
            {/* Normal Segments (Màu đen/xám đậm) */}
            <Line
              type="linear"
              data={processedSegments.normal}
              dataKey="y"
              stroke="#333333"
              strokeWidth={3}
              dot={false}
              connectNulls={false} // QUAN TRỌNG: Không nối các điểm null
              isAnimationActive={false}
            />

            {/* Gain Segments (Màu đỏ) */}
            <Line
              type="linear"
              data={processedSegments.gain}
              dataKey="y"
              stroke="#FF0000"
              strokeWidth={3}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />

            {/* Loss Segments (Màu xanh dương đậm) */}
            <Line
              type="linear"
              data={processedSegments.loss}
              dataKey="y"
              stroke="#0000FF"
              strokeWidth={3}
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Box>
    </Paper>
  );
};

export default CNVChart;
