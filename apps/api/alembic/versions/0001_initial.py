"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("credibility_score", sa.Float(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_incidents_id"), "incidents", ["id"], unique=False)

    op.create_table(
        "source_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=100), nullable=False),
        sa.Column("historical_accuracy", sa.Float(), nullable=False),
        sa.Column("reliability_baseline", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_source_profiles_id"), "source_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_source_profiles_source_name"), "source_profiles", ["source_name"], unique=True)

    op.create_table(
        "incident_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_incident_sources_id"), "incident_sources", ["id"], unique=False)
    op.create_index(op.f("ix_incident_sources_incident_id"), "incident_sources", ["incident_id"], unique=False)

    op.create_table(
        "incident_timeline_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("incident_id", sa.Integer(), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_incident_timeline_entries_id"), "incident_timeline_entries", ["id"], unique=False)
    op.create_index(op.f("ix_incident_timeline_entries_incident_id"), "incident_timeline_entries", ["incident_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_incident_timeline_entries_incident_id"), table_name="incident_timeline_entries")
    op.drop_index(op.f("ix_incident_timeline_entries_id"), table_name="incident_timeline_entries")
    op.drop_table("incident_timeline_entries")

    op.drop_index(op.f("ix_incident_sources_incident_id"), table_name="incident_sources")
    op.drop_index(op.f("ix_incident_sources_id"), table_name="incident_sources")
    op.drop_table("incident_sources")

    op.drop_index(op.f("ix_source_profiles_source_name"), table_name="source_profiles")
    op.drop_index(op.f("ix_source_profiles_id"), table_name="source_profiles")
    op.drop_table("source_profiles")

    op.drop_index(op.f("ix_incidents_id"), table_name="incidents")
    op.drop_table("incidents")
