import shutil
from sqlalchemy.orm import Session
from zipfile import ZipFile
import io
from pydantic import BaseModel
from typing import Optional, List

from .models import Algorithm, AlgorithmParameter
from utils.minio_util import MinioUtil
import importlib.util
from pathlib import Path
from .plugin import BaseInput, BaseOutput, AlgorithmPlugin
from .schemas import AlgorithmParameterDto, AlgorithmSummary


def _extract_files_from_zip(algorithm_zip: bytes, extract_dir: Path):
    with ZipFile(io.BytesIO(algorithm_zip)) as z:
        z.extractall(extract_dir)

def _get_class_from_module(module, class_name: str):
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ImportError(f"Class '{class_name}' not found in module '{module.__name__}'")
    return cls

def _load_module_from_path(module_name: str, plugin_dir: Path):
    module_path = plugin_dir / f"{module_name}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Module file '{module_path}' not found.")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # actually loads the code
    return module


class AlgorithmMetadata(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    input_class: str    # For example: main:ExampleInput -> class ExampleInput in main.py
    output_class: str   # For example: main:ExampleOutput -> class ExampleOutput in main.py
    exe_class: str      # For example: main:ExamplePlugin -> class ExamplePlugin in main.py
    parameters: Optional[List[AlgorithmParameterDto]] = []


class AlgorithmService:
    @staticmethod
    def save(db: Session, plugin_dir: Path, algorithm_zip: bytes):
        """Save a new algorithm from the provided zip file."""
        # Extract zip file
        with ZipFile(io.BytesIO(algorithm_zip)) as z:
            # Assume the zip contains 'metadata.json', else raise Error
            if 'metadata.json' not in z.namelist():
                raise ValueError("metadata.json not found in the zip file")
            
            metadata = z.read('metadata.json').decode('utf-8')

            # Parse metadata, will raise ValidationError if invalid
            algorithm_metadata = AlgorithmMetadata.model_validate_json(metadata)

            plugin_dir = plugin_dir / f"{algorithm_metadata.name}_{algorithm_metadata.version}"
            plugin_dir.mkdir(parents=True, exist_ok=True)

            _extract_files_from_zip(algorithm_zip, plugin_dir)


            # Validate classes
            modules_classes = [
                [algorithm_metadata.input_class, BaseInput],
                [algorithm_metadata.output_class, BaseOutput],
                [algorithm_metadata.exe_class, AlgorithmPlugin],
            ]

            for module_class, base_class in modules_classes:
                module_name, class_name = module_class.split(":")
                module = _load_module_from_path(module_name, plugin_dir)
                cls = _get_class_from_module(module, class_name)
                if not issubclass(cls, base_class):
                    # Delete the created plugin_dir to avoid clutter
                    shutil.rmtree(plugin_dir)
                    raise TypeError(f"{class_name} must inherit from {base_class.__name__}")

            algorithm_url = MinioUtil.save_file(
                algorithm_zip, 
                object_name=f"{algorithm_metadata.name}_{algorithm_metadata.version}.zip", 
                content_type="application/zip")
            
            # If all checks pass, we can proceed to upload the algorithm
            algorithm = Algorithm(
                id=f"{algorithm_metadata.name}_{algorithm_metadata.version}",
                name=algorithm_metadata.name,
                version=algorithm_metadata.version,
                description=algorithm_metadata.description,
                url=algorithm_url,
                input_class=algorithm_metadata.input_class,
                output_class=algorithm_metadata.output_class,
                exe_class=algorithm_metadata.exe_class,
                parameters=[
                    AlgorithmParameter(
                        id=f"{algorithm_metadata.name}_{algorithm_metadata.version}_{param.name}",
                        name=param.name,
                        type=param.type,
                        description=param.description
                    ) for param in algorithm_metadata.parameters
                ]
            )

            db.add(algorithm)
            db.commit()

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
                    AlgorithmParameterDto(
                        name=param.name,
                        type=param.type,
                        description=param.description
                    ) for param in algo.parameters
                ]
            )
            result.append(algo_summary)
        return result
    
    @staticmethod
    def run(db: Session, plugin_dir: Path, algorithm_id: str, input_data: dict, **kwargs) -> BaseOutput:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")
        
        # If plugin_dir for this algorithm does not exist, create it
        plugin_dir = plugin_dir / algorithm_id
        if not plugin_dir.exists():
            plugin_dir.mkdir(parents=True, exist_ok=True)
            algorithm_zip = MinioUtil.get_file(algorithm.url)
            _extract_files_from_zip(algorithm_zip, plugin_dir)

        names = [algorithm.input_class, algorithm.exe_class]
        classes = []
        for name in names:
            module_name, class_name = name.split(":")
            module = _load_module_from_path(module_name, plugin_dir)
            cls = _get_class_from_module(module, class_name)
            classes.append(cls)

        input_class, exe_class = classes

        input_instance = input_class(**input_data)
        return exe_class().run(input_instance, **kwargs)
    
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