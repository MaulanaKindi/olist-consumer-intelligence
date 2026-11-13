# Dataset License and Usage Notes

**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)  
**Project:** OLIST-CI-02 (Olist Consumer Intelligence & Market Intelligence Assessment)

## Source and terms
- **Source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **License/terms:** Governed by Kaggle and the dataset publisher (Olist). The exact license and permitted uses must be verified on the dataset page before any public release, redistribution, or commercial use.
- This repository does **not** relicense the source data. Raw CSVs, derived databases, and any extracts remain subject to the original dataset terms.

## Data handling in this repository
- Raw data files are expected under `data/raw/` and the DuckDB warehouse under `db/`; these paths are gitignored by default to avoid committing large/proprietary artifacts.
- Analytical outputs (`outputs/`), generated profiles, and reports are derived from the dataset and should be reviewed for compliance before publication.
- The data is anonymized by the publisher; do not attempt re-identification or combine with external sources in ways that violate terms or privacy expectations.

## Attribution
When publishing results, cite the dataset and Olist/Kaggle as required by the dataset page, and clearly state the analysis period (2016–2018) and observational limitations.

## Pre-publication checklist
- [ ] Confirm current license/terms on Kaggle dataset page.
- [ ] Ensure no raw data, credentials, or large binaries are committed.
- [ ] Include attribution and limitations in public-facing reports/README.
- [ ] Obtain any required permissions for redistribution of derived artifacts if applicable.
