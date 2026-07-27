"""Chronological transactions with explainable planted fraud scenarios."""

import hashlib
import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fraud_pipelines.generation.entities import NAMESPACE


def generate_transactions(
    seed: int, count: int, accounts: list[dict[str, object]], merchants: list[dict[str, object]]
) -> list[dict[str, object]]:
    rng = random.Random(seed + 2)
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for i in range(count):
        account = accounts[rng.randrange(len(accounts))]
        merchant = merchants[rng.randrange(len(merchants))]
        scenario = "normal"
        is_fraud = False
        amount = Decimal(str(round(rng.lognormvariate(3.5, 0.8), 2)))
        country = str(merchant["country"])
        if i % 97 == 0:
            scenario, is_fraud, amount = "high_value_cross_border", True, Decimal("2500.00")
            country = "GB" if account["home_country"] != "GB" else "US"
        elif i % 89 == 0:
            scenario, is_fraud, amount = "rapid_velocity", True, Decimal("650.00")
        event_time = start + timedelta(seconds=i * 53)
        device = f"device-{rng.randrange(max(10, len(accounts) // 2)):06d}"
        rows.append(
            {
                "id": str(uuid.uuid5(NAMESPACE, f"transaction:{seed}:{i}")),
                "account_id": account["id"],
                "merchant_id": merchant["id"],
                "event_time": event_time.isoformat(),
                "amount": f"{amount:.2f}",
                "currency": "USD",
                "channel": rng.choice(["card_present", "ecommerce", "wallet", "atm"]),
                "country": country,
                "region": str(merchant["region"]),
                "device_id": device,
                "ip_hash": hashlib.sha256(f"{seed}:{device}".encode()).hexdigest(),
                "is_fraud": is_fraud,
                "scenario": scenario,
            }
        )
    return rows
