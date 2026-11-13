# Portfolio Audience Guide

This project is structured as a layered portfolio artifact for GitHub. Each audience should be able to find the right level of detail quickly.

## What Each Audience Looks For

| Audience | Typical time | Primary questions | Where to look in this repo |
|---|---:|---|---|
| **Recruiter / hiring manager (screening)** | 30–90 seconds | Is this a real, clear, well-scoped project with measurable outcomes? | [README](../README.md): business problem, key findings table, recommendations, visuals, tech stack, status |
| **Executive / business stakeholder** | < 2 minutes | What was found, why it matters, and what to do next? | [Executive summary](executive_summary.md), [Strategic recommendations](strategic_recommendations.md), README key findings/recommendations and charts (`docs/assets/`) |
| **Manager / product-ops stakeholder** | A few minutes | Are business questions clear and are recommendations actionable and prioritized? | [Project charter](project_charter.md), [Strategic recommendations](strategic_recommendations.md), [Executive summary](executive_summary.md), [KPI definitions](olist/03_kpi_definitions.md) |
| **Data analyst / analytics engineer** | Minutes–hours | Are metrics valid, is the logic/grain correct, is it reproducible and trustworthy? | [Research design](research_design.md), [Data dictionary](data_dictionary.md), [KPI definitions](olist/03_kpi_definitions.md), [Analysis pitfalls](olist/04_pitfalls.md), `queries/`, `src/`, `scripts/`, `notebooks/00–05`, `tests/`, validation artifacts (`docs/olist/analytics_validation.json`, `outputs/findings/*` when regenerated) |

## Layered Reading Path

1. **30 seconds:** README problem statement + key findings (numbers) + recommendations.
2. **5 minutes:** README visuals, [executive summary](executive_summary.md), [strategic recommendations](strategic_recommendations.md).
3. **Deep dive:** Reproduce via README steps/pipeline, inspect SQL and modules, review data quality/grain checks, KPI governance, and limitations.

## Communication Principles (applied)

- **Business framing first:** Questions, decision context, and stakeholder relevance are explicit.
- **Evidence with guardrails:** Every metric states source, `order_status` filter, and grain; KPIs are approved in a single dictionary.
- **Insight over EDA:** Findings answer “so what” and lead to prioritized, owner-aware recommendations.
- **Honesty:** Observational 2016–2018 scope; associations are not causal; limitations and data-handling notes are documented.
- **Reproducibility:** Pipeline, validation, tests, and regeneration steps are documented and runnable.