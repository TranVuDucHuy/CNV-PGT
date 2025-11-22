import os
from pathlib import Path
import zipfile
import io
from config import SandboxConfig
import json
import shutil
import time
import subprocess

from utils.module_utils import modulize_name
from redis_utils import connect_queue


PYPROJECT_TEMPLATE = """
[project]
name = "{name}"
version = "{version}"
requires-python = ">=3.9"
dependencies = {dependencies}

[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {{"" = "src"}}

[tool.setuptools.packages.find]
where = ["src"]
include = ["*"]
"""


class SandboxService:
    @staticmethod
    def install_from_zip(
        algorithm_id: str,
        algo_zip: bytes,
        runner_queue,
    ):
        """Install an algorithm from a zip file.
        The zip file should contain a metadata.json file with at least the following fields:
        - version: str
        - dependencies: List[str] (optional)

        If the zip does not contain a pyproject.toml or setup.py, a basic pyproject.toml will be created.
        Finally, the algorithm will be installed in editable mode using pip.

        Args:
            algorithm_id (str): The unique identifier for the algorithm.
            algo_zip (bytes): The zip file content as bytes.
        """
        with zipfile.ZipFile(io.BytesIO(algo_zip)) as zip_ref:
            if "metadata.json" not in zip_ref.namelist():
                raise ValueError("Invalid algorithm package: missing metadata.json")

            metadata = json.loads(zip_ref.read("metadata.json").decode("utf-8"))
            name = modulize_name(algorithm_id)
            version = metadata.get("version", "0.1.0")
            dependencies = metadata.get("dependencies", [])
            if "requirements.txt" in zip_ref.namelist():
                reqs = zip_ref.read("requirements.txt").decode("utf-8").splitlines()
                dependencies.extend(reqs)

            # Remove lines start with # and empty lines
            dependencies = [
                dep
                for dep in dependencies
                if dep.strip() and not dep.strip().startswith("#")
            ]

            print("Preparing algorithm installation...")
            algo_container_dir = SandboxConfig.ALGORITHM_PATH
            os.makedirs(algo_container_dir, exist_ok=True)
            algo_dir = algo_container_dir / name
            os.makedirs(algo_dir, exist_ok=True)

            print("Extracting algorithm to:", algo_dir)
            if (
                "pyproject.toml" not in zip_ref.namelist()
                or "setup.py" not in zip_ref.namelist()
            ):
                # Create a folder
                # algo/
                #  ├─ pyproject.toml
                #  └─ src/
                #      └─ algo/
                #          ├─ __init__.py
                #          └─ ...algorithm files

                # Create pyproject.toml
                pyproject_content = PYPROJECT_TEMPLATE.format(
                    name=name,
                    version=version,
                    dependencies=json.dumps(dependencies),
                )

                with open(algo_dir / "pyproject.toml", "w") as f:
                    f.write(pyproject_content)

                # Create src/algo/ and extract files
                src_algo_dir = algo_dir / "src" / name
                os.makedirs(src_algo_dir, exist_ok=True)
                zip_ref.extractall(src_algo_dir)

                # If __init__.py does not exist, create it
                init_file = src_algo_dir / "__init__.py"
                if not init_file.exists():
                    with open(init_file, "w") as f:
                        f.write("# Init file for algorithm package\n")
            else:
                # Directly extract all files
                zip_ref.extractall(algo_dir)

            # Run pip install -e <algo_dir>
            algo_dir_abs_path = str(algo_dir.resolve())

            # Check if redis queue for current user exists, if not create one
            job = runner_queue.enqueue("tasks.install_algorithm", algo_dir_abs_path)

            while job.get_status() not in ("finished", "failed"):
                time.sleep(0.5)

            res = job.result
            if not res["done"]:
                raise RuntimeError(f"Algorithm installation failed: {res['error']}")

    @staticmethod
    def run_algorithm(
        algorithm_id: str,
        input_cls: str,
        exe_cls: str,
        bam: bytes,
        input_data: dict,
        params: dict,
        runner_queue,
    ) -> dict:
        """Run an installed algorithm in a sandboxed environment.
        Args:
            algorithm_id (str): The unique identifier for the algorithm.
            input_cls (str): The input class name.
            exe_cls (str): The execution class name.
            bam (bytes): The BAM file content as bytes.
            input_data (dict): The input data for the algorithm.
            params (dict): Additional parameters for the algorithm execution.
        Returns:
            dict: The output data from the algorithm execution.
        """
        job = runner_queue.enqueue(
            "tasks.run_algorithm",
            algorithm_id,
            input_cls,
            exe_cls,
            bam,
            input_data,
            **params,
        )

        while job.get_status() not in ("finished", "failed"):
            time.sleep(0.5)
        res = job.result
        if not res["done"]:
            raise RuntimeError(f"Algorithm execution failed: {res['error']}")
        return res["output"]

    @staticmethod
    def uninstall_algorithm(algorithm_id: str, runner_queue):
        """Uninstall an algorithm by its ID.
        This method removes the installed algorithm package using pip and deletes its files.

        Args:
            algorithm_id (str): The unique identifier for the algorithm.
            worker_process_pool (dict): The worker process pool for managing worker processes.
            user_id (str): The user ID for the sandbox queue.
        """

        algorithm_id = modulize_name(algorithm_id)
        # Uninstall using pip
        os.system(f"pip uninstall -y {algorithm_id}")
        # Remove algorithm files
        algo_container_dir = SandboxConfig.ALGORITHM_PATH
        algo_dir = algo_container_dir / algorithm_id
        if algo_dir.exists() and algo_dir.is_dir():
            shutil.rmtree(algo_dir)

        job = runner_queue.enqueue(
            "tasks.uninstall_algorithm",
            algorithm_id,
        )
        while job.get_status() not in ("finished", "failed"):
            time.sleep(0.5)
        res = job.result
        if not res["done"]:
            raise RuntimeError(f"Algorithm uninstallation failed: {res['error']}")

    @staticmethod
    def get_algorithm_zip(algorithm_id: str) -> bytes:
        """Get the zip file of an installed algorithm.

        Args:
            algorithm_id (str): The unique identifier for the algorithm.

        Returns:
            bytes: The zip file content as bytes.
        """
        algorithm_id = modulize_name(algorithm_id)
        algo_container_dir = SandboxConfig.ALGORITHM_PATH
        algo_dir = algo_container_dir / algorithm_id
        if not algo_dir.exists() or not algo_dir.is_dir():
            raise ValueError(f"Algorithm '{algorithm_id}' is not installed.")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(algo_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(algo_dir)
                    zip_file.write(file_path, arcname)

        zip_buffer.seek(0)
        return zip_buffer.read()
