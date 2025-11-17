from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Response, Form
import traceback
from .service import RunnerService
import json

router = APIRouter()


@router.post("/{algorithm_id}/run")
def run_algorithm(
    algorithm_id: str,
    bam: UploadFile = File(...),
    input_data: str = Form(...),
    params: str = Form(...),
    input_cls: str = Form(...),
    exe_cls: str = Form(...),
):
    try:
        # Print all received parameters for debugging
        print("Algorithm ID:", algorithm_id)
        print("Running algorithm with data:", input_data)
        print("Parameters:", params)
        print("Input Class:", input_cls)
        print("Execution Class:", exe_cls)
        input_data_dict = json.loads(input_data)
        params_dict = json.loads(params)
        result = RunnerService.run_algorithm(
            algorithm_id=algorithm_id,
            input_cls=input_cls,
            exe_cls=exe_cls,
            bam=bam.file.read(),
            input_data=input_data_dict,
            **params_dict,
        )
        return result
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
