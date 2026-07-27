"""Deterministic synthetic operational reference data."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from fraud_api.db.models import Account, AccountSegment, Merchant, MerchantRiskTier
from fraud_api.db.session import create_session_factory

SEED_NAMESPACE = uuid.UUID("d4c1c96b-f9ba-49f0-8207-c7ae103c64ea")


def stable_id(name: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NAMESPACE, name)


def seed_reference_data(session: Session) -> tuple[list[Account], list[Merchant]]:
    accounts = [
        Account(
            id=stable_id("account-001"),
            external_ref="acct_demo_001",
            home_country="US",
            home_region="NY",
            opened_at=datetime(2024, 1, 1, tzinfo=UTC),
            segment=AccountSegment.CONSUMER,
        ),
        Account(
            id=stable_id("account-002"),
            external_ref="acct_demo_002",
            home_country="US",
            home_region="CA",
            opened_at=datetime(2024, 6, 1, tzinfo=UTC),
            segment=AccountSegment.SMALL_BUSINESS,
        ),
    ]
    merchants = [
        Merchant(
            id=stable_id("merchant-001"),
            external_ref="merchant_demo_low",
            category_code="5411",
            country="US",
            region="NY",
            risk_tier=MerchantRiskTier.LOW,
        ),
        Merchant(
            id=stable_id("merchant-002"),
            external_ref="merchant_demo_high",
            category_code="5999",
            country="GB",
            region="LND",
            risk_tier=MerchantRiskTier.HIGH,
        ),
    ]
    for record in [*accounts, *merchants]:
        session.merge(record)
    session.flush()
    return accounts, merchants


def main() -> None:
    with create_session_factory()() as session, session.begin():
        accounts, merchants = seed_reference_data(session)
    print(f"Seeded {len(accounts)} accounts and {len(merchants)} merchants.")


if __name__ == "__main__":
    main()
