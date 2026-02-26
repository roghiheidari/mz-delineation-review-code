# Management Zone Delineation Review – Code & Pipelines

This repository contains the prompt templates and analysis scripts referenced in the review paper on within-field management zone delineation in precision agriculture.

The goal is to support transparency and reproducibility of the review workflow. To avoid copyright and licensing issues, the repository does **not** include publisher PDFs, full-text content, or proprietary database exports.

## Contents

- `keyword_scoring/`
  - Evidence-based keyword scoring used to prioritize Q1 abstracts for manual screening.
- `ai_screening/`
  - The canonical inclusion/exclusion prompt template (Appendix A equivalent) and a runnable full-text screening helper.
- `extraction_pipeline/`
  - Script used to prefill the review/extraction table from intermediate CSVs generated during screening.

## What is included / excluded

- Included:
  - Prompt templates.
  - Scoring logic and full keyword lists.
  - Scripts used in the processing pipeline.

- Not included:
  - Full bibliographic databases (RIS/CSV exports).
  - Full-text PDFs or extracted full-text files.
  - Screening outputs (CSV logs) and intermediate analysis tables.
  - API keys or credentials.

## 1) Keyword scoring (Q1 abstracts)

Folder: `keyword_scoring/`

- `06_score_and_filter_papers.py`
  - Implements the evidence-based category scoring described in the manuscript.
  - Each category contributes its weight at most once per abstract.
  - Adds a completeness bonus when at least one methods keyword, one data keyword, and one results/validation keyword are present.

- `Keywords_used_for_scoring.txt`
  - Human-readable keyword groups and weights.

- `S2_Complete_keyword_list.txt`
  - Complete keyword list and scoring description (Supplementary Material S2).

## 2) AI-assisted screening

Folder: `ai_screening/`

### Title/abstract screening prompt

- `01_AI_SCREENING_PROMPTS.txt`
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

By default this expects the following folder structure under `temp_vector_pipeline/`:

- `temp_vector_pipeline/full_text/` (input `.txt` files)
- `temp_vector_pipeline/analysis/` (output CSV)

You can change this by editing `ai_screening/config.py`.

## 3) Extraction pipeline / review table prefill

Folder: `extraction_pipeline/`

- `prefill_full_review_table.py`
  - Prefills an extraction/review table template (CSV) by joining intermediate screening metadata files.

Note: This script is intentionally "project glue code" and expects intermediate CSVs produced during the review workflow. The input/output files are not included in this repository.
