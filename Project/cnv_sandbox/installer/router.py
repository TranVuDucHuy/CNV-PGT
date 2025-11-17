from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Response, Form
import traceback
from .service import InstallerService
import json
import subprocess

router = APIRouter()


@router.post("/{algorithm_id}/zip")
def install_algorithm_zip(
    algorithm_id: str,
    request: Request,
    file: UploadFile = File(...),
):
    try:
        algorithm_zip = file.file.read()
        InstallerService.install_from_zip(
            algorithm_id=algorithm_id, algo_zip=algorithm_zip
        )

        # Restart the runner service to load the new algorithm
        runner_process = request.app.state.runner_process
        print("Runner process in root endpoint:", runner_process)
        if runner_process:
            print("Restarting runner process...")
            runner_process.terminate()
            runner_process.wait()
        runner_process = subprocess.Popen(["uvicorn", "runner:app", "--port", "8016"])
        request.app.state.runner_process = runner_process
        print("New runner process started:", runner_process)

    except Exception as e:

        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Algorithm zip installed successfully"}


@router.delete("/{algorithm_id}")
def uninstall_algorithm(
    algorithm_id: str,
):
    try:
        InstallerService.uninstall_algorithm(algorithm_id=algorithm_id)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Algorithm uninstalled successfully"}


@router.get("/{algorithm_id}/zip")
def download_algorithm_zip(
    algorithm_id: str,
):
    try:
        algo_zip = InstallerService.get_algorithm_zip(algorithm_id=algorithm_id)
        return Response(content=algo_zip, media_type="application/zip")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/git")
def install_algorithm_git(
    algorithm_id: str,
    git_url: str,
):
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/run-cmd")
def run_command(
    command: str,
):
    raise HTTPException(status_code=501, detail="Not implemented yet")
