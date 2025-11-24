from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sample
import algorithm
import result
import aberration
# Import models to register them with Base
from sample.models import Sample
from algorithm.models import Algorithm, AlgorithmParameter
from result.models import Result, SampleSegment, SampleBin
from aberration.models import Aberration, AberrationSegment, AberrationThreshold
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
import os


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CNV PGT Backend", root_path="/api/v1")


# CORS settings (allow Next.js dev server)
_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # WSL/Windows host-only network (Next.js shows this in terminal)
    # Add more origins via CORS_ALLOW_ORIGINS env (comma-separated)
]
_env_origins = [
    o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()
]
allow_origins = _default_origins + _env_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],  # fallback to * if nothing provided
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sample.router, prefix="/samples", tags=["samples"])
app.include_router(algorithm.router, prefix="/algorithms", tags=["algorithms"])
app.include_router(result.router, prefix="/results", tags=["results"])


@app.get("/")
def read_root(request: Request):
    return {
        "msg": "Welcome to the CNV PGT Backend!",
        "status": "running",
    }
