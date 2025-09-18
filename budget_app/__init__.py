from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory for the budget manager API."""
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI="sqlite:///budget.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from . import routes  # noqa: WPS433  (import inside function for factory pattern)
    app.register_blueprint(routes.bp)

    from .cli import register_cli

    register_cli(app)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Simple health endpoint useful for smoke testing."""
        return {"status": "ok"}

    return app
