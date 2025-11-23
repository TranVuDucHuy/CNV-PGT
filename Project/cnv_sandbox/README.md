# Sandbox to run CNV-PGT algorithms safely

## `NOTE`: Better to run this in a virtual machine to avoid security risks.

## Setup Instructions

1. Create a conda environment:

   ```bash
   conda create -n cnv_sandbox python=3.13 -y
   conda activate cnv_sandbox
   ```

2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Start a Redis server (can be run by docker):

   ```bash
   docker run -d -p 6379:6379 redis
   ```

   Or use the docker-compose file:

   ```bash
   docker-compose up -d
   ```

4. Run the sandbox server:

   ```bash
   uvicorn main:app --reload --port=8001
   ```
