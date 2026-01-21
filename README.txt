#Management Zone Delineation Review – Code & Pipelines
This repository contains the code and prompt templates referenced in the paper:
- Evidence-based keyword scoring for Q1 abstracts.
- AI-assisted screening prompts and full-text screening.
- Scripts to prefill the data extraction / review table.
##1. Keyword scoring (Q1 abstracts)
Folder: `keyword_scoring/`
- [06_score_and_filter_papers.py]  
  Python implementation of the evidence-based keyword scoring described in the paper:
  - Six keyword categories (methods, data, application, results, context, exclusion).
  - Each category contributes its weight at most once per abstract.
  - Completeness bonus when at least one methods, one data, and one results keyword are all present.
- [Keywords_used_for_scoring.txt]  
  Main keyword groups and weights.
- [S2_Complete_keyword_list.txt]  
  Complete keyword list and detailed description of the scoring algorithm.
##2. AI-assisted screening
Folder: `ai_screening/`
- [01_AI_SCREENING_PROMPTS.txt](cci:7://file:///d:/MZ/New/FINAL/GIT/ai_screening/01_AI_SCREENING_PROMPTS.txt:0:0-0:0)  
  Canonical prompts used for AI-assisted title/abstract screening.  
  Corresponds to the screening prompt described in Appendix A.
- [fulltext_screening.py](cci:7://file:///d:/MZ/New/FINAL/GIT/ai_screening/fulltext_screening.py:0:0-0:0)  
  Script for AI-assisted full-text screening using a local Ollama model:
  - Builds prompts from full-text files and inclusion/exclusion criteria.
  - Writes `FULLTEXT_AI_SCREENING.csv` (not included here) for human review.
> Note: this script expects a `config.PipelineConfig` class (not included here) that provides
> `paths.output_root` and optional `screening.fulltext_criteria` / `ollama_model`.
##3. Extraction pipeline / review table
Folder: `extraction_pipeline/`
- [prefill_full_review_table.py]  
  Prefills a review/extraction table (e.g. `FULL_REVIEW_154_TEMPLATE.csv`, not included here)
  from:
  - FINAL_INCLUDED_PAPERS.csv
  - PAPERS_154_METADATA.csv
  - methods_data_per_paper_FINAL_INCLUDED.csv
This script implements the processing pipeline described in the paper for generating
a structured extraction template from inclusion decisions and metadata.
