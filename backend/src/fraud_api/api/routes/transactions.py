"""Transaction ingestion and retrieval routes."""

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from fraud_api.api.dependencies import get_model_provider
from fraud_api.db.session import get_session
from fraud_api.models.loader import ModelBundle
from fraud_api.repositories.transactions import (
    ReferenceNotFoundError,
    TransactionConflictError,
    TransactionNotFoundError,
    result_for_transaction,
)
from fraud_api.schemas.transactions import TransactionInput, TransactionResult
from fraud_api.services.ingestion import IngestionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResult, status_code=status.HTTP_201_CREATED)
def score_transaction(
    payload: TransactionInput,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    model_provider: Annotated[Callable[[], ModelBundle], Depends(get_model_provider)],
) -> TransactionResult:
    try:
        outcome = IngestionService(session, model_provider).ingest(payload)
    except TransactionConflictError as exc:
        raise HTTPException(
            status_code=409, detail="Transaction ID already has a different payload"
        ) from exc
    except ReferenceNotFoundError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not outcome.created:
        response.status_code = status.HTTP_200_OK
    elif outcome.result.status == "scoring_failed":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return outcome.result


@router.get("/{transactionId}", response_model=TransactionResult)
def get_transaction(
    transaction_id: Annotated[uuid.UUID, Path(alias="transactionId")],
    session: Annotated[Session, Depends(get_session)],
) -> TransactionResult:
    try:
        return result_for_transaction(session, transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found") from exc
