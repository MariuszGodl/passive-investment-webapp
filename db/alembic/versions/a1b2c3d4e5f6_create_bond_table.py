"""create bond table

Revision ID: a1b2c3d4e5f6
Revises: 2c30aa35fb1e
Create Date: 2026-11-03 17:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "2c30aa35fb1e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text("""
CREATE TABLE bond (
    id                      SERIAL PRIMARY KEY,
    symbol                  VARCHAR(30)    NOT NULL UNIQUE,
    name                    VARCHAR(30)    NOT NULL,
    duration                VARCHAR(30)    NOT NULL,
    rate_type               rate_type      NOT NULL,
    interest_mechanism      TEXT,
    interest_rate           DECIMAL(6, 4)  NOT NULL,
    capitalization          VARCHAR(30),
    interest_payout         BOOLEAN,
    interest_payout_freq    VARCHAR(30),
    inflation_indexed       BOOLEAN,
    early_redemption        BOOLEAN,
    institution_name        VARCHAR(255),
    cash_flow_dates         TEXT,
    cash_flow_names         TEXT,
    additional_requirement_1 TEXT,
    additional_requirement_2 TEXT,
    created_at              TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP TABLE IF EXISTS bond;"))
