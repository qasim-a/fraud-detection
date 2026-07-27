"""Atomic transaction ingestion and fraud scoring orchestration."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from fraud_api.db.models import TransactionStatus
from fraud_api.features.online import build_online_features
from fraud_api.models.loader import ModelBundle, ModelUnavailableError
from fraud_api.repositories.transactions import (
    TransactionConflictError,
    build_feature_context,
    create_transaction,
    find_existing,
    persist_score,
    result_for_transaction,
)
from fraud_api.schemas.transactions import TransactionInput, TransactionResult
from fraud_api.services.scoring import score_features

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    result: TransactionResult
    created: bool


class IngestionService:
    def __init__(self, session: Session, model_provider: Callable[[], ModelBundle]) -> None:
        self._session = session
        self._model_provider = model_provider

    def ingest(self, payload: TransactionInput) -> IngestionOutcome:
        existing = find_existing(self._session, payload)
        if existing is not None:
            if not existing.is_identical:
                raise TransactionConflictError(str(payload.id))
            logger.info("transaction_duplicate", extra={"transaction_id": str(payload.id)})
            return IngestionOutcome(
                result_for_transaction(self._session, payload.id), created=False
            )

        transaction = create_transaction(self._session, payload)
        context = build_feature_context(self._session, payload)
        features = build_online_features(payload, context)
        try:
            bundle = self._model_provider()
        except ModelUnavailableError:
            transaction.status = TransactionStatus.SCORING_FAILED
            transaction.failure_code = "model_unavailable"
            self._session.flush()
            logger.warning(
                "transaction_scoring_failed",
                extra={"transaction_id": str(payload.id), "failure_code": "model_unavailable"},
            )
            return IngestionOutcome(result_for_transaction(self._session, payload.id), created=True)

        outcome = score_features(bundle, features)
        score, alert = persist_score(self._session, transaction, features, context, bundle, outcome)
        logger.info(
            "transaction_scored",
            extra={
                "transaction_id": str(payload.id),
                "score_id": str(score.id),
                "model_version": bundle.metadata.version,
                "risk_band": outcome.risk_band.value,
                "alert_created": alert is not None,
            },
        )
        return IngestionOutcome(result_for_transaction(self._session, payload.id), created=True)
