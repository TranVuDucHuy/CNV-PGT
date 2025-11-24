FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python-is-python3


WORKDIR /app
COPY . .


# Sandbox venv
WORKDIR /app/sandbox
COPY sandbox/requirements.txt .
RUN python3 -m venv /app/sandbox/.venv 
RUN /app/sandbox/.venv/bin/pip install --upgrade pip setuptools wheel build
RUN /app/sandbox/.venv/bin/pip install -r requirements.txt

EXPOSE 8001
CMD ["/app/sandbox/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
