# Project Charter

## Brazilian E-Commerce: Consumer Behavior, Experience & Market Intelligence

**Project ID:** OLIST-CI-02  
**Project Type:** Consumer Intelligence / Market Intelligence  
**Primary Decision Audience:** E-commerce Marketplace Management  
**Dataset:** Brazilian E-Commerce Public Dataset by Olist  
**Data Period:** 2016–2018  
**Status:** Draft v0.1

### 1. Project Background

The growth of e-commerce has increased the importance of understanding consumer purchasing behavior and customer experience. Transactional data provides valuable evidence of how consumers interact with an online marketplace, what they purchase, and how their shopping experiences are reflected in customer feedback.

However, transactional records, product information, payment data, delivery records, and customer reviews often exist in separate datasets. An integrated analytical approach is therefore necessary to develop a more comprehensive understanding of consumer behavior and marketplace performance.

This project uses the Brazilian E-Commerce Public Dataset by Olist to develop an evidence-based consumer intelligence assessment.

### 2. Business Context

E-commerce marketplaces generate substantial amounts of transactional and operational data through consumer purchases, payment activities, product information, delivery processes, and customer feedback.

These data can provide valuable insights into purchasing behavior, customer experience indicators, product-category performance, and geographic variations.

From a marketplace management perspective, analyzing these dimensions can help identify behavioral patterns, operational challenges, and potential commercial opportunities.

This project adopts an independent analytical perspective, using publicly available historical data from the Olist marketplace to develop consumer and marketplace intelligence insights. The analysis does not assume access to Olist's internal management priorities or decision-making processes.

### 3. Business Problem Statement

Understanding consumer purchasing behavior and marketplace experience requires an integrated analysis of transactional, product, payment, delivery, review, and geographic data.

However, these datasets must be systematically integrated and evaluated before meaningful behavioral patterns, customer experience indicators, and potential commercial improvement opportunities can be identified.

This project addresses this analytical challenge by developing an evidence-based assessment of consumer behavior and marketplace experience using historical data from the Olist e-commerce marketplace.

### 4. Project Objectives

The project aims to:

1. Examine consumer purchasing behavior and transaction patterns, including purchase frequency, repeat purchases, and order value.
2. Analyze the relationships between delivery performance, freight costs, and customer review scores as an observable proxy for customer satisfaction.
3. Identify differences in purchasing patterns and customer review scores across product categories.
4. Examine geographic variations in consumer purchasing behavior and delivery performance.
5. Translate validated analytical findings into evidence-based strategic recommendations for e-commerce marketplace management.

### 5. Research Objectives

The research will investigate four analytical domains:

- Consumer Purchase Behavior
- Consumer Experience Intelligence
- Product & Category Intelligence
- Geographic Consumer Intelligence

The analysis will prioritize descriptive and diagnostic methods, with statistical testing and segmentation applied where appropriate and supported by the available data.

### 6. Research Questions

**RQ1.** What patterns characterize consumer purchasing behavior on the Olist marketplace?

**RQ2.** How are delivery performance and freight costs associated with customer review scores?

**RQ3.** How do purchasing patterns and customer review scores differ across product categories?

**RQ4.** How do consumer purchasing patterns and delivery performance vary across geographic regions?

### 7. Project Scope and Boundaries

**In Scope**
- Historical consumer transaction analysis.
- Purchase frequency and repeat-purchase behavior.
- Order value and payment patterns.
- Customer review and delivery performance analysis.
- Product-category purchasing patterns.
- Geographic purchasing and delivery patterns.
- Evidence-based strategic recommendations.

**Out of Scope**
- Direct competitor benchmarking and market share estimation.
- Claims about the entire Brazilian e-commerce market.
- Causal claims without an appropriate causal identification strategy.
- Real-time consumer behavior or current market conditions.
- Psychological or motivational interpretations not directly supported by the dataset.

### 8. Stakeholder and Decision Context

**Primary stakeholder:** E-commerce marketplace management.

**Secondary stakeholders:**
- Customer experience and operations teams.
- Category and commercial management teams.
- Seller and merchant management teams.

The intelligence outputs are intended to inform decisions concerning customer experience improvement, category prioritization, and geographic operational opportunities.

### 9. Expected Deliverables

1. Project Charter and Research Design.
2. Data Provenance and Data Quality Assessment.
3. Reproducible Analytical Dataset and SQL Scripts.
4. Consumer Behavior and Experience Analysis.
5. Product-Category and Geographic Intelligence Findings.
6. Strategic Opportunity and Recommendation Matrix.
7. Executive Intelligence Report.
8. Supporting Dashboard and GitHub Portfolio Documentation.

### 10. Success Criteria

The project will be considered successful when:

- Data sources and transformations are documented and traceable.
- Data quality and referential integrity are systematically assessed.
- Analytical methods are appropriate for the research questions.
- Findings are supported by reproducible calculations.
- Interpretations distinguish evidence from assumptions and limitations.
- Recommendations are relevant to identifiable management decisions.
- Analytical outputs are reproducible and professionally documented.

### 11. Key Limitations

The Olist dataset represents activity from a single Brazilian e-commerce marketplace during 2016–2018. It does not represent the entire Brazilian market or the current e-commerce environment.

Customer review data is available only for orders with submitted reviews. Customer identifiers must be interpreted carefully, and multi-table joins must preserve the appropriate analytical grain.

The findings should therefore be interpreted as marketplace-specific historical intelligence rather than universal consumer behavior evidence.

### 12. Data Source

Olist Brazilian E-Commerce Public Dataset:  
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Dataset licensing, redistribution conditions, and attribution requirements must be verified before public release.