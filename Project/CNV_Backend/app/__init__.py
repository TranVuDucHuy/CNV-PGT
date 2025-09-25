from flask import Flask

from .extensions import db, migrate
from .features.sample import sample_bp
from .config import Config


def create_app() -> Flask:
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config())

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(sample_bp, url_prefix="/api")

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


