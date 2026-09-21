"""Create the initial PostgreSQL schema.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-09-18
"""
from pathlib import Path

from alembic import op


revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "backend" / "database" / "schema.sql"
    op.execute(schema_path.read_text(encoding="utf-8"))


def downgrade() -> None:
    raise NotImplementedError(
        "El baseline no tiene downgrade automático; restaura un respaldo de la base de datos"
    )