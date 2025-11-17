from fastapi import FastAPI
from .router import router as runner_router

app = FastAPI(root_path="/api/v1", title="Sandbox API", version="1.0.0")

app.include_router(runner_router, prefix="/runner")


@app.get("/")
def read_root():
    return {"message": "Runner API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
