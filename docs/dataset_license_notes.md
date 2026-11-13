# Dataset License and Usage Notes

**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)  
**Project:** OLIST-CI-02 (Olist Consumer Intelligence & Market Intelligence Assessment)

## Source and terms
- **Source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **License/terms (verified):** Kaggle dataset metadata (checked 2026-11-13 via dataset page/JSON-LD) lists **CC BY-NC-SA 4.0** — https://creativecommons.org/licenses/by-nc-sa/4.0/. Re-verify on the dataset page before public release, redistribution, or commercial use in case terms change.
- This repository does **not** relicense the source data. Raw CSVs, derived databases, and any extracts remain subject to the original dataset terms.

## Data handling in this repository
- Raw data files are expected under `data/raw/` and the DuckDB warehouse under `db/`; these paths are gitignored by default to avoid committing large/proprietary artifacts.
- Analytical outputs (`outputs/`), generated profiles, and reports are derived from the dataset and should be reviewed for compliance before publication.
- The data is anonymized by the publisher; do not attempt re-identification or combine with external sources in ways that violate terms or privacy expectations.

## Attribution
When publishing results, cite the dataset and Olist/Kaggle as required by the dataset page, state the analysis period (2016–2018), and include observational limitations.

## Pre-publication checklist
- [x] Confirm current license/terms on Kaggle dataset page (CC BY-NC-SA 4.0 observed 2026-11-13; re-verify before publishing).
- [x] Ensure no raw data, credentials, or large binaries are committed (`.gitignore`: `data/raw/`, `db/`, `outputs/`, env/scratch patterns).
- [x] Include attribution (Olist/Kaggle), analysis period (2016–2018), and limitations in public-facing docs (`README.md`, executive/recommendation docs).
- [ ] On public release: confirm redistribution scope for derived artifacts complies with CC BY-NC-SA 4.0 (attribution, non-commercial, share-alike as applicable) and keep attribution visible.
