import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fraud_api.schemas.transactions import TransactionInput
from pydantic import ValidationError


def valid_payload() -> dict[str, object]:
    return {
        "id": str(uuid.uuid4()),
        "eventTime": datetime(2026, 7, 27, 14, 30, tzinfo=UTC).isoformat(),
        "accountId": str(uuid.uuid4()),
        "merchantId": str(uuid.uuid4()),
        "amount": "125.00",
        "currency": "USD",
        "channel": "ecommerce",
        "country": "US",
        "region": "NY",
        "deviceId": "device_demo_001",
        "ipHash": "0123456789abcdef",
    }


def test_transaction_accepts_strict_public_shape() -> None:
    transaction = TransactionInput.model_validate(valid_payload())

    assert transaction.amount == Decimal("125.00")
    assert transaction.model_dump(mode="json", by_alias=True)["eventTime"].endswith("Z")


@pytest.mark.parametrize(
    ("field", "value"),
    [("amount", "0.00"), ("currency", "usd"), ("country", "USA"), ("channel", "wire")],
)
def test_transaction_rejects_invalid_values(field: str, value: object) -> None:
    payload = valid_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        TransactionInput.model_validate(payload)


def test_transaction_rejects_unknown_fields() -> None:
    payload = valid_payload()
    payload["cardNumber"] = "4111111111111111"

    with pytest.raises(ValidationError):
        TransactionInput.model_validate(payload)
