"""Create transaction scoring core tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_scoring_core"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("external_ref", sa.String(64), nullable=False, unique=True),
        sa.Column("home_country", sa.String(2), nullable=False),
        sa.Column("home_region", sa.String(64), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("segment", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "merchants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("external_ref", sa.String(64), nullable=False, unique=True),
        sa.Column("category_code", sa.String(4), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("risk_tier", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("account_id", sa.Uuid(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("merchant_id", sa.Uuid(), sa.ForeignKey("merchants.id"), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("region", sa.String(64), nullable=False),
        sa.Column("device_id", sa.String(128), nullable=False),
        sa.Column("ip_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("failure_code", sa.String(64)),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transactions_event_time", "transactions", ["event_time"])
    op.create_index("ix_transactions_account_event", "transactions", ["account_id", "event_time"])
    op.create_index("ix_transactions_merchant_event", "transactions", ["merchant_id", "event_time"])
    op.create_table(
        "feature_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=False, unique=True),
        sa.Column("feature_version", sa.String(32), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("source_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("version", sa.String(64), nullable=False, unique=True),
        sa.Column("feature_version", sa.String(32), nullable=False),
        sa.Column("dataset_id", sa.String(128), nullable=False),
        sa.Column("artifact_uri", sa.String(512), nullable=False),
        sa.Column("artifact_sha256", sa.String(64), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("threshold", sa.Numeric(8, 7), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "uq_model_versions_one_active",
        "model_versions",
        ["status"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "fraud_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("transaction_id", sa.Uuid(), sa.ForeignKey("transactions.id"), nullable=False, unique=True),
        sa.Column("feature_snapshot_id", sa.Uuid(), sa.ForeignKey("feature_snapshots.id"), nullable=False, unique=True),
        sa.Column("model_version_id", sa.Uuid(), sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("probability", sa.Numeric(8, 7), nullable=False),
        sa.Column("risk_band", sa.String(32), nullable=False),
        sa.Column("threshold", sa.Numeric(8, 7), nullable=False),
        sa.Column("explanation_status", sa.String(32), nullable=False),
        sa.Column("explanation_factors", sa.JSON(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_fraud_scores_probability_time", "fraud_scores", ["probability", "scored_at"])
    op.create_index("ix_fraud_scores_model_time", "fraud_scores", ["model_version_id", "scored_at"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("fraud_score_id", sa.Uuid(), sa.ForeignKey("fraud_scores.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_alerts_status_created", "alerts", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_alerts_status_created", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_fraud_scores_model_time", table_name="fraud_scores")
    op.drop_index("ix_fraud_scores_probability_time", table_name="fraud_scores")
    op.drop_table("fraud_scores")
    op.drop_index("uq_model_versions_one_active", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_table("feature_snapshots")
    op.drop_index("ix_transactions_merchant_event", table_name="transactions")
    op.drop_index("ix_transactions_account_event", table_name="transactions")
    op.drop_index("ix_transactions_event_time", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("merchants")
    op.drop_table("accounts")
