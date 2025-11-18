from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from .router import router as installer_router


app = FastAPI(root_path="/api/v1", title="Sandbox API", version="1.0.0")

app.include_router(installer_router, prefix="/sandbox")


@app.get("/")
def read_root(request: Request):

    return {"message": "Installer API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
