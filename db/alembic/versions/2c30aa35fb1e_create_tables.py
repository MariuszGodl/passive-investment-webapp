"""create tables

Revision ID: 2c30aa35fb1e
Revises:
Create Date: 2026-09-30 19:34:38.584147

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2c30aa35fb1e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text("""
-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE product_type AS ENUM (
    'term_deposit',
    'savings_account',
    'deposit_with_fund'
);

CREATE TYPE rate_type AS ENUM (
    'fixed',
    'variable'
);

CREATE TYPE term_unit AS ENUM (
    'months',
    'days'
);

CREATE TYPE capitalization AS ENUM (
    'at_maturity',
    'monthly',
    'quarterly',
    'daily',
    'annual',
    'at_promo_end'
);

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE bank (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10)  NOT NULL UNIQUE,  -- csv: kod_banku
    name        VARCHAR(255) NOT NULL,         -- not in csv
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE product (
    id            SERIAL PRIMARY KEY,
    bank_id       INTEGER       NOT NULL REFERENCES bank(id) ON DELETE CASCADE, -- derived from csv: kod_banku
    code          VARCHAR(30)   NOT NULL,   -- csv: kod_lokaty
    name          VARCHAR(500)  NOT NULL,   -- csv: nazwa_lokaty
    product_type  product_type  NOT NULL,   -- csv: lokata/konto
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    UNIQUE (bank_id, code)
);

CREATE TABLE offer_variant (
    id                    SERIAL PRIMARY KEY,
    product_id            INTEGER        NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    variant_code          VARCHAR(30)    NOT NULL UNIQUE,
    interest_rate         DECIMAL(6, 4)  NOT NULL,
    apy                   DECIMAL(20, 16),                  -- annual percentage yield
    rate_type             rate_type      NOT NULL,
    term_value            DECIMAL(8, 2),
    term_unit             term_unit,
    term_days             INTEGER,
    currency              VARCHAR(3)     NOT NULL DEFAULT 'PLN',
    capitalization        capitalization,
    interest_payout       VARCHAR(100),
    inflation_indexed     BOOLEAN,
    early_termination     BOOLEAN,
    interest_details      TEXT,
    additional_condition  TEXT,
    created_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================



-- Sort/filter by interest rate
CREATE INDEX idx_offer_variant_rate
    ON offer_variant (interest_rate DESC);

-- Filter by term length
CREATE INDEX idx_offer_variant_term_days
    ON offer_variant (term_days);

-- Product → bank join path
CREATE INDEX idx_product_bank_id
    ON product (bank_id);

-- Offer → product join path
CREATE INDEX idx_offer_variant_product_id
    ON offer_variant (product_id);
    """)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text("""
DROP TABLE IF EXISTS offer_variant;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS bank;

DROP TYPE IF EXISTS capitalization;
DROP TYPE IF EXISTS term_unit;
DROP TYPE IF EXISTS rate_type;
DROP TYPE IF EXISTS product_type;
    """)
    )
