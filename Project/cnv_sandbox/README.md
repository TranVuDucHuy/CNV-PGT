# Sandbox Service to run installed algorithms

## Installation

### Docker Setup

Simply using docker compose up will build and start the service.

```bash
docker compose up --build
```

### Running Locally

1. Go to `main.py` and run the file directly to start the service.
2. Use `uvicorn`

```bash
uvicorn installer:app --port=8001
```

## API Endpoints

### Install Algorithm from Zip

- **Endpoint:** `POST /sandbox/{algorithm_id}/zip`
- **Description:** Installs an algorithm from a provided zip file.
