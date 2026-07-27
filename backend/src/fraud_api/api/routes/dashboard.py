"""Operational dashboard and active-model endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fraud_api.db.session import get_session
from fraud_api.repositories.dashboard import (
    ActiveModelNotFoundError,
    ModelMetricsUnavailableError,
    active_model_summary,
    dashboard_summary,
)
from fraud_api.schemas.dashboard import DashboardSummary, ModelSummary

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    start: datetime,
    end: datetime,
    session: Annotated[Session, Depends(get_session)],
) -> DashboardSummary:
    if start.tzinfo is None or end.tzinfo is None:
        raise HTTPException(status_code=422, detail="start and end must include timezone offsets")
    if start >= end:
        raise HTTPException(status_code=422, detail="start must be before end")
    return dashboard_summary(session, start, end)


@router.get("/models/active", response_model=ModelSummary)
def get_active_model(session: Annotated[Session, Depends(get_session)]) -> ModelSummary:
    try:
        return active_model_summary(session)
    except ActiveModelNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ModelMetricsUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
