from flask import Blueprint

sample_bp = Blueprint("sample", __name__)

from . import routes  # noqa: E402,F401


