from __future__ import annotations

import csv
import json
import re
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


def _norm_country(raw: Any) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    # Examples:
    # - "USA (Southern High Plains of Texas, near Olton, ..." -> "USA"
    # - "United States" -> "United States"
    s = s.split("(", 1)[0]
    s = s.split(",", 1)[0]
    return s.strip()


def _split_tokens(raw: Any) -> list[str]:
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    parts = re.split(r"[;,]+", s)
    out: list[str] = []
    for p in parts:
        t = p.strip()
        if not t:
            continue
        out.append(t)
    return out


def _norm_crop(token: str) -> str:
    # "Corn (Zea mays L.)" -> "Corn"
    t = token.split("(", 1)[0].strip()
    if not t:
        return ""

    # Guard against broken fragments like "Corymbia citriodora)" that can appear
    # when the source text contains nested parentheses.
    if ")" in t and "(" not in token:
        return ""

    t = re.sub(r"\s+", " ", t).strip()

    # Drop non-crop tokens that appear in some rows
    tl = t.lower()
    if tl.startswith("plot"):
        return ""
    if tl in {"plots", "plot", "plot a", "plot b", "plot c", "plot d"}:
        return ""

    # Normalize capitalization and common variants
    crop_map = {
        "corn": "Corn",
        "maize": "Corn",
        "soybean": "Soybean",
        "soybeans": "Soybean",
        "cotton": "Cotton",
        "wheat": "Wheat",
        "durum wheat": "Wheat",
        "sorghum": "Sorghum",
        "barley": "Barley",
        "rice": "Rice",
        "alfalfa": "Alfalfa",
        "cover crops": "Cover crops",
        "corn silage": "Corn silage",
    }

    if tl in crop_map:
        return crop_map[tl]

    # Default: sentence-style capitalization (avoids Cotton vs cotton)
    return t[:1].upper() + t[1:].lower()


def _extract_workflow_groups(raw: Any) -> list[str]:
    if raw is None:
        return []
    s = str(raw)
    if not s.strip():
        return []
    # Workflow groups are coded like A1..A5, B1..B5, C1..C5, D1..D5
    codes = re.findall(r"\b[A-D][1-5]\b", s.upper())
    # Distinct while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _extract_validation_tiers(raw: Any) -> list[str]:
    if raw is None:
        return []
    s = str(raw)
    if not s.strip():
        return []
    tiers = re.findall(r"\bVAL_TIER_[A-Z]\b", s.upper())
    seen: set[str] = set()
    out: list[str] = []
    for t in tiers:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


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

    # Keep a compact, reviewer-friendly copy of the "first-round" raw extraction
    raw_cols = [
        "Paper_ID",
        "BibTeX_ID",
        "Title",
        "Year",
        "Journal",
        "Country",
        "FieldSize",
        "Data used for MZ",
        "Auxilary data",
        "Data used for validation",
        "Sensors/DataSources names",
        "SamplingDensity",
        "Resolution",
        "Methods",
        "Sub-Methods-Internal",
        "Zones",
        "ManagementFocus",
        "Crops",
        "Validation",
        "Notes",
    ]
    raw_cols = [c for c in raw_cols if c in df.columns]
    raw_map: dict[int, dict[str, Any]] = {}
    for _, r in df[raw_cols].iterrows():
        pid = r.get("Paper_ID")
        if pd.isna(pid):
            continue
        try:
            pid_int = int(pid)
        except Exception:
            continue
        raw_map[pid_int] = {k: r.get(k) for k in raw_cols if k != "Paper_ID"}

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

        # Derived: list of data categories used for MZ delineation
        flag_cols = [c for c in dataflags.columns if c not in ("Paper_ID", "BibTeX_ID")]
        if flag_cols:
            def _collect_data_used(row: pd.Series) -> str:
                used: list[str] = []
                for c in flag_cols:
                    v = row.get(c)
                    try:
                        vv = float(v)
                    except Exception:
                        continue
                    if vv == 1:
                        used.append(str(c).strip())
                return "; ".join(used)

            df["DataUsed_MZ"] = df.apply(_collect_data_used, axis=1)
            df["DataUsed_MZ_list"] = df["DataUsed_MZ"].map(_split_tokens)

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

    # Prefer method explanation text for the Methods column displayed in the UI
    if "Explanations (for each workflows) " in df.columns:
        df["Methods_Explanation"] = df["Explanations (for each workflows) "]

    # Make an Abstract column available for UI (public-safe snippet)
    if "Abstract_Snippet" in df.columns and "Abstract" not in df.columns:
        df["Abstract"] = df["Abstract_Snippet"]

    # Derived DOI URL
    if "DOI" in df.columns:
        df["DOI"] = df["DOI"].map(_norm_doi)
        df["DOI_URL"] = df["DOI"].map(_doi_url)
    else:
        df["DOI_URL"] = ""

    # Normalized fields for smarter filtering
    if "Country" in df.columns:
        df["Country_norm"] = df["Country"].map(_norm_country)
    if "Country(RAW)" in df.columns and "Country_norm" not in df.columns:
        df["Country_norm"] = df["Country(RAW)"].map(_norm_country)

    if "Crops" in df.columns:
        crops_list = df["Crops"].map(_split_tokens)
        df["Crops_list"] = crops_list
        df["Crops_norm"] = crops_list.map(lambda xs: "; ".join([_norm_crop(x) for x in xs if _norm_crop(x)]))

    # Attach compact raw extraction object per paper for the UI modal
    if "Paper_ID" in df.columns:
        def _raw_for_pid(pid: Any) -> dict[str, Any] | None:
            if pd.isna(pid):
                return None
            try:
                pid_int = int(pid)
            except Exception:
                return None
            return raw_map.get(pid_int)

        df["Raw_Extraction"] = df["Paper_ID"].map(_raw_for_pid)

    if "Workflows" in df.columns:
        wf_list = df["Workflows"].map(_extract_workflow_groups)
        df["Workflow_Groups"] = wf_list
        df["Workflow_Groups_str"] = wf_list.map(lambda xs: "; ".join(xs))

    if "Validation-Code" in df.columns:
        vt_list = df["Validation-Code"].map(_extract_validation_tiers)
        df["Validation_Tier"] = vt_list
        df["Validation_Tier_str"] = vt_list.map(lambda xs: "; ".join(xs))

    # Clean types for JSON
    def to_json_safe(value: Any) -> Any:
        if isinstance(value, (list, tuple, set)):
            return [to_json_safe(v) for v in value]

        if isinstance(value, dict):
            return {str(k): to_json_safe(v) for k, v in value.items()}

        # pd.isna() is not safe on lists/arrays; keep it after iterable handling
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
