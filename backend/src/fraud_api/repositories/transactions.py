"""Persistence operations for idempotent transaction scoring."""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from fraud_api.db.models import (
    Account,
    AlertRecord,
    AlertStatus,
    ExplanationStatus,
    FeatureSnapshot,
    FraudScoreRecord,
    Merchant,
    MerchantRiskTier,
    ModelStatus,
    ModelVersionRecord,
    TransactionRecord,
    TransactionStatus,
)
from fraud_api.db.review_models import AlertHistoryRecord, HistoryEventType
from fraud_api.features.online import OnlineFeatureContext
from fraud_api.models.loader import ModelBundle
from fraud_api.schemas.transactions import (
    ExplanationFactor,
    FraudScore,
    TransactionInput,
    TransactionResult,
)
from fraud_api.services.scoring import ScoreOutcome


class TransactionConflictError(RuntimeError):
    """A transaction identifier was reused with a different payload."""


class ReferenceNotFoundError(RuntimeError):
    """An account or merchant reference does not exist."""


class TransactionNotFoundError(RuntimeError):
    """A transaction identifier does not exist."""


@dataclass(frozen=True, slots=True)
class ExistingTransaction:
    transaction: TransactionRecord
    is_identical: bool


RISK_VALUES = {
    MerchantRiskTier.LOW: 0.1,
    MerchantRiskTier.MEDIUM: 0.5,
    MerchantRiskTier.HIGH: 0.9,
}


def transaction_payload_hash(transaction: TransactionInput) -> str:
    payload = transaction.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def find_existing(session: Session, transaction: TransactionInput) -> ExistingTransaction | None:
    record = session.get(TransactionRecord, transaction.id)
    if record is None:
        return None
    return ExistingTransaction(record, record.payload_hash == transaction_payload_hash(transaction))


def create_transaction(session: Session, transaction: TransactionInput) -> TransactionRecord:
    record = TransactionRecord(
        id=transaction.id,
        account_id=transaction.account_id,
        merchant_id=transaction.merchant_id,
        event_time=transaction.event_time,
        amount=transaction.amount,
        currency=transaction.currency,
        channel=transaction.channel,
        country=transaction.country,
        region=transaction.region,
        device_id=transaction.device_id,
        ip_hash=transaction.ip_hash,
        status=TransactionStatus.ACCEPTED,
        payload_hash=transaction_payload_hash(transaction),
    )
    session.add(record)
    session.flush()
    return record


def build_feature_context(session: Session, transaction: TransactionInput) -> OnlineFeatureContext:
    account = session.get(Account, transaction.account_id)
    merchant = session.get(Merchant, transaction.merchant_id)
    if account is None or merchant is None:
        raise ReferenceNotFoundError("Account or merchant reference does not exist")
    prior: Select[tuple[int, Decimal | None]] = select(
        func.count(TransactionRecord.id),
        func.avg(TransactionRecord.amount),
    ).where(
        TransactionRecord.account_id == transaction.account_id,
        TransactionRecord.event_time < transaction.event_time,
        TransactionRecord.event_time >= transaction.event_time - timedelta(days=30),
    )
    _count_30d, average = session.execute(prior).one()
    count_1h = session.scalar(
        select(func.count(TransactionRecord.id)).where(
            TransactionRecord.account_id == transaction.account_id,
            TransactionRecord.event_time < transaction.event_time,
            TransactionRecord.event_time >= transaction.event_time - timedelta(hours=1),
        )
    )
    return OnlineFeatureContext(
        account_tx_count_1h=int(count_1h or 0),
        account_avg_amount_30d=float(average or 0),
        account_country=account.home_country,
        merchant_risk_score=RISK_VALUES[merchant.risk_tier],
        source_as_of=transaction.event_time,
    )


def ensure_model_version(session: Session, bundle: ModelBundle) -> ModelVersionRecord:
    existing = session.scalar(
        select(ModelVersionRecord).where(ModelVersionRecord.version == bundle.metadata.version)
    )
    if existing is not None:
        return existing
    metadata = bundle.metadata
    record = ModelVersionRecord(
        name=metadata.name,
        version=metadata.version,
        feature_version=metadata.feature_version,
        dataset_id=metadata.dataset_id,
        artifact_uri=str(bundle.artifact_path),
        artifact_sha256=metadata.artifact_sha256,
        metrics=metadata.metrics,
        threshold=Decimal(str(metadata.threshold)),
        status=ModelStatus.ACTIVE,
        created_at=metadata.created_at,
        activated_at=metadata.activated_at,
    )
    session.add(record)
    session.flush()
    return record


def persist_score(
    session: Session,
    transaction: TransactionRecord,
    features: dict[str, float | int],
    context: OnlineFeatureContext,
    bundle: ModelBundle,
    outcome: ScoreOutcome,
) -> tuple[FraudScoreRecord, AlertRecord | None]:
    snapshot = FeatureSnapshot(
        transaction_id=transaction.id,
        feature_version=bundle.metadata.feature_version,
        values=features,
        source_as_of=context.source_as_of,
    )
    session.add(snapshot)
    session.flush()
    model = ensure_model_version(session, bundle)
    score = FraudScoreRecord(
        transaction_id=transaction.id,
        feature_snapshot_id=snapshot.id,
        model_version_id=model.id,
        probability=Decimal(str(outcome.probability)),
        risk_band=outcome.risk_band,
        threshold=Decimal(str(outcome.threshold)),
        explanation_status=ExplanationStatus.AVAILABLE,
        explanation_factors=[factor.model_dump() for factor in outcome.factors],
    )
    session.add(score)
    transaction.status = TransactionStatus.SCORED
    session.flush()
    alert: AlertRecord | None = None
    if outcome.creates_alert:
        created_at = datetime.now(UTC)
        alert = AlertRecord(
            fraud_score_id=score.id,
            status=AlertStatus.OPEN,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(alert)
        session.flush()
        session.add(
            AlertHistoryRecord(
                alert_id=alert.id,
                event_type=HistoryEventType.CREATED,
                to_status=AlertStatus.OPEN,
                actor_ref="system",
                created_at=created_at,
            )
        )
        session.flush()
    return score, alert


def result_for_transaction(session: Session, transaction_id: uuid.UUID) -> TransactionResult:
    transaction = session.get(TransactionRecord, transaction_id)
    if transaction is None:
        raise TransactionNotFoundError(str(transaction_id))
    score_record = session.scalar(
        select(FraudScoreRecord).where(FraudScoreRecord.transaction_id == transaction_id)
    )
    if score_record is None:
        return TransactionResult(
            transactionId=transaction.id,
            status="scoring_failed",
            ingestedAt=transaction.ingested_at,
            failureCode=transaction.failure_code,
        )
    model = session.get(ModelVersionRecord, score_record.model_version_id)
    if model is None:
        raise RuntimeError("Score references a missing model version")
    alert_id = session.scalar(
        select(AlertRecord.id).where(AlertRecord.fraud_score_id == score_record.id)
    )
    score = FraudScore(
        id=score_record.id,
        probability=float(score_record.probability),
        riskBand=score_record.risk_band.value,
        threshold=float(score_record.threshold),
        modelVersion=model.version,
        featureVersion=model.feature_version,
        scoredAt=score_record.scored_at,
        explanationStatus=score_record.explanation_status.value,
        factors=[
            ExplanationFactor.model_validate(value) for value in score_record.explanation_factors
        ],
    )
    return TransactionResult(
        transactionId=transaction.id,
        status="scored",
        ingestedAt=transaction.ingested_at,
        score=score,
        alertId=alert_id,
    )
