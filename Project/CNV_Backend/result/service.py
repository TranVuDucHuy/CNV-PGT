import io
import csv
from typing import Iterator, Tuple
from sqlalchemy import select
from uuid import uuid4
from sqlalchemy.orm import Session
from .models import Result, SampleSegment, SampleBin
from algorithm.plugin import (
    BaseOutput,
    SampleSegment as AlgoSampleSegment,
    SampleBin as AlgoSampleBin,
)
from algorithm.models import Algorithm, AlgorithmParameter
from .schemas import ResultDto, ResultSummary
from common.models import ReferenceGenome, Chromosome
from sample.models import Sample

SEGMENT_EXPECTED = {"chromosome", "start", "end", "copy_number", "confidence"}
BIN_EXPECTED = {"chromosome", "start", "end", "copy_number", "read_count", "gc_content"}


def _parse_tsv_bytes(
    b: bytes, expected_cols: set, file_label: str
) -> Iterator[Tuple[int, dict]]:
    f = io.TextIOWrapper(io.BytesIO(b), encoding="utf-8")
    reader = csv.DictReader(f, delimiter="\t")
    if not reader.fieldnames:
        raise ValueError(f"{file_label}: missing header or empty file")
    headers = {h.strip() for h in reader.fieldnames}
    if not expected_cols.issubset(headers):
        missing = expected_cols - headers
        raise ValueError(f"{file_label}: missing columns {missing}")
    row_count = 0
    for i, raw in enumerate(reader, start=1):
        row = {
            k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()
        }
        row_count += 1
        yield i, row

    if row_count == 0:
        raise ValueError(f"{file_label}: no data rows found")


def _map_chromosome(value: str) -> Chromosome:
    """Map chromosome với các trường hợp (normalize & thử nhiều format)."""
    v = value.strip().removeprefix("chr").removeprefix("CHR")

    for resolver in (
        lambda: Chromosome(v),  # value-based
        lambda: Chromosome[v.upper()],  # name-based
        lambda: Chromosome(int(v)),  # numeric-based
    ):
        try:
            return resolver()
        except Exception:
            continue
    raise ValueError(f"Cannot map chromosome value '{value}' to Chromosome enum")


class ResultService:
    @staticmethod
    def add_from_files(
        db: Session,
        bins_tsv: bytes,
        segments_tsv: bytes,
        sample_name: str,
        algorithm_id: str,
        algorithm_parameter_id: str,
        reference_genome: str,
    ):
        # 0. Kiểm tra Algorithm và Sample tồn tại
        sample_obj = db.query(Sample).filter(Sample.name == sample_name).first()
        if not sample_obj:
            raise ValueError(f"Sample {sample_name} not found")

        alg = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not alg:
            raise ValueError(f"Algorithm {algorithm_id} not found")

        alg_param = (
            db.query(AlgorithmParameter)
            .filter(AlgorithmParameter.id == algorithm_parameter_id)
            .first()
        )
        if not alg_param:
            raise ValueError(f"AlgorithmParameter {algorithm_parameter_id} not found")

        # 1. Kiểm tra trùng
        existing = (
            db.query(Result)
            .filter(
                Result.sample_id == sample_name,
                Result.algorithm_id == algorithm_id,
                Result.algorithm_parameter_id == algorithm_parameter_id,
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Result for sample={sample_name}, algorithm={algorithm_id}, parameter={algorithm_parameter_id} already exists"
            )

        result_id = uuid4().hex

        # 2. Parse segments
        segments_objs: list[SampleSegment] = []
        for idx, row in _parse_tsv_bytes(segments_tsv, SEGMENT_EXPECTED, "segments"):
            try:
                chrom = _map_chromosome(row["chromosome"])
                start = int(row["start"])
                end = int(row["end"])
                copy_number = float(row["copy_number"])
                conf_raw = row.get("confidence", "")
                confidence = float(conf_raw) if conf_raw not in (None, "") else None
            except Exception as e:
                raise ValueError(f"segments line {idx}: {e}")

            segments_objs.append(
                SampleSegment(
                    id=uuid4().hex,
                    result_id=result_id,
                    chromosome=chrom,
                    start=start,
                    end=end,
                    copy_number=copy_number,
                    confidence=confidence,
                )
            )

        # 3. Parse bins
        bins_objs: list[SampleBin] = []
        for idx, row in _parse_tsv_bytes(bins_tsv, BIN_EXPECTED, "bins"):
            try:
                chrom = _map_chromosome(row["chromosome"])  # chromosome
                start = int(row["start"])  # start
                end = int(row["end"])  # end
                copy_number = float(row["copy_number"])  # copy_number
                read_count = int(row["read_count"])  # read_count
                gc_content = float(row["gc_content"])  # gc_content
            except Exception as e:
                raise ValueError(f"bins line {idx}: {e}")

            bins_objs.append(
                SampleBin(
                    id=uuid4().hex,
                    result_id=result_id,
                    chromosome=chrom,
                    start=start,
                    end=end,
                    copy_number=copy_number,
                    read_count=read_count,
                    gc_content=gc_content,
                )
            )

        # 4. Khởi tạo Result
        result = Result(
            id=result_id,
            sample_id=sample_name,
            algorithm_id=algorithm_id,
            algorithm_parameter_id=algorithm_parameter_id,
            reference_genome=ReferenceGenome(reference_genome),
        )
        result.segments = segments_objs
        result.bins = bins_objs

        # 6. Persist
        try:
            db.add(result)
            db.commit()
            db.refresh(result)
        except Exception:
            db.rollback()
            raise

        return result

    @staticmethod
    def add_from_algorithm_output(
        db: Session,
        sample_id: str,
        algorithm_id: str,
        algorithm_parameter_id: str,
        algorithm_output: dict,
    ):
        # Kiểm tra trùng
        existing = (
            db.query(Result)
            .filter(
                Result.sample_id == sample_id,
                Result.algorithm_id == algorithm_id,
                Result.algorithm_parameter_id == algorithm_parameter_id,
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Result for sample={sample_id}, algorithm={algorithm_id}, parameter={algorithm_parameter_id} already exists"
            )

        result = Result(
            id=uuid4().hex,
            sample_id=sample_id,
            algorithm_id=algorithm_id,
            algorithm_parameter_id=algorithm_parameter_id,
            reference_genome=ReferenceGenome(algorithm_output["reference_genome"]),
        )

        segments = [
            SampleSegment(
                id=uuid4().hex,
                chromosome=Chromosome(segment["chromosome"]),
                start=segment["start"],
                end=segment["end"],
                copy_number=segment["copy_number"],
                confidence=segment["confidence"],
            )
            for segment in algorithm_output["segments"]
        ]
        bins = [
            SampleBin(
                id=uuid4().hex,
                chromosome=Chromosome(bin["chromosome"]),
                start=bin["start"],
                end=bin["end"],
                copy_number=bin["copy_number"],
                read_count=bin["read_count"],
                gc_content=bin["gc_content"],
            )
            for bin in algorithm_output["bins"]
        ]

        result.segments = segments
        result.bins = bins

        db.add(result)
        db.commit()
        return result

    @staticmethod
    def delete(db: Session, result_id: str):
        result = db.query(Result).filter(Result.id == result_id).first()
        if result:
            db.delete(result)
            db.commit()
        else:
            raise ValueError(f"Result {result_id} not found")

    @staticmethod
    def get_all(db: Session) -> list[ResultSummary]:
        stmt = (
            select(
                Result.id,
                Sample.name.label("sample_name"),
                Algorithm.name.label("algorithm_name"),
                Result.reference_genome,
                Result.created_at.label("created_at"),
            )
            .join(Sample)
            .join(Algorithm)
            .order_by(Result.created_at.desc())
        )

        rows = db.execute(stmt).all()
        return [ResultSummary(**row._asdict()) for row in rows]

    def get(db: Session, result_id: str) -> ResultDto:
        stmt = (
            select(
                Result.id,
                Sample.name.label("sample_name"),
                Algorithm.name.label("algorithm_name"),
                Result.reference_genome,
                Result.created_at.label("created_at"),
            )
            .join(Sample)
            .join(Algorithm)
            .where(Result.id == result_id)
        )
        result = db.execute(stmt).first()
        if not result:
            raise ValueError(f"Result {result_id} not found")

        result_dict = result._asdict()

        # --- load segments and bins ---
        segment_rows = (
            db.query(
                SampleSegment.chromosome,
                SampleSegment.start,
                SampleSegment.end,
                SampleSegment.copy_number,
                SampleSegment.confidence,
            )
            .filter(SampleSegment.result_id == result_id)
            .all()
        )
        bin_rows = (
            db.query(
                SampleBin.chromosome,
                SampleBin.start,
                SampleBin.end,
                SampleBin.copy_number,
                SampleBin.read_count,
                SampleBin.gc_content,
            )
            .filter(SampleBin.result_id == result_id)
            .all()
        )

        result_dict["segments"] = [
            AlgoSampleSegment(**s._asdict()) for s in segment_rows
        ]
        result_dict["bins"] = [AlgoSampleBin(**b._asdict()) for b in bin_rows]

        return ResultDto(**result_dict)
