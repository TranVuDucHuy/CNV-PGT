import os
import shutil
import subprocess
from multiprocessing import Pool
from sqlalchemy.orm import Session
from zipfile import ZipFile
import io
from typing import List
from uuid import uuid4
import json

from .models import Algorithm, AlgorithmParameter
from utils.minio_util import MinioUtil
import importlib.util
from pathlib import Path
from .plugin import BaseInput, BaseOutput, AlgorithmPlugin
from .schemas import (
    AlgorithmSummary,
    AlgorithmParameterDto,
    AlgorithmMetadata,
    AlgorithmDto,
)
from result.service import ResultService
from sample.service import SampleService


def _extract_files_from_zip(algorithm_zip: bytes, extract_dir: Path):
    with ZipFile(io.BytesIO(algorithm_zip)) as z:
        z.extractall(extract_dir)


def _get_class_from_module(module, class_name: str):
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ImportError(
            f"Class '{class_name}' not found in module '{module.__name__}'"
        )
    return cls


def _load_module_from_path(module_name: str, plugin_dir: Path):
    module_path = plugin_dir / f"{module_name}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Module file '{module_path}' not found.")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # actually loads the code
    return module


class AlgorithmService:
    @staticmethod
    def save_zip(
        db: Session, plugin_dir: Path, algorithm_id: str, algorithm_zip: bytes
    ):
        """Save a new algorithm from the provided zip file."""
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")
        # Extract zip file
        with ZipFile(io.BytesIO(algorithm_zip)) as z:
            # Assume the zip contains 'metadata.json', else raise Error
            if "metadata.json" not in z.namelist():
                raise ValueError("metadata.json not found in the zip file")

            metadata = z.read("metadata.json").decode("utf-8")
            # Convert metadata json to dict
            algorithm_metadata = json.loads(metadata)

            plugin_dir = plugin_dir / f"{algorithm.name}_{algorithm.version}"
            plugin_dir.mkdir(parents=True, exist_ok=True)

            _extract_files_from_zip(algorithm_zip, plugin_dir)

            # Validate classes
            modules_classes = [
                [algorithm_metadata["input_class"], BaseInput],
                [algorithm_metadata["output_class"], BaseOutput],
                [algorithm_metadata["exe_class"], AlgorithmPlugin],
            ]

            for module_class, base_class in modules_classes:
                module_name, class_name = module_class.split(":")
                module = _load_module_from_path(module_name, plugin_dir)
                cls = _get_class_from_module(module, class_name)
                if not issubclass(cls, base_class):
                    # Delete the created plugin_dir to avoid clutter
                    shutil.rmtree(plugin_dir)
                    raise TypeError(
                        f"{class_name} must inherit from {base_class.__name__}"
                    )

            algorithm_url = MinioUtil.save_file(
                algorithm_zip,
                object_name=f"{algorithm.name}_{algorithm.version}.zip",
                content_type="application/zip",
            )

            # If all checks pass, we can proceed to upload the algorithm
            algorithm.input_class = algorithm_metadata["input_class"]
            algorithm.output_class = algorithm_metadata["output_class"]
            algorithm.exe_class = algorithm_metadata["exe_class"]
            algorithm.url = algorithm_url

            db.add(algorithm)
            db.commit()

    @staticmethod
    def register(db: Session, algorithm_metadata: AlgorithmMetadata):
        """Save algorithm metadata without uploading zip file."""
        init_params = {}
        for param in algorithm_metadata.parameters:
            init_params[param.name] = {
                "default": param.default,
                "value": param.value,
                "type": param.type,
            }
        algorithm = Algorithm(
            id=f"{algorithm_metadata.name}_{algorithm_metadata.version}",
            name=algorithm_metadata.name,
            version=algorithm_metadata.version,
            description=algorithm_metadata.description,
            parameters=[AlgorithmParameter(id=uuid4().hex, value=init_params)],
        )

        db.add(algorithm)
        db.commit()
        return algorithm.id

    @staticmethod
    def get_all(db: Session) -> List[AlgorithmSummary]:
        algorithms = db.query(Algorithm).all()
        result = []
        for algo in algorithms:
            algo_summary = AlgorithmSummary(
                id=algo.id,
                name=algo.name,
                version=algo.version,
                description=algo.description,
                parameters=[
                    AlgorithmParameterDto(id=param.id, value=param.value)
                    for param in algo.parameters
                ],
            )
            result.append(algo_summary)
        return result

    @staticmethod
    def run(
        db: Session,
        plugin_dir: Path,
        algorithm_id: str,
        input_data: dict,
        **kwargs,
    ) -> BaseOutput:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")

        # If plugin_dir for this algorithm does not exist, create it
        plugin_dir = plugin_dir / algorithm_id
        if not plugin_dir.exists():
            plugin_dir.mkdir(parents=True, exist_ok=True)
            algorithm_zip = MinioUtil.get_file(algorithm.url)
            _extract_files_from_zip(algorithm_zip, plugin_dir)

        venv_dir = plugin_dir / ".venv"
        python_bin = (
            venv_dir / "Scripts" / "python.exe"
            if os.name == "nt"
            else venv_dir / "bin" / "python"
        )
        if not venv_dir.exists():
            # Create virtual environment
            import venv

            venv.EnvBuilder(with_pip=True).create(venv_dir)
            # Install requirements if requirements.txt exists
            requirements_path = plugin_dir / "requirements.txt"
            if requirements_path.exists():
                subprocess.run(
                    [
                        str(python_bin),
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(requirements_path),
                    ],
                    check=True,
                )

        names = [algorithm.input_class, algorithm.exe_class]
        classes = []
        for name in names:
            module_name, class_name = name.split(":")
            module = _load_module_from_path(module_name, plugin_dir)
            cls = _get_class_from_module(module, class_name)
            classes.append(cls)

        input_class, exe_class = classes

        print("Preparing input data for algorithm execution...")
        sample_id = input_data.get("sample_id", None)
        if not sample_id:
            raise ValueError("'sample_id' is required in input_data")
        bam = SampleService.get_file_by_id(db=db, sample_id=sample_id)
        # Replace sample_id with bam content
        input_data["bam"] = bam
        del input_data["sample_id"]

        # Check if 'params' is provided, if not check 'params_id'. Params is optional.
        params = input_data.get("params", None)
        if params:
            del input_data["params"]
        else:
            params_id = input_data.get("params_id", None)
            if params_id:
                params = (
                    db.query(AlgorithmParameter)
                    .filter(AlgorithmParameter.id == params_id)
                    .first()
                )
                del input_data["params_id"]

        # If params is found, extend kwargs with params
        if params:
            kwargs.update(params.value)

        print("Running algorithm...")

        # Run in a separate process
        with Pool(processes=1) as pool:

            def _target():
                input_instance = input_class(**input_data)
                output_instance = exe_class().run(input_instance, **kwargs)
                return output_instance

            result = pool.apply(_target)
            output_instance = result

        ResultService.add_from_algorithm_output(
            db=db,
            sample_id=sample_id,
            algorithm_id=algorithm_id,
            algorithm_output=output_instance,
        )

        return output_instance

    @staticmethod
    def delete(db: Session, algorithm_id: str):
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")

        # Delete from Minio
        MinioUtil.delete_file(algorithm.url)

        # Delete from DB
        db.delete(algorithm)
        db.commit()

    @staticmethod
    def get_raw_algorithm_zip(db: Session, algorithm_id: str) -> bytes:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")

        return MinioUtil.get_file(algorithm.url)

    @staticmethod
    def get_by_id(db: Session, algorithm_id: str) -> AlgorithmDto:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")

        algo_dto = AlgorithmDto(
            id=algorithm.id,
            name=algorithm.name,
            version=algorithm.version,
            description=algorithm.description,
            upload_date=str(algorithm.upload_date),
            url=algorithm.url,
            parameters=[
                AlgorithmParameterDto(id=param.id, value=param.value)
                for param in algorithm.parameters
            ],
        )
        return algo_dto
