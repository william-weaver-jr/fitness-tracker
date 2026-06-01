-- Migration 0003: Audit columns and functional JSON indexes
-- Adds created_by/updated_by where missing, adds indexes on JSON paths
-- queried through Duality Views to avoid full scans.

-- ─── Functional indexes on profile tier_code (already a column, skip) ─────────

-- ─── JSON functional index on activities.metrics (heart_rate, steps) ──────────
CREATE INDEX idx_activities_metrics_hr
    ON activities (JSON_VALUE(metrics, '$.heartRateAvg'))
/

CREATE INDEX idx_activities_metrics_steps
    ON activities (JSON_VALUE(metrics, '$.steps'))
/

-- ─── JSON functional index on drawings.eligibility ────────────────────────────
CREATE INDEX idx_drawings_eligibility_min_age
    ON drawings (JSON_VALUE(eligibility, '$.minAccountAgeDays' RETURNING NUMBER))
/

-- ─── Functional index on drawing_time for scheduler queries ───────────────────
CREATE INDEX idx_drawings_time ON drawings(drawing_time)
/

-- ─── Index on tickets.is_winner for fulfillment queries ───────────────────────
CREATE INDEX idx_tickets_winner ON tickets(is_winner)
/

-- ─── Index on fulfillments.forfeit_deadline for forfeit worker ────────────────
CREATE INDEX idx_fulfillments_deadline ON prize_fulfillments(forfeit_deadline_at)
/
