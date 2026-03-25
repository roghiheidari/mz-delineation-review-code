# Management Zone Delineation Review – Code & Pipelines
 
Associated manuscript: *The Evolution of Data-Driven Management Zone Delineation: A Systematic Review*
 
This repository contains the prompt templates and analysis scripts referenced in the review paper on within-field management zone delineation in precision agriculture.
 
The goal is to support transparency and reproducibility of the review workflow. To avoid copyright and licensing issues, the repository does **not** include publisher PDFs, full-text content, or proprietary database exports.
 
## Contents
 
- `keyword_scoring/`
  - Evidence-based keyword scoring used to prioritize Q1 abstracts for manual screening.
- `ai_screening/`
  - The canonical inclusion/exclusion prompt template and a runnable full-text screening helper.
- `extraction_pipeline/`
  - Script used to prefill the review/extraction table.

## Public database (GitHub Pages)

This repository also hosts a lightweight, reviewer-facing database website (GitHub Pages) under `docs/`.

- The website is a searchable/filterable table built from the final curated extraction files (study-level variables, methods/workflows, data used for MZ, validation codes, and screening metadata).
- The site does not include PDFs/full text. To reduce copyright risk, long text fields are truncated in-table with a "Show more" expansion - Also, from the abstract we show only 300 first characters.
- Access the project page: [https://roghiheidari.github.io/mz-delineation-review-code/](https://roghiheidari.github.io/mz-delineation-review-code/)

### Suggested acknowledgement

"Database and web interface created by Reza Khanmohammadi, Roghayeh Heidari, and Faramarz F. Samavati."

### Citation (BibTeX)

```bibtex
@dataset{khanmohammadi2026mzreviewdb,
  author       = {Khanmohammadi, Reza and Heidari, Roghayeh and Samavati, Faramarz F.},
  title        = {Management Zone Delineation Review Database},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.18945916},
  url          = {https://doi.org/10.5281/zenodo.18945916}
}
```

## What is included / excluded
 
- Included:
  - Prompt.
  - Scoring logic and full keyword lists.
  - Scripts used in the processing pipeline.
 
- Not included:
  - Full bibliographic databases (RIS/CSV exports).
  - Full-text PDFs or extracted full-text files.
  - Screening outputs (CSV logs) and intermediate analysis tables.
  - API keys or credentials.
 
## 1) Keyword scoring (From Q1 papers abstracts)
 
Folder: `keyword_scoring/`
 
- `score_and_filter_papers.py`
  - Implements the evidence-based category scoring described in the manuscript.
  - Each category contributes its weight at most once per abstract.
  - Adds a completeness bonus when at least one methods keyword, one data keyword, and one results/validation keyword are present.
 

## 2) AI-assisted screening
 
Folder: `ai_screening/`
 
### Title/abstract screening prompt
 
- `AI_SCREENING_PROMPTS.txt`
  - Canonical inclusion/exclusion prompt template and required output format for title/abstract screening.
  - This file is the "final query" / prompt template referenced for abstract screening.
 
### Full-text screening helper (local)
 
- `fulltext_screening.py`
  - Uses a local Ollama model (via the `ollama` CLI) to produce a structured INCLUDE/EXCLUDE/UNCERTAIN suggestion from full-text excerpts.
  - Writes `FULLTEXT_AI_SCREENING.csv` to an analysis directory for human review.
 
#### Minimal setup
 
1. Install Ollama and ensure `ollama` is on your PATH.
2. Place plain-text full-text files in:
   - `<output_root>/full_text/*.txt`
 
#### Example run
 
From the repository root:
 
```bash
python -m ai_screening.fulltext_screening
```
 
## 3) Extraction pipeline / review table prefill
 
Folder: `extraction_pipeline/`
 
- `prefill_full_review_table.py`
  - Prefills an extraction/review table template (CSV) by joining intermediate screening metadata files.

- `xml_extraction_rules_prompt.md`
  - Rules and structured XML output format used for study-level extraction.
