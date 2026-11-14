# Dataset License and Usage Notes

**Dataset:** Brazilian E-Commerce Public Dataset by Olist (Kaggle)
**Project:** OLIST-CI-02 (Olist Consumer Intelligence & Market Intelligence Assessment)
**Last reviewed:** 2026-11-14

## 1. Source (verified)
- **Dataset:** Brazilian E-Commerce Public Dataset by Olist
- **Official Kaggle listing:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Dataset listing license (as displayed on Kaggle):** CC BY-NC-SA 4.0
- **Canonical license:** https://creativecommons.org/licenses/by-nc-sa/4.0/
- **Legal code:** https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en
- **Verification:** **Dataset listing license: VERIFIED ON KAGGLE (2026-11-14).** The Kaggle dataset page identifies Olist as the provider and displays CC BY-NC-SA 4.0.
- **Legal interpretation of the intended portfolio/job-application use: NOT INDEPENDENTLY RESOLVED.** A public portfolio used for job applications is not automatically commercial and not automatically non-commercial; this requires context-specific interpretation under the applicable terms and law.

## 2. CC BY-NC-SA 4.0 — Key Requirements (summary)
1. **BY (Attribution):** provide appropriate attribution, a source link, a license link, and indicate modifications made to the material.
2. **NC (NonCommercial):** use must not be primarily intended for commercial advantage or monetary compensation.
3. **SA (ShareAlike):** qualifying adapted material that is publicly shared must be distributed under the same license as the original or a compatible license (as defined by the license terms).

This is a summary, not legal advice. Consult the canonical license/legal code and qualified advice for definitive interpretation.

## 3. How This Project Uses the Dataset
- This project **uses the Olist dataset as its analytical source**.
- It **cleans, transforms, joins, and aggregates** the source data (raw → staging → analytics in DuckDB), and produces metrics, validations, notebooks, and reports.
- It **does not intentionally redistribute original raw CSV files or the local DuckDB database** in this repository (source data and DB artifacts are gitignored/local).
- It **publishes selected aggregate findings, charts, and documentation** derived from the analysis.

## 4. Material Scope Distinctions
- **A. Original Olist dataset:** governed by the dataset’s terms/license as provided by the source (Kaggle listing displays CC BY-NC-SA 4.0; verify current terms before release/use).
- **B. Project source code:** original Python, SQL, and configuration authored for this repository. The dataset license does **not** automatically apply to all original project code; however, no project-wide open-source license has been granted (see Section 6).
- **C. Analytical findings and derived outputs:** aggregate findings, charts, reports, notebooks, and transformed data are derived from the dataset. They do **not** automatically constitute Adapted Material in all cases either; whether copyright/database-right obligations or ShareAlike conditions apply depends on the specific material and applicable rights/law. Treat redistribution and public sharing conservatively and in line with verified source terms.
- **D. Third-party dependencies and assets:** libraries, tools, and any third-party content retain their respective licenses/terms.

No endorsement by Olist is implied.

## 5. Attribution (recommended text)
> Dataset: Brazilian E-Commerce Public Dataset by Olist. Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. The Kaggle dataset listing identifies the license as CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). This project uses a cleaned, transformed, and analyzed version of the source data. The original dataset is not redistributed in this repository. No endorsement by Olist is implied.

When publishing results, also state the analysis period (2016–2018, observed 2016-09-04 to 2018-10-17) and observational limitations (not causal; not representative of all/current Brazilian e-commerce). Do not invent a dataset version or claim direct permission from Olist beyond what the source page demonstrates.

## 6. Project Source-Code License — Decision Pending (no LICENSE file)
- **Current state:** no confirmed project-wide source-code license is declared in this repository (no `LICENSE` file granting reuse rights was added).
- **Implication:** public visibility on GitHub does **not** automatically grant general permission to reuse, modify, or redistribute the code. Default copyright reservation applies unless/until an explicit license is granted by the rights holder(s).
- **Future licensing:** any future code license must be limited to material the repository owner has authority to license. Upstream dataset material and third-party dependencies/assets must retain their respective licensing conditions and attributions.
- **Possible option (not adopted):** a permissive license such as **MIT** may be considered for **original project code only**, but this remains a **recommendation pending owner authorization**. No `LICENSE` file is created or committed by this remediation.

## 7. Data Handling in this Repository
- Raw data expected under `data/raw/` and DuckDB under `db/`; gitignored by default.
- Regenerable outputs in `outputs/` are gitignored by default; curated docs/assets/reports may be included intentionally.
- Data is anonymized by the publisher; do not attempt re-identification or combine with external data in ways that violate terms/privacy.

## 8. Pre-publication Checklist
- [x] **Dataset listing license verified on Kaggle (2026-11-14):** CC BY-NC-SA 4.0 displayed on https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce (canonical/legal links recorded). Re-verify before publication in case terms change.
- [ ] **Legal interpretation for intended use:** portfolio/job-application context assessed as needed (not independently resolved here).
- [x] Ensure no raw data, local DBs, credentials, or unnecessary secrets/binaries are committed (`.gitignore` covers `data/raw/`, `db/`, `outputs/`, `.env*`, scratch patterns).
- [x] Include attribution, source/license links, modification note, analysis period, and limitations in public-facing docs.
- [ ] Confirm redistribution/public-sharing scope for derived artifacts against verified terms and applicable rights.
- [ ] Obtain explicit owner authorization before selecting/publishing a project source-code license.
