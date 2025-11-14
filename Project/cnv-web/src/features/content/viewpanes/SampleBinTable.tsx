import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from "@mui/material";

import { SampleBin } from "@/types/result";

type Props = {
  data: SampleBin[];
  dense?: boolean;
  onRowClick?: (row: SampleBin) => void;
};

export default function SampleBinTable({ data, dense = false, onRowClick }: Props) {
  return (
    <Paper>
      <TableContainer>
        <Table size={dense ? "small" : "medium"}>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Result ID</TableCell>
              <TableCell>Chromosome</TableCell>
              <TableCell align="right">Start</TableCell>
              <TableCell align="right">End</TableCell>
              <TableCell align="right">Copy #</TableCell>
              <TableCell align="right">Read Count</TableCell>
              <TableCell align="right">GC %</TableCell>
              <TableCell>Result Name</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {data.length === 0 && (
                <TableRow key="empty">
                <TableCell colSpan={9} align="center">
                    Không có dữ liệu
                </TableCell>
                </TableRow>
            )}

            {data.map((r, index) => (
                <TableRow
                key={r.id ?? `row-${index}`}  // ✅ fallback key
                hover
                onClick={() => onRowClick?.(r)}
                style={{ cursor: onRowClick ? "pointer" : "default" }}
                >
                <TableCell>{r.id}</TableCell>
                <TableCell>{r.result_id}</TableCell>
                <TableCell>
                    {typeof r.chromosome === "string"
                    ? r.chromosome
                    : JSON.stringify(r.chromosome)}
                </TableCell>
                <TableCell align="right">{r.start}</TableCell>
                <TableCell align="right">{r.end}</TableCell>
                <TableCell align="right">{r.copy_number}</TableCell>
                <TableCell align="right">{r.read_count}</TableCell>
                <TableCell align="right">{(r.gc_content * 100).toFixed(2)}%</TableCell>
                <TableCell>{r.result?.reference_genome}</TableCell>
                </TableRow>
            ))}
            </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}
