from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List
from .service import AlgorithmService
from .schemas import (
    AlgorithmSummary,
    AlgorithmMetadata,
    RegisterAlgorithmResponse,
    AlgorithmDto,
)
from common.schemas import BasicResponse
from database import get_db
from sqlalchemy.orm import Session
import io
import traceback

router = APIRouter()


@router.get("/", response_model=List[AlgorithmSummary])
def get_all_algorithms(db: Session = Depends(get_db)):
    algorithms = AlgorithmService.get_all(db=db)
    return algorithms


@router.post("/", response_model=RegisterAlgorithmResponse)
def register_algorithm(
    algorithm_metadata: AlgorithmMetadata,
    db: Session = Depends(get_db),
):
    algorithm_id, algorithm_parameter_id = AlgorithmService.register(
        db=db,
        algorithm_metadata=algorithm_metadata,
    )
    return RegisterAlgorithmResponse(
        message="Algorithm registered successfully",
        algorithm_id=algorithm_id,
        algorithm_parameter_id=algorithm_parameter_id,
    )


@router.post("/{algorithm_id}/upload", response_model=BasicResponse)
def upload_algorithm_zip(
    request: Request,
    algorithm_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        algorithm_zip = file.file.read()
        AlgorithmService.save_zip(
            db=db,
            algorithm_id=algorithm_id,
            algorithm_zip=algorithm_zip,
        )
        print(f"✅ Algorithm {file.filename} uploaded successfully")
        return BasicResponse(message="Algorithm uploaded successfully")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{algorithm_id}/run")
def run_algorithm(
    algorithm_id: str,
    sample_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        input_data = {
            "sample_id": sample_id,
        }
        output = AlgorithmService.run(
            db=db,
            algorithm_id=algorithm_id,
            input_data=input_data,
        )
        return output
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{algorithm_id}", response_model=AlgorithmDto)
def get_algorithm_details(
    algorithm_id: str,
    db: Session = Depends(get_db),
):
    try:
        algorithm = AlgorithmService.get_by_id(db=db, algorithm_id=algorithm_id)
        return algorithm
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{algorithm_id}/download")
def download_algorithm(
    algorithm_id: str,
    db: Session = Depends(get_db),
):
    try:
        algorithm_zip = AlgorithmService.get_raw_algorithm_zip(
            db=db, algorithm_id=algorithm_id
        )
        return StreamingResponse(
            io.BytesIO(algorithm_zip), media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{algorithm_id}", response_model=BasicResponse)
def delete_algorithm(
    algorithm_id: str,
    db: Session = Depends(get_db),
):
    try:
        AlgorithmService.delete(db=db, algorithm_id=algorithm_id)
        return BasicResponse(message="Algorithm deleted successfully")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
