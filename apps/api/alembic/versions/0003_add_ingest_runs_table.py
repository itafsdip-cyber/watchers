"""add ingest runs table for observability stats

Revision ID: 0003_add_ingest_runs_table
Revises: 0002_incident_summary_to_text
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_add_ingest_runs_table"
down_revision = "0002_incident_summary_to_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("total_claims", sa.Integer(), nullable=False),
        sa.Column("inserted", sa.Integer(), nullable=False),
        sa.Column("duplicates_merged", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingest_runs_id"), "ingest_runs", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingest_runs_id"), table_name="ingest_runs")
    op.drop_table("ingest_runs")
