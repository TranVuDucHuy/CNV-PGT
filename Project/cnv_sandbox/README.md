# Sandbox to run algorithms

## Folder Structure

- `runner/`: Contains the separate Python Project to install and run algorithms.
- `sandbox/`: Contains the FastAPI application to interact with the runner.

## How to run?

You have two options to run the sandbox:

1. Using Docker (recommended):
   The compose file brings up three containers: the FastAPI sandbox API, the
   background runner worker, and Redis. Build and start everything with:

```bash
docker compose up --build
```

   After the containers are ready, access the sandbox endpoints at
   `http://localhost:8001/api/v1/sandbox`.

2. Manually:

- First, make sure that the 2 projects have environment and dependencies installed.
- Start Redis locally (or with Docker):

```bash
docker run --rm -p 6379:6379 redis:7
```

- In one terminal, run the `Redis Queue` worker inside the `runner/` project:

```bash
cd runner
pip install -r requirements.txt  # if not already installed
REDIS_HOST=localhost python main.py
```

Or go to `runner/main.py` and run the file directly.

- In another terminal, run the FastAPI application inside the `sandbox/` project:

```bash
cd sandbox
pip install -r requirements.txt  # if not already installed
REDIS_HOST=localhost uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Access the sandbox endpoints at `http://localhost:8001/api/v1/sandbox`.
