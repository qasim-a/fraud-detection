from fraud_api.core.logging import REDACTED, redact


def test_redact_removes_nested_sensitive_fields() -> None:
    value = {
        "transaction": {"amount": "10.00", "card_number": "4111111111111111"},
        "token": "abc",
    }

    assert redact(value) == {
        "transaction": {"amount": "10.00", "card_number": REDACTED},
        "token": REDACTED,
    }
