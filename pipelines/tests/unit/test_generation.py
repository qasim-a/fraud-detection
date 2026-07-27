from fraud_pipelines.generation.entities import generate_accounts, generate_merchants
from fraud_pipelines.generation.transactions import generate_transactions
from fraud_pipelines.generation.write import write_snapshot


def test_generator_is_deterministic_and_plants_named_fraud(tmp_path) -> None:
    accounts = generate_accounts(42, 20)
    merchants = generate_merchants(42, 10)
    first = generate_transactions(42, 200, accounts, merchants)
    second = generate_transactions(42, 200, accounts, merchants)
    assert first == second
    assert {row["scenario"] for row in first if row["is_fraud"]} == {
        "high_value_cross_border",
        "rapid_velocity",
    }
    one = write_snapshot(
        tmp_path / "one", 42, {"accounts": accounts, "merchants": merchants, "transactions": first}
    )
    two = write_snapshot(
        tmp_path / "two", 42, {"accounts": accounts, "merchants": merchants, "transactions": second}
    )
    assert one["dataset_id"] == two["dataset_id"]
    assert one["files"]["transactions"]["sha256"] == two["files"]["transactions"]["sha256"]
