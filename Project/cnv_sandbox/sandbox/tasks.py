import importlib
from utils.module_utils import modulize_name, load_module, get_class_from_module

import sys
import subprocess
from pathlib import Path
import traceback


def install_editable_mode(algorithm_path):
    path = Path(algorithm_path)

    if not path.exists():
        return {"done": False, "error": f"Path does not exist: {algorithm_path}"}

    # Must contain pyproject.toml or setup.py
    if not ((path / "pyproject.toml").exists() or (path / "setup.py").exists()):
        return {
            "done": False,
            "error": "Not a valid Python project: missing pyproject.toml or setup.py",
        }

    # Print content of "pyproject.toml" if exists
    if (path / "pyproject.toml").exists():
        with open(path / "pyproject.toml", "r") as f:
            print("pyproject.toml content:")
            print(f.read())
    # Install the algorithm in editable mode to keep
    try:
        subprocess.run(
            ["pip", "install", "-e", str(path)], check=True
        )
    except subprocess.CalledProcessError as e:
        return {"done": False, "error": str(e)}

    return {"done": True}


def install_conda_pkgs(channels: list[str], packages: list[str]):
    """Install packages using conda.

    Args:
        channels (list[str]): List of conda channels to use.
        packages (list[str]): List of packages to install.

    Returns:
        dict: A dictionary indicating success or failure.
    """
    try:
        command = ["conda", "install", "-y"]
        for channel in channels:
            command.extend(["-c", channel])
        command.extend(packages)

        subprocess.run(command, check=True)
        return {"done": True}
    except subprocess.CalledProcessError as e:
        return {"done": False, "error": str(e)}


def run_algorithm(
    algorithm_id: str,
    input_cls: str,
    exe_cls: str,
    bam: bytes,
    input_data: dict,
    **kwargs,
) -> dict:
    """Run an installed algorithm.
    This method executes the algorithm specified by the name, input_cls, and exe_cls.
    It takes the BAM file and input data as parameters and returns the output.
    """
    try:
        algorithm_id = modulize_name(algorithm_id)
        class_names = [input_cls, exe_cls]
        classes = []
        for cls_name in class_names:
            pre_modules, actual_name = cls_name.split(":")
            module = load_module(f"{algorithm_id}.{pre_modules}")
            cls = get_class_from_module(module, actual_name)
            classes.append(cls)
        InputClass, ExecClass = classes

        input_instance = InputClass(bam=bam, **input_data)
        output_instance = ExecClass().run(input_instance, **kwargs)

        return {"done": True, "output": output_instance.model_dump()}
    except Exception as e:
        print("Error during algorithm execution:", str(e))
        traceback.print_exc()
        return {"done": False, "error": str(e)}


def uninstall_algorithm(algorithm_id: str):
    algorithm_id = modulize_name(algorithm_id)
    try:
        subprocess.run(["pip", "uninstall", "-y", algorithm_id], check=True)
        return {"done": True}
    except subprocess.CalledProcessError as e:
        return {"done": False, "error": str(e)}


def example_execute():
    return {"status": "success", "message": "Example algorithm executed."}
