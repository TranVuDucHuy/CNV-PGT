import importlib.util as importlib_util


def load_module(module_name: str):
    print(f"Loading module: {module_name}")
    spec = importlib_util.find_spec(module_name)
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)  # actually loads the code
    return module


def get_class_from_module(module, class_name: str):
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ImportError(
            f"Class '{class_name}' not found in module '{module.__name__}'"
        )
    return cls


def modulize_name(name: str) -> str:
    """Replace invalid characters in a name to make it a valid Python module name."""
    return name.replace("-", "_").replace(" ", "_").replace(".", "_")
