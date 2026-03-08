"""expand incident summary and keep title bounded

Revision ID: 0002_incident_summary_to_text
Revises: 0001_initial
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_incident_summary_to_text"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "incidents",
        "summary",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=False,
        postgresql_using="summary::text",
    )


def downgrade() -> None:
    op.alter_column(
        "incidents",
        "summary",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using="left(summary, 255)",
    )
