# Data Analysis Standards (SQL and Python)

## Language
- All project artifacts are written in English: code, identifiers, comments, docstrings, documentation, file names, commit messages, and report text.
- Use proper, consistent English: correct grammar, American spelling, concise sentences.
- Use consistent terminology. Pick one term per concept and reuse it (for example always "order", never alternating with "purchase").
- Keep original source values as-is (for example Portuguese product category names). Document their English translation separately instead of altering the data.
- Reply to the user in Indonesian in the chat. (Change this line to "Reply to the user in English." if English replies are preferred.)

## General
- Reproducible: results must be repeatable from raw data via scripts, with no undocumented manual steps.
- Raw data (schema raw) is never modified. Transformations happen only in staging and analytics.
- Consistent: snake_case names, ISO date formats, explicit units.
- Single source of truth for metrics: use the KPI dictionary. Do not silently invent new definitions; propose them first.
- Document assumptions, filters, and the reasons for them in comments or docs.
- Validate after each transformation: row counts, nulls, duplicates, value ranges, and total reconciliation.

## SQL
- State the grain of each table (1 row = what) before joining. Put the grain in a comment.
- No SELECT *; list columns explicitly.
- Use clearly named CTEs; avoid nested subqueries.
- Be explicit about join type, order_status filter, and NULL handling.
- Idempotent: use CREATE OR REPLACE so scripts can be rerun.
- After a join, check whether row counts inflated, and never sum order-level values at item level.

## Python
- No hardcoded paths, parameters, or credentials; use configuration and .env (never commit .env).
- Small testable functions; move stable logic from notebooks into scripts or modules.
- Set random seeds and pin library versions in requirements.txt.
- Notebooks must run top to bottom without errors.

## Output
- For every number, state the source table, filter, and grain.
- State data limitations. Distinguish correlation from causation.
