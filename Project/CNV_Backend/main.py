from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sample
import algorithm
import result
import shutil
from pathlib import Path
import asyncio
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    plugin_dir = Path("plugins_runtime")
    plugin_dir.mkdir(exist_ok=True)
    (plugin_dir / "__init__.py").touch(exist_ok=True)
    app.state.plugin_dir = plugin_dir

    print(f"✅ Created plugin runtime dir: {plugin_dir}")

    try:
        yield
    except asyncio.CancelledError:
        # Handle uvicorn shutdown gracefully
        print("⚠️ Lifespan cancelled — cleaning up...")
    finally:
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir, ignore_errors=True)
            print(f"🧹 Cleaned up runtime dir: {plugin_dir}")


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CNV PGT Backend", root_path="/api/v1", lifespan=lifespan)


# CORS settings (allow Next.js dev server)
_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # WSL/Windows host-only network (Next.js shows this in terminal)
    # Add more origins via CORS_ALLOW_ORIGINS env (comma-separated)
]
_env_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()]
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
    return {"msg": "Welcome to the CNV PGT Backend!", "status": "running", "plugin_dir": str(request.app.state.plugin_dir)}