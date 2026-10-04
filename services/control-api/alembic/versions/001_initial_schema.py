"""Initial control-plane schema.

Revision ID: 001
Revises:
Create Date: 2026-03-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("tier", sa.String(32), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "memberships",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", "user_id"),
    )
    op.create_table(
        "quotas",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), primary_key=True),
        sa.Column("max_devices", sa.Integer(), nullable=False),
        sa.Column("max_events_per_sec", sa.Integer(), nullable=False),
        sa.Column("max_concurrent_runs", sa.Integer(), nullable=False),
        sa.Column("max_run_duration_s", sa.Integer(), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("max_api_rps", sa.Integer(), nullable=False),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("prefix", sa.String(32), nullable=False, unique=True),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])
    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "scenario_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("spec", postgresql.JSONB(), nullable=False),
        sa.Column("spec_yaml", sa.Text()),
        sa.Column("checksum", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("scenario_id", "version"),
    )
    op.create_table(
        "runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("scenario_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_versions.id")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("seed", sa.BigInteger()),
        sa.Column("mode", sa.String(32)),
        sa.Column("speed", sa.Float()),
        sa.Column("device_count", sa.Integer()),
        sa.Column("events_emitted", sa.BigInteger(), server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "ground_truth_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.id")),
        sa.Column("device_id", sa.Text()),
        sa.Column("metric", sa.Text()),
        sa.Column("kind", sa.Text()),
        sa.Column("magnitude", sa.Float()),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("source_event", sa.Text()),
    )
    op.create_table(
        "usage_daily",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("events_ingested", sa.BigInteger(), server_default="0"),
        sa.Column("events_rejected", sa.BigInteger(), server_default="0"),
        sa.Column("api_calls", sa.BigInteger(), server_default="0"),
        sa.Column("sim_seconds", sa.BigInteger(), server_default="0"),
        sa.PrimaryKeyConstraint("tenant_id", "day"),
    )


def downgrade() -> None:
    op.drop_table("usage_daily")
    op.drop_table("ground_truth_labels")
    op.drop_table("runs")
    op.drop_table("scenario_versions")
    op.drop_table("scenarios")
    op.drop_table("api_keys")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("quotas")
    op.drop_table("memberships")
    op.drop_table("users")
    op.drop_table("tenants")
