# Task Progress

## 2025-10-09
- Repaired adaptive-K retrieval scaling by forcing cache-underfilled plans to refresh, surfacing coverage diagnostics, and extending the adaptive rewrite regression. Validation logs captured via the focused pytest sweep confirm the new metrics and fetch-plan telemetry.【F:baseline/logs/test-adaptive-rewrite-20251009T230049Z.log†L1-L21】
- Stabilised the scheduler benchmark guard: the refreshed script run recorded
  119.82/237.54 tasks/s means with tight per-sample variance, and the focused
  pytest now enforces the ≥1.7× per-sample speedup guard.【a8f96b†L1-L5】【e862eb†L1-L10】
