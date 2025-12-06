import uuid
from collections import Counter
from typing import List
from sqlalchemy.orm import Session
import subprocess
import os
import csv
from pathlib import Path

from result.models import SampleSegment
from aberration.models import Aberration, AberrationSegment, AberrationType, AssessmentType
from common.models import Chromosome
from sample.models import Sample


DEFAULT_MOSAICISM_THRESHOLD = 0.3


class AberrationService:
    @staticmethod
    def generate_and_save_aberrations(result_id: str, db: Session) -> Aberration:
        # Get segments and result info
        segments = (
            db.query(SampleSegment)
            .filter(SampleSegment.result_id == result_id)
            .order_by(SampleSegment.chromosome, SampleSegment.start)
            .all()
        )
        
        # Get result and sample for annotation
        from result.models import Result
        result = db.query(Result).filter(Result.id == result_id).first()
        sample = db.query(Sample).filter(Sample.id == result.sample_id).first()

        chromosome_counts = Counter(segment.chromosome for segment in segments)
        inferred_sex = AberrationService._infer_sex_from_segments(segments)
        aberration_segments = []

        for segment in segments:
            expected_cn = AberrationService._expected_copy_number(segment.chromosome, inferred_sex)
            delta = abs(segment.copy_number - expected_cn)
            rounded_mosaicism = round(delta, 1)
            if rounded_mosaicism < DEFAULT_MOSAICISM_THRESHOLD:
                continue

            # Determine type
            if segment.copy_number > expected_cn:
                aberration_type = AberrationType.GAIN
                type_symbol = "+"
            else:
                aberration_type = AberrationType.LOSS
                type_symbol = "-"

            # Build aberration code
            structure_suffix = "s" if chromosome_counts[segment.chromosome] > 1 else ""
            aberration_code = f"{type_symbol}{segment.chromosome.value}{structure_suffix}"

            # Calculate size
            size = segment.end - segment.start

            # Create aberration segment record
            aberration_segment = AberrationSegment(
                id=str(uuid.uuid4()),
                chromosome=segment.chromosome,
                start=segment.start,
                end=segment.end,
                copy_number=segment.copy_number,
                confidence=segment.confidence,
                size=size,
                type=aberration_type,
                mosaicism=rounded_mosaicism,
                aberration_code=aberration_code,
                assessment=AssessmentType.UNKNOWN,
                annotation_for_segment=None,
                man_change=False,
            )
            
            aberration_segments.append(aberration_segment)

        aberration_codes = [seg.aberration_code for seg in aberration_segments]
        aberration = Aberration(
            id=str(uuid.uuid4()),
            result_id=result_id,
            aberration_summary=aberration_codes,
            aberration_segments=aberration_segments,
        )

        # Save to database
        db.add(aberration)
        db.commit()
        
        return aberration

    @staticmethod
    def _weighted_average_copy_number(segments: List[SampleSegment]) -> float | None:
        total_length = 0
        weighted_sum = 0.0

        for segment in segments:
            length = max(segment.end - segment.start, 1)
            weighted_sum += segment.copy_number * length
            total_length += length

        if total_length == 0:
            return None

        return weighted_sum / total_length

    @staticmethod
    def _infer_sex_from_segments(segments: List[SampleSegment]) -> str:
        y_segments = [segment for segment in segments if segment.chromosome == Chromosome.CHR_Y]
        avg_y = AberrationService._weighted_average_copy_number(y_segments)

        if avg_y is None:
            return "unknown"

        if avg_y < DEFAULT_MOSAICISM_THRESHOLD:
            return "female"

        return "male"

    @staticmethod
    def _expected_copy_number(chromosome: Chromosome, inferred_sex: str) -> float:
        if inferred_sex == "female":
            if chromosome == Chromosome.CHR_X:
                return 2.0
            if chromosome == Chromosome.CHR_Y:
                return 0.0
        elif inferred_sex == "male":
            if chromosome in (Chromosome.CHR_X, Chromosome.CHR_Y):
                return 1.0

        return 2.0

    @staticmethod
    def annotate_result(result_id: str, db: Session) -> Aberration:
        # Ensure aberration exists
        aberration = db.query(Aberration).filter(Aberration.result_id == result_id).first()
        if not aberration:
            aberration = AberrationService.generate_and_save_aberrations(result_id, db)

        # Load result/sample
        from result.models import Result

        result = db.query(Result).filter(Result.id == result_id).first()
        if not result:
            raise ValueError(f"Result {result_id} not found")

        sample = db.query(Sample).filter(Sample.id == result.sample_id).first()
        if not sample:
            raise ValueError(f"Sample {result.sample_id} not found")

        # Query segments for this aberration
        segments = (
            db.query(AberrationSegment)
            .filter(AberrationSegment.aberration_id == aberration.id)
            .order_by(AberrationSegment.chromosome, AberrationSegment.start)
            .all()
        )

        for seg in segments:
            try:
                annotation, assessment = AberrationService.annotate_aberration_segment(seg, sample)
                seg.annotation_for_segment = annotation
                seg.assessment = assessment
                db.add(seg)
                db.commit()
            except Exception as e:
                print(f"Error annotating segment {seg.id}: {e}")
                db.rollback()

        db.refresh(aberration)
        return aberration

    @staticmethod
    def annotate_aberration_segment(segment: AberrationSegment, sample: Sample) -> tuple[list[dict] | None, AssessmentType]:
        # Setup workspace path
        workspace_dir = Path(__file__).parent.parent / "annotsv_workspace"
        bed_file = workspace_dir / "aberration.bed"
        tsv_output = workspace_dir / "aberration.annotated.tsv"
        annotations_dir = workspace_dir / "AnnotSV_annotations"
        
        try:
            # Clean up old files
            bed_file.unlink(missing_ok=True)
            tsv_output.unlink(missing_ok=True)
            
            # Create BED file
            sv_type = "DUP" if segment.type == AberrationType.GAIN else "DEL"
            chrom = str(segment.chromosome.value)
            
            with open(bed_file, "w") as f:
                f.write("chrom\tstart\tend\tSV_type\tSample_ID\n")
                f.write(f"{chrom}\t{segment.start}\t{segment.end}\t{sv_type}\t{segment.id}\n")
            
            # Determine genome build
            genome_build = "GRCh37" if "hg19" in sample.reference_genome.value else "GRCh38"
            
            # Run AnnotSV
            cmd = [
                "micromamba", "run", "-n", "cnv_annotsv",
                "AnnotSV",
                "-annotationsDir", str(annotations_dir),
                "-SVinputFile", str(bed_file),
                "-genomeBuild", genome_build,
                "-svtBEDcol", "4",
                "-samplesidBEDcol", "5",
                "-outputFile", str(tsv_output)
            ]
            
            result = subprocess.run(cmd, cwd=str(workspace_dir), check=True, capture_output=True, text=True)
            
            # Parse AnnotSV output
            omim_annotations: list[dict] = []
            assessment = AssessmentType.UNKNOWN

            if tsv_output.exists():
                with open(tsv_output, "r") as f:
                    reader = csv.DictReader(f, delimiter="\t")

                    for idx, row in enumerate(reader):
                        omim_id = row.get("OMIM_ID", "")
                        omim_phenotype = row.get("OMIM_phenotype", "")

                        if omim_id and omim_phenotype:
                            omim_annotations.append({
                                "OMIM_ID": omim_id,
                                "OMIM_phenotype": omim_phenotype,
                            })

                        if idx == 0:
                            acmg_class = row.get("ACMG_class", "NA")
                            assessment = AberrationService._map_acmg_to_assessment(acmg_class)

            return (omim_annotations if omim_annotations else None, assessment)
            
        except subprocess.CalledProcessError as e:
            print(f"Error running AnnotSV: {e.stderr}")
            raise
        except Exception as e:
            print(f"Error annotating segment {segment.id}: {e}")
            raise
    
    @staticmethod
    def _map_acmg_to_assessment(acmg_class: str) -> AssessmentType:
        acmg_str = str(acmg_class).strip()
        
        if "NA" in acmg_str:
            return AssessmentType.ARTEFACT
        elif "5" in acmg_str:
            return AssessmentType.PATHOGENIC
        elif "4" in acmg_str:
            return AssessmentType.PROBABLY_PATHOGENIC
        elif "3" in acmg_str:
            return AssessmentType.UNKNOWN
        elif "2" in acmg_str:
            return AssessmentType.PROBABLY_BENIGN
        elif "1" in acmg_str:
            return AssessmentType.BENIGN
        else:
            return AssessmentType.UNKNOWN
