from sqlalchemy import select
from uuid import uuid4
from sqlalchemy.orm import Session
from .models import Result, SampleSegment, SampleBin, Chromosome, ReferenceGenome
from algorithm.plugin import (
    BaseOutput,
    SampleSegment as AlgoSampleSegment,
    SampleBin as AlgoSampleBin,
)
from algorithm.models import Algorithm
from .schemas import ResultDto, ResultSummary


class ResultService:
    @staticmethod
    def add_from_files(db: Session, bins_tsv: bytes, segments_tsv: bytes):
        # Implementation for adding a Result with associated bins and segments
        pass

    @staticmethod
    def add_from_algorithm_output(
        db: Session,
        sample_id: str,
        algorithm_id: str,
        algorithm_output: BaseOutput,
    ):
        result = Result(
            id=f"{sample_id}_{algorithm_id}",
            sample_id=sample_id,
            algorithm_id=algorithm_id,
            reference_genome=ReferenceGenome(algorithm_output.reference_genome),
        )

        segments = [
            SampleSegment(
                id=uuid4().hex,
                result_id=result.id,
                chromosome=Chromosome(segment.chromosome),
                start=segment.start,
                end=segment.end,
                copy_number=segment.copy_number,
                confidence=segment.confidence,
                result=result,
            )
            for segment in algorithm_output.segments
        ]
        bins = [
            SampleBin(
                id=uuid4().hex,
                result_id=result.id,
                chromosome=Chromosome(bin.chromosome),
                start=bin.start,
                end=bin.end,
                copy_number=bin.copy_number,
                read_count=bin.read_count,
                gc_content=bin.gc_content,
                result=result,
            )
            for bin in algorithm_output.bins
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
                Result.sample_id,
                Algorithm.name.label("algorithm_name"),
                Result.reference_genome,
                Result.uploaded_at.label("created_at"),
            )
            .join(Algorithm)
            .order_by(Result.uploaded_at.desc())
        )

        rows = db.execute(stmt).all()
        return [ResultSummary(**row._asdict()) for row in rows]

    def get(db: Session, result_id: str) -> ResultDto:
        stmt = (
            select(
                Result.id,
                Result.sample_id,
                Algorithm.name.label("algorithm_name"),
                Result.reference_genome,
                Result.uploaded_at.label("created_at"),
            )
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
