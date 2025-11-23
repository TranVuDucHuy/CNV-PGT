# How to run the CNV PGT Backend

- Conda environment setup (recommended):

```bash
conda create -n cnv_backend python=3.13.3 -y # Or other version on your system
conda activate cnv_backend
```

- Select Intepreter as `cnv_backend` in your IDE (e.g., VSCode, PyCharm) to run and debug the code. For example with VSCode:

  - Open Command Palette (Ctrl+Shift+P)
  - Type and select `Python: Select Interpreter`
  - Choose `cnv_backend` from the list

- Install the required dependencies:

```bash
pip install -r requirements.txt
```

- Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

# Algorithm Plugin Instructions

## Metadata.json

```json
{
  "name": "CNV_PGT_Backend",
  "version": "1.0.0",
  "description": "Backend for CNV PGT analysis using FastAPI"
}
```
