from fastapi import FastAPI
import sample

app = FastAPI(title="CNV PGT Backend", root_path="/api/v1")

app.include_router(sample.router, prefix="/samples", tags=["samples"])


@app.get("/")
def read_root():
    return {"msg": "Welcome to the CNV PGT Backend!"}
