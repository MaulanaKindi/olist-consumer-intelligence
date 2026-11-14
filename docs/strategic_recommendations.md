# Strategic Opportunity & Recommendation Matrix

**Project:** OLIST-CI-02 | **KPI basis:** `docs/olist/03_kpi_definitions.md` v1.1 (approved) | **Evidence:** `outputs/findings/analysis_findings.json`

| Priority | Observed finding (evidence, grain/filter) | Business implication | Recommendation | Owner (stakeholder) | Limitations |
|---|---|---|---|---|---|
| High | On-time/early deliveries: avg review ~4.290 (n=89,949) vs late ~2.271 (n=6,410); `on_time_delivery_rate` ~93.23%; longer buckets trend lower (review-order joined to delivery, valid reviews; delivered with estimate/days as defined) | Delivery reliability strongly associated with satisfaction | Reduce late deliveries; monitor on-time rate and lead-time buckets by lane/seller; proactive ETAs | Operations, CX, Seller management | Association not causal |
| High | Delivery days vary by state using order-level location mapping (e.g. SP ~8.3d, 41,746 orders vs several North/Northeast states ~19–24+ days; reconciled to 99,441 orders / ~16.01M BRL GMV) | Regional service gaps affect experience | Regional logistics benchmarking and SLA targets; carrier/mode options for long-haul regions | Operations, Marketplace management | Averages mask within-state variance; volume differs |
| Medium | GMV and orders concentrate in SP/RJ/MG and top categories with mixed avg reviews (item/order grain, all statuses; review averaged at distinct order-category pairs) | Growth/quality levers differ by segment | Category & region scorecards combining GMV, orders, delivery, review; act on high-revenue lower-review segments | Category/Commercial, CX | Category nulls (~1.85%); order may map to multiple categories |
| Medium | `repeat_customer_rate` ~3.12% (2,997/96,096 `customer_unique_id`, all statuses, observed period) | Limited observed repeat behavior | Validate identity linkage; if confirmed, design/test retention/cohort initiatives with approved measurement | Marketplace management, CRM/Marketing | Observed-period and linkage dependent |
| Medium | `cancellation_rate` ~0.63% (625/99,441, status canceled, all orders denominator) | Low explicit cancellation share but operationally relevant | Track cancellations by time/segment; distinguish from unavailable/unfulfilled statuses in ops reporting | Operations, Marketplace management | Status definitions per source system |

## Implementation notes
- Keep `order_status` filters and grains explicit per KPI dictionary; recompute before operational decisions.
- Track: order_count, gmv_payments, aov, repeat_customer_rate, cancellation_rate, on_time_delivery_rate, avg_delivery_days, avg_review_score by approved cuts.
- Monthly trends must respect complete month spine and partial boundary months (2016-09, 2018-09, 2018-10).
