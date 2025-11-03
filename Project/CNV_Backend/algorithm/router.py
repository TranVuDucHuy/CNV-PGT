from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List
from .service import AlgorithmService
from .schemas import BasicResponse, AlgorithmSummary
from database import get_db
from sqlalchemy.orm import Session
import io

router = APIRouter()


@router.get("/", response_model=List[AlgorithmSummary])
def get_all_algorithms(db: Session = Depends(get_db)):
    algorithms = AlgorithmService.get_all(db=db)
    return algorithms


@router.post("/", response_model=BasicResponse)
def upload_algorithm(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        algorithm_zip = file.file.read()
        AlgorithmService.save(
            db=db, plugin_dir=request.app.state.plugin_dir, algorithm_zip=algorithm_zip
        )
        print(f"✅ Algorithm {file.filename} uploaded successfully")
        return BasicResponse(message="Algorithm uploaded successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{algorithm_id}/run")
def run_algorithm(
    algorithm_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    input_data = {
        "sample_id": "324e7f24-e9c4-4b3e-99af-5cad6e716f1d",
        "params_id": "f1f948ba095241e1a55aa72e643d0c5b",
        "input_1": "example_input",
        "input_2": 42,
    }
    output = AlgorithmService.run(
        db=db,
        plugin_dir=request.app.state.plugin_dir,
        algorithm_id=algorithm_id,
        input_data=input_data,
    )
    return output


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
