"""Analyst alert queue, detail, status, and decision routes."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from fraud_api.db.models import AlertStatus
from fraud_api.db.session import get_session
from fraud_api.repositories.alerts import (
    AlertNotFoundError,
    InvalidCursorError,
    get_alert_detail,
    list_alerts,
)
from fraud_api.schemas.alerts import (
    AlertDetail,
    AlertPage,
    AlertStatusInput,
    AlertSummary,
    ReviewDecision,
    ReviewDecisionInput,
)
from fraud_api.services.reviews import (
    InvalidAlertTransitionError,
    record_decision,
    update_alert_status,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertPage)
def alert_queue(
    start: datetime,
    end: datetime,
    session: Annotated[Session, Depends(get_session)],
    alert_status: Annotated[AlertStatus | None, Query(alias="status")] = None,
    min_risk: Annotated[float | None, Query(alias="minRisk", ge=0, le=1)] = None,
    merchant: str | None = None,
    channel: str | None = None,
    country: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> AlertPage:
    if start >= end:
        raise HTTPException(status_code=422, detail="start must be before end")
    try:
        return list_alerts(
            session,
            start=start,
            end=end,
            status=alert_status,
            min_risk=min_risk,
            merchant=merchant,
            channel=channel,
            country=country,
            limit=limit,
            cursor=cursor,
        )
    except InvalidCursorError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{alertId}", response_model=AlertDetail)
def alert_detail(
    alert_id: Annotated[uuid.UUID, Path(alias="alertId")],
    session: Annotated[Session, Depends(get_session)],
) -> AlertDetail:
    try:
        return get_alert_detail(session, alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc


@router.patch("/{alertId}", response_model=AlertSummary)
def change_alert_status(
    payload: AlertStatusInput,
    alert_id: Annotated[uuid.UUID, Path(alias="alertId")],
    session: Annotated[Session, Depends(get_session)],
) -> AlertSummary:
    try:
        update_alert_status(session, alert_id, payload.status)
        return get_alert_detail(session, alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc
    except InvalidAlertTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{alertId}/decisions", response_model=ReviewDecision, status_code=status.HTTP_201_CREATED
)
def create_decision(
    payload: ReviewDecisionInput,
    alert_id: Annotated[uuid.UUID, Path(alias="alertId")],
    session: Annotated[Session, Depends(get_session)],
) -> ReviewDecision:
    try:
        return record_decision(session, alert_id, payload)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Alert not found") from exc
