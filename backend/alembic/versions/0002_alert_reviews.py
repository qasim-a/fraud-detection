"""Add append-only alert review workflow tables.

Revision ID: 0002_alert_reviews
Revises: 0001_scoring_core
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_alert_reviews"
down_revision: str | None = "0001_scoring_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("reviewer_ref", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_review_decisions_alert_created", "review_decisions", ["alert_id", "created_at"]
    )
    op.create_table(
        "alert_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("alerts.id"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("from_status", sa.String(32)),
        sa.Column("to_status", sa.String(32)),
        sa.Column(
            "review_decision_id", sa.Uuid(), sa.ForeignKey("review_decisions.id")
        ),
        sa.Column("actor_ref", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alert_history_alert_created", "alert_history", ["alert_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_alert_history_alert_created", table_name="alert_history")
    op.drop_table("alert_history")
    op.drop_index("ix_review_decisions_alert_created", table_name="review_decisions")
    op.drop_table("review_decisions")
