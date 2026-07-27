"""Stable synthetic accounts and merchants."""

import random
import uuid
from datetime import UTC, datetime, timedelta

NAMESPACE = uuid.UUID("d8f330e8-906c-4c9b-b24e-f1faf5ab5c61")


def generate_accounts(seed: int, count: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    countries = [("US", "NY"), ("GB", "LND"), ("CA", "ON"), ("DE", "BE")]
    opened = datetime(2020, 1, 1, tzinfo=UTC)
    return [
        {
            "id": str(uuid.uuid5(NAMESPACE, f"account:{seed}:{i}")),
            "external_ref": f"ACC-{i:06d}",
            "home_country": (location := countries[rng.randrange(len(countries))])[0],
            "home_region": location[1],
            "opened_at": (opened + timedelta(days=rng.randrange(1000))).isoformat(),
            "segment": "small_business" if rng.random() < 0.15 else "consumer",
        }
        for i in range(count)
    ]


def generate_merchants(seed: int, count: int) -> list[dict[str, object]]:
    rng = random.Random(seed + 1)
    countries = [("US", "NY"), ("GB", "LND"), ("CA", "ON"), ("DE", "BE")]
    tiers = ["low", "low", "medium", "high"]
    return [
        {
            "id": str(uuid.uuid5(NAMESPACE, f"merchant:{seed}:{i}")),
            "external_ref": f"MER-{i:05d}",
            "category_code": rng.choice(["5411", "5812", "5732", "7995"]),
            "country": (location := countries[rng.randrange(len(countries))])[0],
            "region": location[1],
            "risk_tier": rng.choice(tiers),
        }
        for i in range(count)
    ]
