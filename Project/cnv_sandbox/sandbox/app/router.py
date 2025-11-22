from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Response, Form
import traceback
from .service import SandboxService
import json
import subprocess

from redis_utils import connect_queue

router = APIRouter()


@router.post("/{algorithm_id}/zip")
def install_algorithm_zip(
    request: Request,
    algorithm_id: str,
    file: UploadFile = File(...),
):
    try:
        user_id = "root"  # In real scenario, extract from request/auth
        worker_process_pool = request.app.state.worker_process_pool
        queue_name = f"sandbox_queue_{user_id}"
        if user_id not in worker_process_pool:
            worker_process_pool[user_id] = subprocess.Popen(
                ["rq", "worker", queue_name],
            )
        runner_queue = connect_queue(
            redis_conn=request.app.state.redis_conn,
            queue_name=queue_name,
        )
        algorithm_zip = file.file.read()

        SandboxService.install_from_zip(
            algorithm_id=algorithm_id,
            algo_zip=algorithm_zip,
            runner_queue=runner_queue,
        )

        try:
            # Restart the worker process to update the installed packages
            worker_process_pool[user_id].terminate()
            worker_process_pool[user_id] = subprocess.Popen(
                ["rq", "worker", queue_name],
            )

            print(f"Worker process for user '{user_id}' restarted successfully.")
        except Exception as e:
            raise RuntimeError(
                f"Failed to restart worker process for user '{user_id}': {str(e)}\n"
                + "Running algorithms may fail until the worker is manually restarted."
            )

    except Exception as e:

        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Algorithm zip installed successfully"}


@router.post("/{algorithm_id}/run")
def run_algorithm(
    request: Request,
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

        user_id = "root"  # In real scenario, extract from request/auth
        worker_process_pool = request.app.state.worker_process_pool
        queue_name = f"sandbox_queue_{user_id}"
        if user_id not in worker_process_pool:
            worker_process_pool[user_id] = subprocess.Popen(
                ["rq", "worker", queue_name],
            )
        runner_queue = connect_queue(
            redis_conn=request.app.state.redis_conn,
            queue_name=queue_name,
        )
        result = SandboxService.run_algorithm(
            algorithm_id=algorithm_id,
            input_cls=input_cls,
            exe_cls=exe_cls,
            bam=bam.file.read(),
            input_data=input_data_dict,
            params=params_dict,
            runner_queue=runner_queue,
        )
        return result

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{algorithm_id}")
def uninstall_algorithm(
    request: Request,
    algorithm_id: str,
):
    try:
        user_id = "root"
        worker_process_pool = request.app.state.worker_process_pool
        queue_name = f"sandbox_queue_{user_id}"
        if user_id not in worker_process_pool:
            worker_process_pool[user_id] = subprocess.Popen(
                ["rq", "worker", queue_name],
            )
        runner_queue = connect_queue(
            redis_conn=request.app.state.redis_conn,
            queue_name=queue_name,
        )
        SandboxService.uninstall_algorithm(
            algorithm_id=algorithm_id, runner_queue=runner_queue
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Algorithm uninstalled successfully"}


@router.get("/{algorithm_id}/zip")
def download_algorithm_zip(
    algorithm_id: str,
):
    try:
        algo_zip = SandboxService.get_algorithm_zip(algorithm_id=algorithm_id)
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
