# How to run the CNV PGT Backend

- Set up a virtual environment (optional but recommended)

- Install the required dependencies:

```bash
pip install -r requirements.txt
```

- Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app
```

# How to upload an algorithm plugin

1. Create plugin:

   - Create `__init__.py`
   - Create metadata.json
   - Create a python file implementing the algorithm plugin. For example, see `plugin_example/algorithm.py`.
   - In the python file, `import` the necessary base classes from `algorithm` package.
   - In metadata.json, specify the input class, output class, and exe class in the format `module_name:ClassName`.
   - Include any additional files required by your plugin.

2. Zip the plugin files. Note: `Select All the files` when zipping, `NOT` the parent folder.

3. Use the `/algorithms` endpoint to upload the zipped plugin.

For example Microsoft PowerShell command to zip files:

```powershell
curl.exe -X POST -F "file=@plugin_example.zip" http://localhost:8000/api/v1/algorithms/
```

4. Test the uploaded plugin using the `/run_algorithm/{algorithm_name}` endpoint.

For example, enter this in your browser:

```
http://localhost:8000/api/v1/algorithms/plugin_example_1.0.0/run
```
