from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import subprocess

from .router import router as installer_router
from redis_utils import connect_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_conn = connect_redis()
    worker_process_pool: dict[str, subprocess.Popen] = {}

    try:
        app.state.redis_conn = redis_conn
        app.state.worker_process_pool = worker_process_pool
        yield
    finally:
        redis_conn.close()
        for process in worker_process_pool.values():
            process.terminate()
        worker_process_pool.clear()


app = FastAPI(root_path="/api/v1", title="Sandbox API", lifespan=lifespan)

app.include_router(installer_router, prefix="/sandbox")


@app.get("/")
def read_root(request: Request):
    return {
        "message": "Installer API is running",
        "redis_connected": request.app.state.redis_conn.ping(),
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
