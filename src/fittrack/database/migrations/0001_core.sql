-- Migration 0001: Core tables
-- All 10 entities + indexes. No ORM — Python accesses via JSON Duality Views (0002).

-- ─── Users ────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    user_id             RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    email               VARCHAR2(255) NOT NULL,
    password_hash       VARCHAR2(255) NOT NULL,
    email_verified      NUMBER(1)     DEFAULT 0              NOT NULL,
    email_verified_at   TIMESTAMP,
    status              VARCHAR2(20)  DEFAULT 'pending'      NOT NULL
                        CHECK (status IN ('pending','active','suspended','deactivated')),
    role                VARCHAR2(20)  DEFAULT 'user'         NOT NULL
                        CHECK (role IN ('user','premium','admin')),
    premium_expires_at  TIMESTAMP,
    point_balance       NUMBER(10)    DEFAULT 0              NOT NULL,
    version             NUMBER(10)    DEFAULT 1              NOT NULL,  -- optimistic lock
    last_login_at       TIMESTAMP,
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,

    CONSTRAINT uk_users_email      UNIQUE (email),
    CONSTRAINT chk_point_balance   CHECK (point_balance >= 0),
    CONSTRAINT chk_version_positive CHECK (version >= 1)
)
/

CREATE INDEX idx_users_status ON users(status)
/

-- ─── Profiles ─────────────────────────────────────────────────────────────────
CREATE TABLE profiles (
    profile_id          RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    user_id             RAW(16)       NOT NULL               REFERENCES users(user_id),
    display_name        VARCHAR2(50)  NOT NULL,
    date_of_birth       DATE          NOT NULL,
    state_of_residence  VARCHAR2(2)   NOT NULL,
    biological_sex      VARCHAR2(10)  NOT NULL
                        CHECK (biological_sex IN ('male','female')),
    age_bracket         VARCHAR2(10)  NOT NULL
                        CHECK (age_bracket IN ('18-29','30-39','40-49','50-59','60+')),
    fitness_level       VARCHAR2(20)  NOT NULL
                        CHECK (fitness_level IN ('beginner','intermediate','advanced')),
    tier_code           VARCHAR2(20)  NOT NULL,
    height_inches       NUMBER(3),
    weight_pounds       NUMBER(5,1),
    goals               JSON,
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,

    CONSTRAINT uk_profiles_user UNIQUE (user_id)
)
/

CREATE INDEX idx_profiles_tier ON profiles(tier_code)
/

-- ─── Tracker Connections ──────────────────────────────────────────────────────
CREATE TABLE tracker_connections (
    connection_id       RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    user_id             RAW(16)       NOT NULL               REFERENCES users(user_id),
    provider            VARCHAR2(20)  NOT NULL
                        CHECK (provider IN ('apple_health','google_fit','fitbit')),
    is_primary          NUMBER(1)     DEFAULT 0              NOT NULL,
    -- Tokens stored AES-256-GCM encrypted via OCI Vault DEK
    access_token_enc    VARCHAR2(4000),
    refresh_token_enc   VARCHAR2(4000),
    token_expires_at    TIMESTAMP,
    last_sync_at        TIMESTAMP,
    sync_status         VARCHAR2(20)  DEFAULT 'pending'      NOT NULL
                        CHECK (sync_status IN ('pending','syncing','success','error')),
    error_message       VARCHAR2(500),
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,

    CONSTRAINT uk_connection_user_provider UNIQUE (user_id, provider)
)
/

CREATE INDEX idx_connections_user ON tracker_connections(user_id)
/

-- ─── Activities ───────────────────────────────────────────────────────────────
CREATE TABLE activities (
    activity_id         RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    user_id             RAW(16)       NOT NULL               REFERENCES users(user_id),
    connection_id       RAW(16)                              REFERENCES tracker_connections(connection_id),
    external_id         VARCHAR2(255),
    activity_type       VARCHAR2(30)  NOT NULL
                        CHECK (activity_type IN ('running','walking','cycling','swimming',
                                                 'strength_training','yoga','hiit','other')),
    start_time          TIMESTAMP     NOT NULL,
    end_time            TIMESTAMP,
    duration_minutes    NUMBER(5),
    intensity           VARCHAR2(20)
                        CHECK (intensity IN ('low','moderate','high','very_high')),
    metrics             JSON,
    points_earned       NUMBER(5)     DEFAULT 0              NOT NULL,
    processed           NUMBER(1)     DEFAULT 0              NOT NULL,
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,

    CONSTRAINT uk_activity_external UNIQUE (user_id, connection_id, external_id)
)
/

CREATE INDEX idx_activities_user_date   ON activities(user_id, start_time)
/
CREATE INDEX idx_activities_unprocessed ON activities(processed)
/

-- ─── Point Transactions ───────────────────────────────────────────────────────
CREATE TABLE point_transactions (
    transaction_id      RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    user_id             RAW(16)       NOT NULL               REFERENCES users(user_id),
    transaction_type    VARCHAR2(20)  NOT NULL
                        CHECK (transaction_type IN ('earn','spend','adjust','expire')),
    amount              NUMBER(10)    NOT NULL,
    balance_after       NUMBER(10)    NOT NULL               CHECK (balance_after >= 0),
    reference_type      VARCHAR2(30),
    reference_id        RAW(16),
    description         VARCHAR2(255),
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL
)
/

CREATE INDEX idx_transactions_user ON point_transactions(user_id, created_at)
/

-- ─── Sponsors (referenced by prizes) ─────────────────────────────────────────
CREATE TABLE sponsors (
    sponsor_id          RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    name                VARCHAR2(255) NOT NULL,
    contact_name        VARCHAR2(255),
    contact_email       VARCHAR2(255),
    contact_phone       VARCHAR2(20),
    website_url         VARCHAR2(500),
    logo_url            VARCHAR2(500),
    status              VARCHAR2(20)  DEFAULT 'active'       NOT NULL
                        CHECK (status IN ('active','inactive')),
    notes               CLOB,
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL
)
/

-- ─── Drawings ─────────────────────────────────────────────────────────────────
CREATE TABLE drawings (
    drawing_id          RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    drawing_type        VARCHAR2(20)  NOT NULL
                        CHECK (drawing_type IN ('daily','weekly','monthly','annual')),
    name                VARCHAR2(255) NOT NULL,
    description         CLOB,
    ticket_cost_points  NUMBER(6)     NOT NULL               CHECK (ticket_cost_points > 0),
    drawing_time        TIMESTAMP     NOT NULL,
    ticket_sales_close  TIMESTAMP     NOT NULL,
    eligibility         JSON,
    status              VARCHAR2(20)  DEFAULT 'draft'        NOT NULL
                        CHECK (status IN ('draft','scheduled','open','closed','completed','cancelled')),
    total_tickets       NUMBER(10)    DEFAULT 0              NOT NULL,
    random_seed         VARCHAR2(255),
    created_by          RAW(16)                              REFERENCES users(user_id),
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL,
    completed_at        TIMESTAMP
)
/

CREATE INDEX idx_drawings_status ON drawings(status, drawing_time)
/

-- ─── Tickets ──────────────────────────────────────────────────────────────────
CREATE TABLE tickets (
    ticket_id                RAW(16)    DEFAULT SYS_GUID()  PRIMARY KEY,
    drawing_id               RAW(16)    NOT NULL            REFERENCES drawings(drawing_id),
    user_id                  RAW(16)    NOT NULL            REFERENCES users(user_id),
    ticket_number            NUMBER(10),
    purchase_transaction_id  RAW(16)                        REFERENCES point_transactions(transaction_id),
    is_winner                NUMBER(1)  DEFAULT 0           NOT NULL,
    prize_id                 RAW(16),
    created_at               TIMESTAMP  DEFAULT SYSTIMESTAMP NOT NULL
)
/

CREATE INDEX idx_tickets_drawing ON tickets(drawing_id)
/
CREATE INDEX idx_tickets_user    ON tickets(user_id, drawing_id)
/

-- ─── Prizes ───────────────────────────────────────────────────────────────────
CREATE TABLE prizes (
    prize_id            RAW(16)       DEFAULT SYS_GUID()     PRIMARY KEY,
    drawing_id          RAW(16)       NOT NULL               REFERENCES drawings(drawing_id),
    sponsor_id          RAW(16)                              REFERENCES sponsors(sponsor_id),
    rank                NUMBER(3)     NOT NULL               CHECK (rank >= 1),
    name                VARCHAR2(255) NOT NULL,
    description         CLOB,
    value_usd           NUMBER(10,2),
    quantity            NUMBER(3)     DEFAULT 1              NOT NULL CHECK (quantity >= 1),
    fulfillment_type    VARCHAR2(20)
                        CHECK (fulfillment_type IN ('digital','physical')),
    image_url           VARCHAR2(500),
    created_at          TIMESTAMP     DEFAULT SYSTIMESTAMP   NOT NULL
)
/

CREATE INDEX idx_prizes_drawing ON prizes(drawing_id)
/

-- ─── Prize Fulfillments ───────────────────────────────────────────────────────
CREATE TABLE prize_fulfillments (
    fulfillment_id       RAW(16)      DEFAULT SYS_GUID()     PRIMARY KEY,
    ticket_id            RAW(16)      NOT NULL               REFERENCES tickets(ticket_id),
    prize_id             RAW(16)      NOT NULL               REFERENCES prizes(prize_id),
    user_id              RAW(16)      NOT NULL               REFERENCES users(user_id),
    status               VARCHAR2(30) DEFAULT 'pending'      NOT NULL
                         CHECK (status IN ('pending','notified','address_confirmed',
                                          'shipped','delivered','forfeited')),
    shipping_address     JSON,
    tracking_number      VARCHAR2(100),
    carrier              VARCHAR2(50),
    notes                CLOB,
    notified_at          TIMESTAMP,
    address_confirmed_at TIMESTAMP,
    shipped_at           TIMESTAMP,
    delivered_at         TIMESTAMP,
    forfeit_deadline_at  TIMESTAMP,
    created_at           TIMESTAMP    DEFAULT SYSTIMESTAMP   NOT NULL,
    updated_at           TIMESTAMP    DEFAULT SYSTIMESTAMP   NOT NULL
)
/

CREATE INDEX idx_fulfillments_user   ON prize_fulfillments(user_id)
/
CREATE INDEX idx_fulfillments_status ON prize_fulfillments(status)
/
