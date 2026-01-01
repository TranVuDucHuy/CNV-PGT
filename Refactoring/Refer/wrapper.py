"""
WisecondorXPlugin implements huycnv.AlgorithmPlugin interface for the WisecondorX CNV pipeline
located under Exe/Code.

Responsibilities:
- Consume WisecondorXInput (bam bytes)
- Materialize BAM into a temp working area
- Run the existing WisecondorX pipeline against /Plugin working tree layout
- Standardize outputs into WisecondorXOutput (segments, bins)
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Any, Dict
import pysam
import argparse

import numpy as np
import pandas as pd

try:
    # Import interface types from huycnv package
    from huycnv import AlgorithmPlugin, BaseInput, BaseOutput, SampleBin, SampleSegment
except Exception:  # pragma: no cover - allow running without huycnv installed for local dev
    from pydantic import BaseModel
    from abc import ABC, abstractmethod

    class SampleSegment(BaseModel):
        chromosome: str
        start: int
        end: int
        copy_number: float
        confidence: float

    class SampleBin(BaseModel):
        chromosome: str
        start: int
        end: int
        copy_number: float
        read_count: int
        gc_content: float

    class BaseOutput(BaseModel):
        reference_genome: str
        segments: List[SampleSegment]
        bins: List[SampleBin]

    class BaseInput(BaseModel):
        bam: bytes

    class AlgorithmPlugin(ABC):
        @abstractmethod
        def run(self, data: BaseInput, **kwargs) -> BaseOutput: ...


class WisecondorXInput(BaseInput):
    # These attributes are optional. When not provided, plugin will look for files on disk.
    test: List[Any] = []
    reference: List[Any] = []


class WisecondorXOutput(BaseOutput):
    pass


class WisecondorXPlugin(AlgorithmPlugin):
    def __init__(self) -> None:
        self.plugin_root = Path(__file__).resolve().parent
        print(f"Plugin root directory: {self.plugin_root}")
        
        self.run_dir = self.plugin_root / "Exe" / "Run"
        self.input_run = self.run_dir / "Input"
        self.test_run = self.input_run / "Test"
        self.train_run = self.input_run / "Train"

        self.test_run.mkdir(parents=True, exist_ok=True)
        self.train_run.mkdir(parents=True, exist_ok=True)
    
    def _write_inline_sample(self, name: str, bam_bytes: bytes, dest_dir: Path) -> Path:
        """Write an inline BAM to destination folder with sane name and always ensure .bai is created."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        filename = name if name.lower().endswith('.bam') else f"{name}.bam"
        out_path = dest_dir / filename
        with open(out_path, 'wb') as f:
            f.write(bam_bytes)

        print(f"Indexing BAM: {out_path}")
        pysam.index(str(out_path))
        return out_path

    def _collect_bins(self, bins_bed: Path) -> List[SampleBin]:
        bins: List[SampleBin] = []
        if not bins_bed.exists():
            print(f"Warning: bins file not found: {bins_bed}")
            return bins
        
        df = pd.read_csv(bins_bed, sep="\t")
        for _, row in df.iterrows():
            ratio = row.get("ratio")
            # Skip nan values
            if pd.isna(ratio):
                continue
            
            chrom = str(row.get("chr", ""))
            start = int(row.get("start", 0))
            end = int(row.get("end", start))
            cn = float(2.0 ** (float(ratio) + 1.0))
            
            bins.append(
                SampleBin(
                    chromosome=chrom,
                    start=start,
                    end=end,
                    copy_number=cn,
                    read_count=0,  # placeholder
                    gc_content=0.0,  # placeholder
                )
            )
        return bins

    def _collect_segments(self, segments_bed: Path) -> List[SampleSegment]:
        segments: List[SampleSegment] = []
        if not segments_bed.exists():
            print(f"Warning: segments file not found: {segments_bed}")
            return segments
        
        df = pd.read_csv(segments_bed, sep="\t")
        for _, row in df.iterrows():
            chrom = str(row.get("chr", ""))
            start = int(row.get("start", 0))
            end = int(row.get("end", start))
            ratio = float(row.get("ratio", 0.0))
            zscore = float(row.get("zscore", 0.0))
            cn = float(2.0 ** (ratio + 1.0))
            
            segments.append(
                SampleSegment(
                    chromosome=chrom,
                    start=start,
                    end=end,
                    copy_number=cn,
                    confidence=zscore,
                )
            )
        return segments

    def _convert_to_tsv(self, sample_name: str, segments: List[SampleSegment], bins: List[SampleBin]) -> None:
        """Write segments and bins to TSV files in the Output directory."""
        output_dir = self.plugin_root / "Output"
        output_dir.mkdir(parents=True, exist_ok=True)        
        if sample_name.endswith("_S93"):
            sample_name = sample_name[:-4]

        seg_tsv = output_dir / f"{sample_name}_segments.tsv"
        with open(seg_tsv, "w", newline="") as fh:
            fh.write("chromosome\tstart\tend\tcopy_number\tconfidence\n")
            for s in segments:
                chrom = getattr(s, "chromosome", "")
                start = getattr(s, "start", "")
                end = getattr(s, "end", "")
                cn = getattr(s, "copy_number", "")
                conf = getattr(s, "confidence", "")
                fh.write(f"{chrom}\t{start}\t{end}\t{cn}\t{conf}\n")

        bins_tsv = output_dir / f"{sample_name}_bins.tsv"
        with open(bins_tsv, "w", newline="") as fh:
            fh.write("chromosome\tstart\tend\tcopy_number\tread_count\tgc_content\n")
            for b in bins:
                chrom = getattr(b, "chromosome", "")
                start = getattr(b, "start", "")
                end = getattr(b, "end", "")
                cn = getattr(b, "copy_number", "")
                rc = getattr(b, "read_count", "")
                gc = getattr(b, "gc_content", "")
                fh.write(f"{chrom}\t{start}\t{end}\t{cn}\t{rc}\t{gc}\n")

    def _cleanup_run_dirs(self) -> None:
        """Remove all files from run directories before processing."""
        dirs_to_clean = [
            self.test_run,
            self.train_run,
            self.run_dir / "Output",
            self.run_dir / "Temporary" / "Test",
            self.run_dir / "Temporary" / "Train",
        ]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                for file in dir_path.glob("*"):
                    if file.is_file():
                        file.unlink()
                        print(f"Removed: {file}")
                    elif file.is_dir():
                        # Remove subdirectories recursively
                        shutil.rmtree(file)
                        print(f"Removed directory: {file}")
            else:
                dir_path.mkdir(parents=True, exist_ok=True)

    def run(self, data: WisecondorXInput, **kwargs) -> WisecondorXOutput:
        # Clean up temporary directories before running
        self._cleanup_run_dirs()

        # Materialize inputs into run directory layout.
        # Priority: inline lists (test/reference) > single BaseInput.bam > external Input/*
        wrote_test = False
        wrote_ref = False

        # 1) Inline multiple test/reference samples (preferred in backend mode)
        if hasattr(data, 'test') and data.test:
            for i, s in enumerate(data.test, start=1):
                name = getattr(s, 'name', f'test_{i}')
                bam_bytes = getattr(s, 'bam', None)
                if not bam_bytes:
                    continue
                self._write_inline_sample(str(name), bam_bytes, self.test_run)
                wrote_test = True

        if hasattr(data, 'reference') and data.reference:
            for i, s in enumerate(data.reference, start=1):
                name = getattr(s, 'name', f'ref_{i}')
                bam_bytes = getattr(s, 'bam', None)
                if not bam_bytes:
                    continue
                self._write_inline_sample(str(name), bam_bytes, self.train_run)
                wrote_ref = True

        # 2) Single inline BAM (legacy BaseInput.bam)
        if not wrote_test and getattr(data, 'bam', None):
            self._write_inline_sample('F12345678-C123-E1', data.bam, self.test_run)
            wrote_test = True

        # 3) External files already present under plugin root (dev/local mode)
        if not wrote_test:
            external_test = self.plugin_root / "Input" / "Test"
            if external_test.exists():
                for bam in sorted(external_test.glob("*.bam")):
                    target = self.test_run / bam.name
                    if not target.exists():
                        shutil.copy2(bam, target)
                    pysam.index(str(target))
                wrote_test = any(self.test_run.glob('*.bam'))

        if not wrote_ref:
            external_ref = self.plugin_root / "Input" / "Reference"
            if external_ref.exists():
                for bam in sorted(external_ref.glob("*.bam")):
                    target = self.train_run / bam.name
                    if not target.exists():
                        shutil.copy2(bam, target)
                    pysam.index(str(target))
                wrote_ref = any(self.train_run.glob('*.bam'))

        # Run wisecondorx.py as subprocess
        wisecondorx_script = self.plugin_root / "Exe" / "Code" / "wisecondorx.py"
        cmd = [
            "python",
            str(wisecondorx_script),
            "-o", str(self.run_dir),
        ]
        
        print(f"Running WisecondorX pipeline: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(self.plugin_root / "Exe" / "Code"), capture_output=False)
        if result.returncode != 0:
            raise RuntimeError(f"WisecondorX pipeline failed with exit code {result.returncode}")

        # Collect outputs from run_dir/Output/<sample_id>/
        out_dir = self.run_dir / "Output"
        
        # Find all sample directories
        sample_dirs = [d for d in out_dir.iterdir() if d.is_dir()]
        if not sample_dirs:
            raise RuntimeError("No sample output directories found in run Output")

        processed = []  # list of tuples (sample_name, segments, bins)

        for sample_dir in sample_dirs:
            sample_name = sample_dir.name
            
            # Look for _bins.bed and _segments.bed files
            bins_bed = sample_dir / f"{sample_name}_bins.bed"
            segments_bed = sample_dir / f"{sample_name}_segments.bed"
            
            bins_i = self._collect_bins(bins_bed)
            segments_i = self._collect_segments(segments_bed)

            try:
                self._convert_to_tsv(sample_name, segments_i, bins_i)
            except Exception as e:
                print(f"Warning: failed to write TSV artifacts for {sample_name}: {e}")

            processed.append((sample_name, segments_i, bins_i))

        # Return first sample's output
        if processed:
            first_name, first_segments, first_bins = processed[0]
            return WisecondorXOutput(reference_genome="GRCh37", segments=first_segments, bins=first_bins)
        else:
            # Return empty output if no samples processed
            return WisecondorXOutput(reference_genome="GRCh37", segments=[], bins=[])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run WisecondorX CNV plugin")
    parser.add_argument("--params", required=False, default="{}", help="JSON string with params")
    parser.add_argument("--glob", action="store_true", help="Use glob mode to process all BAMs in Input/Test")

    args = parser.parse_args()
    # Working directory is plugin root (backend mounts input to /Plugin/Input)
    workdir = Path(__file__).resolve().parent
    output_root = workdir / "Output"
    output_root.mkdir(parents=True, exist_ok=True)

    # Parse parameters
    try:
        params: Dict[str, Any] = json.loads(args.params or "{}")
    except Exception as e:
        print(f"Failed to parse --params, using defaults: {e}")
        params = {}

    # Create empty WisecondorXInput (WisecondorXPlugin will source BAMs from Input/)
    base_input = WisecondorXInput(bam=b"")

    # Running WisecondorXPlugin ...
    plugin = WisecondorXPlugin()
    try:
        output_model = plugin.run(base_input, **params)
    except Exception as exc:
        print(f"Plugin run failed: {exc}")
        raise

    out_json = output_root / "result.json"
    try:
        data_dict = output_model.model_dump()  # type: ignore[attr-defined]
    except Exception:
        try:
            data_dict = output_model.dict()  # type: ignore[attr-defined]
        except Exception:
            data_dict = json.loads(json.dumps(output_model, default=lambda o: getattr(o, "__dict__", str(o))))

    out_json.write_text(json.dumps(data_dict, indent=2))
    print(f"Wrote standardized output: {out_json}")

    print("Done.")


if __name__ == "__main__":
    main()
