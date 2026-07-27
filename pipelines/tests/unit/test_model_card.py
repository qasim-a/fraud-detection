from fraud_pipelines.training.model_card import render_model_card


def test_model_card_records_risk_context() -> None:
    card = render_model_card(
        {
            "version": "fraud-xgb-test",
            "dataset_id": "dataset-1",
            "feature_version": "1.0.0",
            "threshold": 0.8,
            "artifact_sha256": "abc",
            "metrics": {
                "precision": 0.75,
                "recall": 0.5,
                "pr_auc": 0.7,
                "alert_volume": 4,
                "true_positive": 2,
                "false_positive": 1,
                "true_negative": 10,
                "false_negative": 2,
            },
        }
    )
    assert "Dataset ID: `dataset-1`" in card
    assert "human review" in card
    assert "not causation" in card
