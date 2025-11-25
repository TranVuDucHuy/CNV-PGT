from sqlalchemy.orm import Session
from zipfile import ZipFile
import io
from typing import List
from uuid import uuid4
import json
import requests

from .models import Algorithm, AlgorithmParameter
from .schemas import (
    AlgorithmSummary,
    AlgorithmParameterDto,
    AlgorithmMetadata,
    AlgorithmDto,
)
from sample.service import SampleService
from config import SandboxConfig


class AlgorithmService:
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
        # create a default AlgorithmParameter and capture its id
        new_param_id = uuid4().hex
        algorithm = Algorithm(
            id=f"{algorithm_metadata.name}_{algorithm_metadata.version}",
            name=algorithm_metadata.name,
            version=algorithm_metadata.version,
            description=algorithm_metadata.description,
            references_required=algorithm_metadata.references_required,
            last_parameter_id=new_param_id,
            parameters=[AlgorithmParameter(id=new_param_id, value=init_params)],
        )

        db.add(algorithm)
        db.commit()
        return algorithm.id, new_param_id

    @staticmethod
    def save_zip(db: Session, algorithm_id: str, algorithm_zip: bytes):
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

            # If all checks pass, we can proceed to upload the algorithm
            algorithm.input_class = algorithm_metadata["input_class"]
            algorithm.output_class = algorithm_metadata["output_class"]
            algorithm.exe_class = algorithm_metadata["exe_class"]

            # Upload zip to sandbox
            sandbox_url = SandboxConfig.SANDBOX_URL
            upload_url = f"{sandbox_url}/{algorithm_id}/zip"
            response = requests.post(upload_url, files={"file": algorithm_zip})
            if response.status_code != 200:
                raise ValueError(
                    f"Failed to upload algorithm zip to sandbox: {response.text}"
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
                references_required=algo.references_required,
                last_parameter_id=algo.last_parameter_id,
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
        algorithm_id: str,
        input_data: dict,
        **kwargs,
    ) -> dict:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")

        print("Preparing input data for algorithm execution...")
        sample_id = input_data.get("sample_id", None)
        if not sample_id:
            raise ValueError("'sample_id' is required in input_data")
        bam = SampleService.get_file_by_id(db=db, sample_id=sample_id)
        # Replace sample_id with bam content

        del input_data["sample_id"]

        # Check if 'params' is provided, if not check 'params_id'. Params is optional.
        params = input_data.get("params", None)
        params_id = None
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

        # Run algorithm in sandbox
        sandbox_url = SandboxConfig.SANDBOX_URL
        run_url = f"{sandbox_url}/{algorithm_id}/run"
        resp = requests.post(
            run_url,
            files={"bam": bam},
            data={
                "input_data": json.dumps(input_data),
                "params": json.dumps(kwargs),
                "input_cls": algorithm.input_class,
                "exe_cls": algorithm.exe_class,
            },
        )
        if resp.status_code != 200:
            raise ValueError(f"Algorithm execution failed: {resp.text}")

        output_json = resp.json()
        from result.service import ResultService
        ResultService.add_from_algorithm_output(
            db=db,
            sample_id=sample_id,
            algorithm_id=algorithm_id,
            algorithm_parameter_id=params_id,
            algorithm_output=output_json,
        )

        return output_json

    @staticmethod
    def delete(db: Session, algorithm_id: str):
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")
        # Delete from Sandbox
        sandbox_url = SandboxConfig.SANDBOX_URL
        delete_url = f"{sandbox_url}/{algorithm_id}"
        response = requests.delete(delete_url)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to delete algorithm from sandbox: {response.text}"
            )
        # Delete from DB
        db.delete(algorithm)
        db.commit()

    @staticmethod
    def get_raw_algorithm_zip(db: Session, algorithm_id: str) -> bytes:
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")
        zip_url = f"{SandboxConfig.SANDBOX_URL}/{algorithm_id}/zip"
        response = requests.get(zip_url)
        if response.status_code != 200:
            raise ValueError(
                f"Failed to download algorithm zip from sandbox: {response.text}"
            )
        return response.content

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
            references_required=algorithm.references_required,
            upload_date=str(algorithm.upload_date),
            last_parameter_id=algorithm.last_parameter_id,
            parameters=[
                AlgorithmParameterDto(id=param.id, value=param.value)
                for param in algorithm.parameters
            ],
        )
        return algo_dto

    @staticmethod
    def update_parameters(db: Session, algorithm_id: str, new_params: dict) -> str:
        from result.models import Result
        
        # Kiểm tra algorithm tồn tại
        algorithm = db.query(Algorithm).filter(Algorithm.id == algorithm_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with id {algorithm_id} not found")
        
        # Bước 1: Xóa các parameter không được sử dụng trong result
        used_param_ids = set(
            db.query(Result.algorithm_parameter_id)
            .filter(
                Result.algorithm_id == algorithm_id,
                Result.algorithm_parameter_id.isnot(None)
            )
            .distinct()
            .all()
        )
        used_param_ids = {pid[0] for pid in used_param_ids if pid[0]}
        
        for param in list(algorithm.parameters):
            if param.id not in used_param_ids:
                db.delete(param)
        
        db.flush()  
        
        # Bước 2: Kiểm tra parameter mới có tồn tại chưa
        for existing_param in algorithm.parameters:
            if existing_param.value == new_params:
                # Parameter đã tồn tại, cập nhật last_parameter_id và trả về ID cũ
                algorithm.last_parameter_id = existing_param.id
                db.commit()
                return existing_param.id
        
        # Bước 3: Parameter chưa tồn tại, tạo mới
        new_param_id = uuid4().hex
        new_param = AlgorithmParameter(
            id=new_param_id,
            algorithm_id=algorithm_id,
            value=new_params
        )
        db.add(new_param)
        
        # Cập nhật last_parameter_id
        algorithm.last_parameter_id = new_param_id
        db.commit()
        
        return new_param_id
