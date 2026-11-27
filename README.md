# DHJ-26-2097

Supporting materials for *Functional Structure of China's Hospital Digital Health Ecosystem: A Multi-Source Observational Study*, submitted to *Digital Health*.

This repository recalculates the principal point estimates from aggregate inputs. These cover functional composition, cross-source divergence, within-hospital differences, the functional distribution of documented AI/ADS, survey and award trends, and whole-lot planned-budget shares. Table S15a follows the hospital sample from 638 initially matched hospitals to the 53 included in the paired comparison.

## Run the analysis

With Python 3.9 or later, run the following command from the repository directory. The script uses the Python standard library.

```sh
python analysis.py
```

Run `python analysis.py --json` for the complete numeric output, including all domains and AI/ADS assessment states. The other two files are the [English coding manual](Supplementary-File-1-Codebook-v1.3.pdf) and the [aggregate inputs](analysis-input.csv). The study archive holds the source records, first reviewer answers and cluster-resampling inputs. This four-file companion covers point estimates.

## Read the estimates

| Manuscript location | Result reproduced by the script |
|---|---|
| Table 2 and Figure 2a | At CHIMA 2025, infrastructure leads exhibitor positioning (21.5%) and hospital requirements (22.2%). Clinical care leads supplier-linked awards (33.5%). Survey items have an equal-item profile in Figure 2a. |
| Figure 2b and cross-event comparison | Over seven shared domains, CHIMA EPSP–HPD, SRE–EPSP and SRE–HPD Jensen–Shannon divergences (JSDs) are 0.0102, 0.1124 and 0.1219 bits. Across all eight domains in DMHC, EPSP–HPD is 0.0235 and EPSP–SLPA is 0.1412 bits. |
| Figure 2c and Table S15a | Both sides have records at 638 hospitals. After shared projects are removed, 633 remain. Both sides have functional evidence at 539 hospitals and at least three classifiable units each at 53. These 53 hospitals contribute 671 requirement lots and 255 awards. For awards minus requirements, clinical care differs by +16.6 and infrastructure by −13.8 percentage points. |
| Figure 3 | On the common survey panel, the selection-rate-weighted Data Intelligence share is 26.8%, 28.3% and 31.4%. Using all items gives 28.6%, 33.3% and 34.1%. Clinical care has the largest award share in each year, at 39.4%, 37.0% and 37.1%. |
| Figure 4 | CHIMA has 715 expanded-AI/ADS-positive requirement lots among 2,184 assessable lots. Of the 713 positives with a documented function, 560 (78.5%) include a function outside Data Intelligence and 308 (43.2%) have all documented functions outside that domain. |
| Table S20 | Among 1,878 CHIMA lots with verified planned budgets, 388 (20.7%) are expanded-positive. They account for 38.1% of total budget, or 30.9% after removing the largest 1% of budgets. |

## Observation and coding examples

The eight domains describe the task performed. Strict AI and expanded AI/algorithmic decision support (AI/ADS) describe the documented technology independently. The coding unit and its own supporting passage determine which labels apply.

| Observation and unit | Example with a source locator |
|---|---|
| **SRE — Supplier-Reported Expectations.** One survey question in one module and cycle. | “人工智能/大模型” (AI/large language models), selected by 202/248 respondents. The question directly names the technology and supports Data Intelligence (E), Strict AI and expanded AI/ADS. See PDF p. 42, Table 5.3, row 1. [CHIMA 2024–2025 supplier survey](https://www.chima.org.cn/Html/News/Articles/17430.html) |
| **EPSP — Exhibitor Product–Service Positioning.** One exhibitor at one edition. | In the CHIMA 2025 handbook entry for Odin Health, paragraphs 298–300 describe “多种数据交换能力” and “AI增强型…中间件产品”. The handbook supports Interoperability and Integration (B) and the two AI tags for the displayed middleware. See Supplementary Table S2 for the handbook-only example. |
| **HPD — Hospital Procurement Demand.** One formal requirement lot. | In Shenzhen tender LGZXCG-2025-0007, Chapter 3, technical requirements, service item 1, the hospital calls for patient navigation using “大模型预训练、微调与推理技术”. The passage supports Patient-facing Services (D) and both AI tags for the required service. [Shenzhen procurement notice and tender documents](https://www.szggzy.com/globalSearch/details.html?contentId=20033809) |
| **SLPA — Supplier-Linked Procurement Awards.** The attributable award scope of a named legal supplier. | Zhejiang award ZJWS2024-JJ126, sections III and IV, names 北京惠每云科技有限公司 and specifies “肿瘤规范化管理系统” for Taizhou Enze Medical Center. The awarded clinical oncology system supports Clinical Care and Workflow (A). SLPA is coded for functions only. [Zhejiang government procurement award notice](https://zfcg.czt.zj.gov.cn/site/detail?categoryCode=ZcyAnnouncement&parentId=600007&articleId=Ov2kUfNjhzFqukGU8afxnw%3D%3D) |

## What the aggregate input contains

Each row is keyed by `block`, `frame`, `period`, `observation`, `scheme`, `group` and `category`. The last two columns store the numerator and denominator. Domain mass is recorded as an integer or an exact fraction (for example, `7/3`). Planned budgets are in CNY. A count-only row has denominator 1. Reported percentages are rounded only for display.

- **Functional composition.** Each classifiable unit contributes a total weight of one divided equally among its evidenced domains. The denominators of the `profile`, `survey_profile`, `award_profile` and `paired_profile` blocks are the sums of the corresponding unit or selection-rate weights. `coverage` and `award_coverage` give classifiable and included counts. SRE did not separately measure B. Comparisons involving SRE use seven shared domains and renormalise each profile. The conference comparison without SRE uses eight. JSD is base 2.
- **Time and conference.** The three SRE waves are repeated cross-sections. The common panel has 23 items and 16 classifiable items per wave. For the middle wave the retained large-language-model option has the report’s 56/197 response (28.43%). The similar 10/197 option is kept as a distinct source entry and is not added to its weight. Annual hospital awards use the union of three CHIMA exhibitor rosters. The 2025 cross-section uses the corresponding event’s own roster. DMHC retains its full frame. The two HPD samples share 3,605 lots (5,893 unique lots).
- **Within-hospital comparison.** `matching_flow` records the number of hospitals and the eligible records on each side at each stage. The final `paired_profile` groups are 53 anonymous matched hospitals. Within each hospital calculate the two profiles separately. Average their within-hospital differences with equal hospital weights.
- **AI/ADS.** `ai_state` retains the four source states for each applicable tag. The assessable denominator is positive plus reviewed text without a positive finding. `ai_embedding` counts E only, E with another domain, and entirely outside E, among positives with an evidenced function. `outside_coverage` counts each evidenced non-E domain among the last group. A multi-domain lot can contribute to several domain counts. SLPA contributes no AI/ADS observations.
- **Budget.** `budget_count` and `budget_cny` use the same verified positive-budget HPD lots, separately for each tag and conference. The amount belongs to the entire lot. The trimmed analysis removes the largest 1% of lots by budget, rounding the number removed upward in each frame.

The coding rules are v1.3, with the 24 November 2026 terminology update. The release uses the signed 23 November functional and AI/ADS coding, the paper’s source-verified middle-wave survey rate, and the 27 November 2026 Chinese manuscript master.

