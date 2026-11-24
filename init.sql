CREATE TABLE IF NOT EXISTS predictions (
    id            SERIAL PRIMARY KEY,
    created_at    TEXT             NOT NULL,
    filename      VARCHAR(255)     NOT NULL,
    label         VARCHAR(64)      NOT NULL,
    display_label VARCHAR(96)      NOT NULL,
    fruit         VARCHAR(48)      NOT NULL,
    state         VARCHAR(16)      NOT NULL,
    confidence    DOUBLE PRECISION NOT NULL,
    top_k         TEXT             NOT NULL,
    latency_ms    DOUBLE PRECISION NOT NULL,
    thumbnail     TEXT
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_state ON predictions (state);