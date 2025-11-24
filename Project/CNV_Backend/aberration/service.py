import uuid
from collections import Counter
from typing import List
from sqlalchemy.orm import Session

from result.models import SampleSegment
from aberration.models import Aberration, AberrationSegment, AberrationType, AssessmentType
from common.models import Chromosome


DEFAULT_MOSAICISM_THRESHOLD = 0.3


class AberrationService:
    @staticmethod
    def generate_and_save_aberrations(result_id: str, db: Session) -> Aberration:
        segments = (
            db.query(SampleSegment)
            .filter(SampleSegment.result_id == result_id)
            .order_by(SampleSegment.chromosome, SampleSegment.start)
            .all()
        )

        chromosome_counts = Counter(segment.chromosome for segment in segments)
        aberration_segments = []

        for segment in segments:
            delta = abs(segment.copy_number - 2.0)
            rounded_mosaicism = round(delta, 1)
            if rounded_mosaicism < DEFAULT_MOSAICISM_THRESHOLD or segment.copy_number == 2.0:
                continue

            # Determine type
            if segment.copy_number > 2.0:
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
