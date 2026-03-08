from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def _norm_doi(raw: Any) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    s = s.replace("https://doi.org/", "").replace("http://doi.org/", "").replace("doi:", "").strip()
    return s


def _doi_url(doi: str) -> str:
    doi = _norm_doi(doi)
    return f"https://doi.org/{doi}" if doi else ""


def _abstract_snippet(raw: Any, limit: int = 300) -> str:
    if raw is None:
        return ""
    s = str(raw).replace("\r", " ").replace("\n", " ").strip()
    if not s:
        return ""
    return s[:limit]


def build_integrated_db(source_dir: Path, out_dir: Path) -> Path:
    """Build integrated DB artifacts for GitHub Pages.

    Reads structured extraction and screening outputs from `source_dir` and writes:
    - `papers.json` (for the DB website)
    - `papers.csv` (optional convenient export)

    Returns the path to `papers.json`.
    """

    out_dir.mkdir(parents=True, exist_ok=True)

    # Sources
    decisions_log_path = source_dir / "DECISIONS_LOG.csv"
    top300_selected_path = source_dir / "Top_300_papers_selected.csv"
    top300_for_screening_path = source_dir / "Top300_ForScreening.xlsx"

    allpapers_path = source_dir / "MZ_Delineation_Review_AllPapers.xlsx"
    methods_path = source_dir / "method_used_for_MZ_manual_final_AfterComment.xlsx"
    dataflags_path = source_dir / "data_used_for_MZ_manual_final-Data.xlsx"
    fieldsize_vi_path = source_dir / "field_size_and_VI.xlsx"
    validation_methods_path = source_dir / "Validation_Methods.xlsx"

    # Load
    decisions = pd.read_csv(decisions_log_path)
    top300 = pd.read_csv(top300_selected_path)
    top300_for_screening = pd.read_excel(top300_for_screening_path, sheet_name="Top 300 Papers")

    allpapers = pd.read_excel(allpapers_path, sheet_name="AllPapers")
    methods = pd.read_excel(methods_path, sheet_name="method_used_for_MZ_manual_final")
    dataflags = pd.read_excel(dataflags_path, sheet_name="data_used_for_MZ_manual_final")
    fieldsize_vi = pd.read_excel(fieldsize_vi_path, sheet_name="Used for VI")
    validation = pd.read_excel(validation_methods_path, sheet_name="AllPapers")

    # Normalise IDs
    def norm_id(df: pd.DataFrame) -> pd.DataFrame:
        if "Paper_ID" in df.columns:
            df["Paper_ID"] = pd.to_numeric(df["Paper_ID"], errors="coerce").astype("Int64")
        return df

    for d in (decisions, top300, allpapers, methods, dataflags, fieldsize_vi, validation):
        norm_id(d)

    norm_id(top300_for_screening)

    # Ensure DOI available (from top300 sources)
    top300 = top300.copy()
    if "DOI" in top300.columns:
        top300["DOI"] = top300["DOI"].map(_norm_doi)

    top300_for_screening = top300_for_screening.copy()
    if "DOI" in top300_for_screening.columns:
        top300_for_screening["DOI"] = top300_for_screening["DOI"].map(_norm_doi)

    # Merge into one table (left join on AllPapers)
    df = allpapers.copy()

    # Pull in DOI/score/keywords from Top_300_papers_selected
    top300_cols = [c for c in ["Paper_ID", "Score", "DOI", "Keywords Found"] if c in top300.columns]
    df = df.merge(top300[top300_cols], on="Paper_ID", how="left", suffixes=("", "_top300"))

    # Fallback DOI and abstract-screening fields from Top300_ForScreening
    tfs_cols = [
        "Paper_ID",
        "DOI",
        "Score",
        "Methods Found",
        "Data Found",
        "Results Found",
        "Abstract",
    ]
    tfs_cols = [c for c in tfs_cols if c in top300_for_screening.columns]
    df = df.merge(top300_for_screening[tfs_cols], on="Paper_ID", how="left", suffixes=("", "_top300screen"))

    # Option 1 (public-safe): only store a short abstract snippet, not full abstracts.
    if "Abstract" in df.columns:
        df["Abstract_Snippet"] = df["Abstract"].map(lambda x: _abstract_snippet(x, limit=300))
        df = df.drop(columns=["Abstract"])

    # If DOI is missing, use the fallback DOI from Top300_ForScreening
    if "DOI_top300screen" in df.columns:
        df["DOI"] = df["DOI"].where(df["DOI"].notna() & (df["DOI"].astype(str).str.strip() != ""), df["DOI_top300screen"])

    # Decisions (who decided include/exclude)
    dec_cols = [
        "Paper_ID",
        "Final_Decision",
        "Decision_Source",
        "Decided_By",
        "Confidence",
        "Human_Decision",
        "DeepSeek_Decision",
        "Llama_Decision",
        "Gemini_Decision",
        "Notes",
    ]
    dec_cols = [c for c in dec_cols if c in decisions.columns]
    df = df.merge(decisions[dec_cols], on="Paper_ID", how="left", suffixes=("", "_decision"))

    # Methods workflows
    m_cols = [
        "Paper_ID",
        "Workflows",
        "Explanations (for each workflows) ",
        "Methods_Used in detail",
    ]
    m_cols = [c for c in m_cols if c in methods.columns]
    df = df.merge(methods[m_cols], on="Paper_ID", how="left", suffixes=("", "_methods"))

    # Data flags (binary)
    if "Paper_ID" in dataflags.columns:
        df = df.merge(dataflags, on="Paper_ID", how="left", suffixes=("", "_dataflags"))

    # Field size + VI info
    f_cols = [
        "Paper_ID",
        "FieldSize_raw",
        "FieldSize_max_ha",
        "climate ",
        "management_focus",
        "Country(RAW)",
        "VI_Media",
        "uav",
        "Aircraft",
        "sat",
        "proximal",
        "paper_Used_VI?",
    ]
    f_cols = [c for c in f_cols if c in fieldsize_vi.columns]
    df = df.merge(fieldsize_vi[f_cols], on="Paper_ID", how="left", suffixes=("", "_field"))

    # Validation codes
    v_cols = [
        "Paper_ID",
        "Validation Description",
        "Validation-Code",
        "Note",
    ]
    v_cols = [c for c in v_cols if c in validation.columns]
    df = df.merge(validation[v_cols], on="Paper_ID", how="left", suffixes=("", "_validation"))

    # Derived DOI URL
    if "DOI" in df.columns:
        df["DOI"] = df["DOI"].map(_norm_doi)
        df["DOI_URL"] = df["DOI"].map(_doi_url)
    else:
        df["DOI_URL"] = ""

    # Clean types for JSON
    def to_json_safe(value: Any) -> Any:
        if pd.isna(value):
            return None
        if isinstance(value, (pd.Timestamp,)):
            return value.isoformat()
        if isinstance(value, (int, float)):
            # Keep integers clean
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value
        return str(value)

    records: list[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rec: Dict[str, Any] = {k: to_json_safe(v) for k, v in row.to_dict().items()}
        records.append(rec)

    out_json = out_dir / "papers.json"
    out_csv = out_dir / "papers.csv"

    out_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV export (best-effort; keep column order)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(df.columns) + (["DOI_URL"] if "DOI_URL" not in df.columns else []))
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

    return out_json


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_dir = Path(r"D:\MZ\New\XML to XLS\Final-Excels\Should be Shared")
    out_dir = repo_root / "docs" / "data"

    out_json = build_integrated_db(source_dir=source_dir, out_dir=out_dir)
    print(f"Wrote: {out_json}")


if __name__ == "__main__":
    main()
