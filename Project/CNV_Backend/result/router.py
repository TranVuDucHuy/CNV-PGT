from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from .service import ResultService
from .schemas import ResultSummary
from common.schemas import BasicResponse

router = APIRouter()


@router.post("/")
def upload_result(
    bins_tsv: UploadFile = File(...),
    segments_tsv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        bins_data = bins_tsv.file.read()
        segments_data = segments_tsv.file.read()
        ResultService.add_from_files(
            db=db, bins_tsv=bins_data, segments_tsv=segments_data
        )
        return BasicResponse(message="Result uploaded successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ResultSummary])
def get_all_results(db: Session = Depends(get_db)):
    results = ResultService.get_all(db=db)
    return results


@router.get("/{result_id}", response_model=ResultSummary)
def get_result(result_id: str, db: Session = Depends(get_db)):
    try:
        result = ResultService.get_by_id(db=db, result_id=result_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{result_id}", response_model=BasicResponse)
def delete_result(result_id: str, db: Session = Depends(get_db)):
    try:
        ResultService.delete_by_id(db=db, result_id=result_id)
        return BasicResponse(message="Result deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
