"""Fraud Review API application factory."""

from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fraud_api.api.errors import register_exception_handlers
from fraud_api.api.routes.alerts import router as alerts_router
from fraud_api.api.routes.dashboard import router as dashboard_router
from fraud_api.api.routes.transactions import router as transactions_router
from fraud_api.core.config import Settings, get_settings
from fraud_api.core.logging import configure_logging
from fraud_api.db.session import get_session
from fraud_api.schemas.health import HealthResponse


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    application = FastAPI(title="Fraud Review API", version="0.1.0")
    register_exception_handlers(application)
    application.include_router(alerts_router, prefix="/api/v1")
    application.include_router(dashboard_router, prefix="/api/v1")
    application.include_router(transactions_router, prefix="/api/v1")

    def _health(
        db: Annotated[Session, Depends(get_session)],
        runtime: Annotated[Settings, Depends(get_settings)],
    ) -> HealthResponse:
        try:
            db.execute(text("SELECT 1"))
            database = "available"
        except SQLAlchemyError:
            database = "unavailable"

        model = (
            "available"
            if runtime.model_artifact_path.is_file() and runtime.model_metadata_path.is_file()
            else "unavailable"
        )
        overall = "ok" if database == "available" and model == "available" else "degraded"
        return HealthResponse(status=overall, database=database, model=model)

    application.add_api_route(
        "/api/v1/health",
        _health,
        methods=["GET"],
        response_model=HealthResponse,
        tags=["operations"],
    )

    return application


app = create_app()
