"""Validated append-only analyst review workflow."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from fraud_api.db.models import AlertStatus
from fraud_api.db.review_models import (
    AlertHistoryRecord,
    HistoryEventType,
    ReviewDecisionRecord,
)
from fraud_api.repositories.alerts import get_alert_row
from fraud_api.schemas.alerts import ReviewDecision, ReviewDecisionInput

DEMO_ANALYST = "demo-analyst"


class InvalidAlertTransitionError(RuntimeError):
    """The requested state change is not allowed."""


ALLOWED_TRANSITIONS = {
    AlertStatus.OPEN: {AlertStatus.IN_REVIEW, AlertStatus.CLOSED},
    AlertStatus.IN_REVIEW: {AlertStatus.OPEN, AlertStatus.CLOSED},
    AlertStatus.CLOSED: {AlertStatus.OPEN},
}


def update_alert_status(
    session: Session,
    alert_id: uuid.UUID,
    target: AlertStatus,
    actor_ref: str = DEMO_ANALYST,
) -> None:
    row = get_alert_row(session, alert_id)
    current = row.alert.status
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidAlertTransitionError(
            f"Cannot move alert from {current.value} to {target.value}"
        )
    row.alert.status = target
    event_type = (
        HistoryEventType.REOPENED
        if target == AlertStatus.OPEN and current != AlertStatus.OPEN
        else HistoryEventType.STATUS_CHANGED
    )
    session.add(
        AlertHistoryRecord(
            alert_id=alert_id,
            event_type=event_type,
            from_status=current,
            to_status=target,
            actor_ref=actor_ref,
            created_at=datetime.now(UTC),
        )
    )
    session.flush()


def record_decision(
    session: Session,
    alert_id: uuid.UUID,
    payload: ReviewDecisionInput,
    reviewer_ref: str = DEMO_ANALYST,
) -> ReviewDecision:
    get_alert_row(session, alert_id)
    decision = ReviewDecisionRecord(
        alert_id=alert_id,
        outcome=payload.outcome,
        note=payload.note,
        reviewer_ref=reviewer_ref,
        created_at=datetime.now(UTC),
    )
    session.add(decision)
    session.flush()
    session.add(
        AlertHistoryRecord(
            alert_id=alert_id,
            event_type=HistoryEventType.DECISION_RECORDED,
            review_decision_id=decision.id,
            actor_ref=reviewer_ref,
            created_at=datetime.now(UTC),
        )
    )
    session.flush()
    return ReviewDecision.model_validate(decision, from_attributes=True)
