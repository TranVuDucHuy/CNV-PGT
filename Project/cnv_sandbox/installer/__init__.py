from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .router import router as installer_router
import subprocess
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    runner_process = subprocess.Popen(["uvicorn", "runner:app", "--port", "8016"])
    app.state.runner_process = runner_process
    print("Started runner process:", runner_process)
    try:
        yield
    except asyncio.CancelledError:
        # Handle uvicorn shutdown gracefully
        print("⚠️ Lifespan cancelled — cleaning up...")
    finally:
        if app.state.runner_process:
            print("Terminating runner process...")
            app.state.runner_process.terminate()
            app.state.runner_process.wait()
            print("Runner process terminated.")


app = FastAPI(
    root_path="/api/v1", title="Sandbox API", version="1.0.0", lifespan=lifespan
)

app.include_router(installer_router, prefix="/installer")


@app.get("/")
def read_root(request: Request):

    return {"message": "Installer API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
