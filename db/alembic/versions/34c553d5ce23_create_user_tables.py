"""create user tables

Revision ID: 34c553d5ce23
Revises: a1b2c3d4e5f6
Create Date: 2026-11-13 15:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34c553d5ce23"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text("""
-- "user" is a reserved word in PostgreSQL, hence app_user
CREATE TABLE app_user (
    id             SERIAL PRIMARY KEY,
    full_name      VARCHAR(255)  NOT NULL,
    email          VARCHAR(255)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255)  NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE user_favorite (
    user_id     INTEGER      NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    variant_id  INTEGER      NOT NULL REFERENCES offer_variant(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, variant_id)
);

-- A user may invest in the same variant multiple times
CREATE TABLE user_investment (
    id                SERIAL PRIMARY KEY,
    user_id           INTEGER         NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    variant_id        INTEGER         NOT NULL REFERENCES offer_variant(id) ON DELETE CASCADE,
    amount            DECIMAL(14, 2),
    horizon_months    INTEGER,
    estimated_profit  DECIMAL(14, 2),
    apy               DECIMAL(20, 16),
    start_date        DATE            NOT NULL DEFAULT CURRENT_DATE,
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_favorite_variant_id
    ON user_favorite (variant_id);

CREATE INDEX idx_user_investment_user_id
    ON user_investment (user_id);

CREATE INDEX idx_user_investment_variant_id
    ON user_investment (variant_id);
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("""
DROP TABLE IF EXISTS user_investment;
DROP TABLE IF EXISTS user_favorite;
DROP TABLE IF EXISTS app_user;
    """)
    )
