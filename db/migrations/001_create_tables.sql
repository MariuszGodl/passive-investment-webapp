-- 001_create_tables.sql
-- Creates the core schema for the passive investment app.

BEGIN;

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
    product_id            INTEGER        NOT NULL REFERENCES product(id) ON DELETE CASCADE, -- derived from csv: kod_lokaty
    variant_code          VARCHAR(30)    NOT NULL UNIQUE,  -- csv: kod_wariantu
    valid_from            DATE           NOT NULL,         -- csv: data_od
    valid_to              DATE,                            -- csv: data_do (NULL = currently active)
    interest_rate         DECIMAL(6, 4)  NOT NULL,         -- csv: oproc
    rate_type             rate_type      NOT NULL,         -- csv: rodzaj_oproc (stałe→fixed, zmienne→variable)
    term_value            DECIMAL(8, 2),                   -- csv: okres
    term_unit             term_unit,                       -- csv: okres_typ (mies.→months, dni→days)
    term_days             INTEGER,                         -- computed from okres + okres_typ
    min_amount            DECIMAL(14, 2),                  -- csv: min_kwota
    max_amount            DECIMAL(14, 2),                  -- csv: max_kwota
    currency              VARCHAR(3)     NOT NULL DEFAULT 'PLN', -- csv: min_kwota_waluta / max_kwota_waluta (merged)
    capitalization        capitalization,                   -- csv: kapitalizacja
    additional_condition  TEXT,                             -- csv: dodatkowy_warunek
    created_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Active offers (valid_to IS NULL = currently active)
CREATE INDEX idx_offer_variant_active
    ON offer_variant (valid_to)
    WHERE valid_to IS NULL;

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

COMMIT;
