"""Shared API test fixtures."""

from collections.abc import Callable, Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fraud_api.db.models import Account, Merchant
from fraud_api.db.seed import seed_reference_data
from fraud_api.db.session import Base
from fraud_api.models.loader import ModelBundle, ModelMetadata, Predictor
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


class FakePredictor(Predictor):
    def __init__(self, probability: float = 0.95) -> None:
        self.probability = probability

    def predict_probability(self, _features: dict[str, float | int]) -> float:
        return self.probability

    def predict_contributions(self, _features: dict[str, float | int]) -> list[float]:
        return [0.8, -0.1, 0.05, 0.7, -0.2, 0.6, 0.4, 0.3]


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    database = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(database)
    yield database
    Base.metadata.drop_all(database)
    database.dispose()


@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine, expire_on_commit=False) as database_session:
        seed_reference_data(database_session)
        database_session.commit()
        yield database_session


@pytest.fixture
def references(session: Session) -> tuple[Account, Merchant]:
    account = session.query(Account).order_by(Account.external_ref).first()
    merchant = session.query(Merchant).order_by(Merchant.external_ref.desc()).first()
    assert account is not None and merchant is not None
    return account, merchant


@pytest.fixture
def model_bundle(tmp_path: Path) -> ModelBundle:
    metadata = ModelMetadata(
        name="test-xgboost",
        version="test-v1",
        feature_version="1.0.0",
        dataset_id="fixture-dataset",
        artifact_sha256="0" * 64,
        threshold=0.8,
        metrics={"precision": 0.8, "recall": 0.7, "pr_auc": 0.75, "alert_volume": 10},
        created_at=datetime(2026, 7, 27, tzinfo=UTC),
        activated_at=datetime(2026, 7, 27, tzinfo=UTC),
    )
    return ModelBundle(
        metadata=metadata, predictor=FakePredictor(), artifact_path=tmp_path / "model.json"
    )


@pytest.fixture
def model_provider(model_bundle: ModelBundle) -> Callable[[], ModelBundle]:
    return lambda: model_bundle
