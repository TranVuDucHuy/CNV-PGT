from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    Request,
    Form,
)
import time

from fastapi.responses import StreamingResponse, JSONResponse
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from .service import ResultService
from .schemas import ResultSummary
from .schemas import ResultDto
from .schemas import ResultReportResponse
from common.schemas import BasicResponse
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/")
def upload_result(
    bins_tsv: UploadFile = File(...),
    segments_tsv: UploadFile = File(...),
    algorithm_id: str = Form(...),
    algorithm_parameter_id: str = Form(...),
    created_at: str = Form(None),
    db: Session = Depends(get_db),
):
    try:
        # basic filename checks
        seg_fname = segments_tsv.filename or ""
        bin_fname = bins_tsv.filename or ""
        if not (
            seg_fname.lower().endswith("_segments.tsv")
            and bin_fname.lower().endswith("_bins.tsv")
        ):
            raise ValueError(
                "Uploaded files must be named correctly with _segments.tsv and _bins.tsv suffixes."
            )

        sample_name = seg_fname.rsplit("_segments.tsv", 1)[0]

        bins_data = bins_tsv.file.read()
        segments_data = segments_tsv.file.read()
        result = ResultService.add_from_files(
            db=db,
            bins_tsv=bins_data,
            segments_tsv=segments_data,
            algorithm_parameter_id=algorithm_parameter_id,
            sample_name=sample_name,
            algorithm_id=algorithm_id,
            created_at=created_at,
        )

        return JSONResponse(
            status_code=201,
            content={"message": "Result uploaded successfully", "result_id": result.id},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error"
        )


@router.get("/", response_model=List[ResultSummary])
def get_all_results(db: Session = Depends(get_db)):
    results = ResultService.get_all(db=db)
    return results


@router.get("/{result_id}", response_model=ResultDto)
def get_result(result_id: str, db: Session = Depends(get_db)):
    try:
        result = ResultService.get(db=db, result_id=result_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{result_id}/report", response_model=ResultReportResponse)
def get_result_report(result_id: str, db: Session = Depends(get_db)):
    try:
        report = ResultService.get_mock_report(db=db, result_id=result_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{result_id}", response_model=BasicResponse)
def delete_result(result_id: str, db: Session = Depends(get_db)):
    try:
        ResultService.delete(db=db, result_id=result_id)
        return BasicResponse(message="Result deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
