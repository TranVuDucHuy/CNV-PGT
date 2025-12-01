import io
import csv
from typing import Iterator, Tuple, Optional
from datetime import datetime
from sqlalchemy import select
from uuid import uuid4
from sqlalchemy.orm import Session, selectinload
from .models import Result, SampleSegment, SampleBin
from algorithm.plugin import (
    BaseOutput,
    SampleSegment as AlgoSampleSegment,
    SampleBin as AlgoSampleBin,
)
from algorithm.models import Algorithm, AlgorithmParameter
from aberration.models import Aberration
from .schemas import (
    ResultDto,
    ResultSummary,
    ResultReportResponse,
    SampleInfo,
    AlgorithmInfo,
    AlgorithmParameterInfo,
    AberrationInfo,
    AberrationSegmentInfo,
    AberrationSummary,
    EmbryoInfo,
    CycleReportResponse,
)
from common.models import Chromosome
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
        created_at: Optional[str] = None,
    ):
        # 0. Kiểm tra Algorithm và Sample tồn tại
        sample_obj = db.query(Sample).filter(Sample.name == sample_name).first()
        if not sample_obj:
            raise ValueError(f"Sample {sample_name} not found")

        alg = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not alg:
            raise ValueError(f"Algorithm {algorithm_id} not found")

        # Lấy parameter ID từ last_parameter_id của algorithm
        algorithm_parameter_id = alg.last_parameter_id
        if not algorithm_parameter_id:
            raise ValueError(f"Algorithm {algorithm_id} has no current parameters set")

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
            sample_id=sample_obj.id,
            algorithm_id=algorithm_id,
            algorithm_parameter_id=algorithm_parameter_id,
            reference_genome=sample_obj.reference_genome,
            created_at=created_at if created_at else datetime.now(),
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

        # 7. Generate and save aberrations
        try:
            from aberration.service import AberrationService

            AberrationService.generate_and_save_aberrations(result_id, db)
        except Exception as e:
            print(
                f"Warning: Could not generate aberrations for result {result_id}: {e}"
            )

        return result

    @staticmethod
    def add_from_algorithm_output(
        db: Session,
        sample_id: str,
        algorithm_id: str,
        algorithm_parameter_id: str,
        algorithm_output: dict,
    ):
        # Kiểm tra Sample tồn tại
        sample_obj = db.query(Sample).filter(Sample.id == sample_id).first()
        if not sample_obj:
            raise ValueError(f"Sample {sample_id} not found")

        alg = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not alg:
            raise ValueError(f"Algorithm {algorithm_id} not found")

        algorithm_parameter_id = alg.last_parameter_id
        if not algorithm_parameter_id:
            raise ValueError(f"Algorithm {algorithm_id} has no current parameters set")

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
            reference_genome=sample_obj.reference_genome,
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

        # Generate and save aberrations
        try:
            from aberration.service import AberrationService

            AberrationService.generate_and_save_aberrations(result.id, db)
        except Exception as e:
            print(
                f"Warning: Could not generate aberrations for result {result.id}: {e}"
            )

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

    @staticmethod
    def get_report(db: Session, result_id: str) -> ResultReportResponse:
        from aberration.models import Aberration, AberrationSegment

        # 1. Query Result
        result = db.query(Result).filter(Result.id == result_id).first()
        if not result:
            raise ValueError(f"Result {result_id} not found")

        # 2. Query Sample info
        sample = db.query(Sample).filter(Sample.id == result.sample_id).first()
        if not sample:
            raise ValueError(f"Sample {result.sample_id} not found")

        sample_info = SampleInfo(
            flowcell_id=sample.flowcell_id,
            cycle_id=sample.cycle_id,
            embryo_id=sample.embryo_id,
            cell_type=sample.cell_type.value,
            reference_genome=result.reference_genome.value,
            date=sample.date,
        )

        # 3. Query Algorithm and AlgorithmParameter info
        algorithm = (
            db.query(Algorithm).filter(Algorithm.id == result.algorithm_id).first()
        )
        if not algorithm:
            raise ValueError(f"Algorithm {result.algorithm_id} not found")

        algorithm_params = []
        if result.algorithm_parameter_id:
            alg_param = (
                db.query(AlgorithmParameter)
                .filter(AlgorithmParameter.id == result.algorithm_parameter_id)
                .first()
            )
            if alg_param:
                for param_name, param_detail in alg_param.value.items():
                    algorithm_params.append(
                        AlgorithmParameterInfo(
                            name=param_name,
                            type=param_detail.get("type", ""),
                            default=param_detail.get("default", None),
                            value=param_detail.get("value", None),
                        )
                    )

        algorithm_info = AlgorithmInfo(
            name=algorithm.name, version=algorithm.version, parameters=algorithm_params
        )

        # 4. Query Aberration info
        aberration = (
            db.query(Aberration).filter(Aberration.result_id == result_id).first()
        )

        aberration_summary = []
        aberration_segments = []

        if aberration:
            if aberration.aberration_summary:
                aberration_summary = aberration.aberration_summary

            segments = (
                db.query(AberrationSegment)
                .filter(AberrationSegment.aberration_id == aberration.id)
                .all()
            )

            for segment in segments:
                aberration_segments.append(
                    AberrationSegmentInfo(
                        chromosome=segment.chromosome.value,
                        start=segment.start,
                        end=segment.end,
                        copy_number=segment.copy_number,
                        confidence=segment.confidence,
                        size=segment.size,
                        type=segment.type.value,
                        mosaicism=segment.mosaicism,
                        aberration_code=segment.aberration_code,
                        assessment=segment.assessment.value,
                        annotation_for_segment=segment.annotation_for_segment,
                        man_change=segment.man_change,
                    )
                )

        aberration_info = AberrationInfo(
            aberration_summary=aberration_summary,
            aberration_segments=aberration_segments,
        )

        return ResultReportResponse(
            result_id=result_id,
            sample=sample_info,
            algorithm=algorithm_info,
            aberration=aberration_info,
        )

    @staticmethod
    def get_mock_report(db: Session, result_id: str) -> ResultReportResponse:
        # This is a mock implementation for testing purposes

        sample_info = SampleInfo(
            flowcell_id="FC123",
            cycle_id="C1",
            embryo_id="E456",
            cell_type="TypeA",
            reference_genome="GRCh38",
            date="2024-01-01",
        )

        algorithm_info = AlgorithmInfo(
            name="MockAlgorithm",
            version="1.0",
            parameters=[
                AlgorithmParameterInfo(name="param1", type="int", default=10, value=15)
            ],
        )

        aberration_info = AberrationInfo(
            aberration_summary=["Mock aberration summary"],
            aberration_segments=[
                AberrationSegmentInfo(
                    chromosome="1",
                    start=100000,
                    end=200000,
                    copy_number=2.5,
                    confidence=0.95,
                    size=100000,
                    type="deletion",
                    mosaicism=0.1,
                    aberration_code="DEL1",
                    assessment="pathogenic",
                    annotation_for_segment="Mock annotation",
                )
            ],
        )

        return ResultReportResponse(
            result_id=result_id,
            sample=sample_info,
            algorithm=algorithm_info,
            aberration=aberration_info,
        )

    @staticmethod
    def get_cycle_report(db: Session, report_ids: list[str]) -> CycleReportResponse:
        results = db.query(Result).filter(Result.id.in_(report_ids)).all()
        if not results:
            raise ValueError("No results found for the provided report IDs")

        sample_ids = [r.sample_id for r in results]
        samples = db.query(Sample).filter(Sample.id.in_(sample_ids)).distinct().all()

        if not samples:
            raise ValueError("No samples found for the provided report IDs")

        sample = samples[0]
        cycle_id = sample.cycle_id
        flowcell_id = sample.flowcell_id

        sample_map = {sample.id: sample}
        # Validate all samples belong to the same cycle and flowcell
        for i in range(1, len(samples)):
            sample = samples[i]
            if sample.cycle_id != cycle_id:
                raise ValueError("All samples must belong to the same cycle")
            if sample.flowcell_id != flowcell_id:
                raise ValueError("All samples must belong to the same flowcell")

            sample_map[sample.id] = sample

        aberrations = (
            db.execute(
                select(Aberration)
                .where(Aberration.result_id.in_(report_ids))
                .options(selectinload(Aberration.aberration_segments))
            )
            .scalars()
            .all()
        )

        aberration_result_map = {}
        for ab in aberrations:
            aberration_result_map[ab.result_id] = ab

        embryos = []
        for result in results:
            sample = sample_map[result.sample_id]
            aberration = aberration_result_map.get(result.id, None)

            abberations_summary = []
            if aberration:
                for segment in aberration.aberration_segments:
                    abberations_summary.append(
                        AberrationSummary(
                            code=segment.aberration_code,
                            mosaic=segment.mosaicism,
                            size=segment.size / 1_000_000,  # Convert to Mbp
                            diseases=segment.annotation_for_segment,
                            assessment=segment.assessment.value,
                        )
                    )
            embryos.append(
                EmbryoInfo(
                    embryo_id=sample.embryo_id,
                    cell_type=sample.cell_type.value,
                    call="Abnormal" if aberration else "Normal",
                    abberations=abberations_summary,
                )
            )

        return CycleReportResponse(
            cycle_id=cycle_id, flowcell_id=flowcell_id, embryos=embryos
        )

    @staticmethod
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
