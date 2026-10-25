-- Explicit, configurable standings tie-breaker.
ALTER TABLE tournaments ADD COLUMN tie_breaker TEXT NOT NULL DEFAULT 'goal_difference'
CHECK(tie_breaker IN ('goal_difference', 'head_to_head', 'goals_for', 'wins'));

PRAGMA user_version=5;
