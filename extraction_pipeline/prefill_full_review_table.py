import csv
from pathlib import Path

PROJECT_ROOT = Path(r"d:\MZ\New\FINAL")
analysis_dir = PROJECT_ROOT / "temp_vector_pipeline" / "analysis"

final_included_path = analysis_dir / "FINAL_INCLUDED_PAPERS.csv"
metadata_path = analysis_dir / "PAPERS_154_METADATA.csv"
methods_data_path = analysis_dir / "methods_data_per_paper_FINAL_INCLUDED.csv"
output_path = analysis_dir / "FULL_REVIEW_154_TEMPLATE.csv"

# Load FINAL_INCLUDED_PAPERS (list of integer IDs)
with final_included_path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    included_ids = [row[reader.fieldnames[0]].strip() for row in reader if row[reader.fieldnames[0]].strip()]

# Map paper_id (int) -> methods / data_types
methods_by_id = {}
with methods_data_path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["paper_id"].strip()
        if not pid:
            continue
        methods_by_id[pid] = {
            "methods": row.get("methods", "").strip(),
            "data_types": row.get("data_types", "").strip(),
        }

# Map paper_id (int) -> metadata (title, journal, year, crop guess)
meta_by_id = {}
with metadata_path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid_3d = row["paper_id_3d"].lstrip("0") or "0"
        title = row["title"].strip()
        journal = row["journal"].strip()
        year = row["year"].strip()

        # Simple crop guess from title (very heuristic, you can adjust manually)
        lower_title = title.lower()
        crop = ""
        for c in [
            "maize", "corn", "wheat", "rice", "soybean", "soy", "cotton",
            "almond", "vineyard", "grape", "citrus", "coffee", "barley",
            "potato", "sugarcane", "peach", "turfgrass", "oil palm",
        ]:
            if c in lower_title:
                crop = c
                break

        meta_by_id[pid_3d] = {
            "title": title,
            "journal": journal,
            "year": year,
            "crop": crop,
        }

# Prepare header for FULL_REVIEW_154_TEMPLATE.csv
header = [
    "Paper_ID",
    "Title",
    "Year",
    "Journal",
    "Region",
    "Crop_Type",
    "Field_Size_Scale",
    "Goal_Objective",
    "Primary_Management_Focus",
    "Application",
    "Used_Methods",
    "Degree_of_Zone_Optimization",
    "Temporal_Dimension",
    "Used_Data_Description",
    "Data_Type_Tags",
    "Integration_Fusion_Level",
    "Evaluation_Approach",
    "Evaluation_Metrics",
    "Validation_Data_Independence",
    "Study_Type",
    "Notes",
]

rows = []

for pid in included_ids:
    meta = meta_by_id.get(pid, {})
    md = methods_by_id.get(pid, {})

    title = meta.get("title", "")
    journal = meta.get("journal", "")
    year = meta.get("year", "")
    crop = meta.get("crop", "")

    methods = md.get("methods", "")
    data_types = md.get("data_types", "")

    # Very simple goal/objective from title
    goal = ""
    if title:
        goal = f"Summarise and apply management zone delineation methods described in the paper: {title}"

    # Primary management focus: best-effort guess from title/keywords
    lower_title = title.lower()
    if any(w in lower_title for w in ["nitrogen", "fertilizer", "fertiliser", "nutrient"]):
        pmf = "Nutrient / fertiliser"
    elif any(w in lower_title for w in ["irrigation", "water"]):
        pmf = "Water / irrigation"
    elif any(w in lower_title for w in ["salinity", "soil quality", "soil fertility", "soil mapping"]):
        pmf = "Soil quality / salinity"
    elif any(w in lower_title for w in ["weed", "pest", "disease"]):
        pmf = "Pest / weed / disease"
    elif any(w in lower_title for w in ["yield", "productivity", "profit"]):
        pmf = "Yield / production"
    else:
        pmf = "General / multi-objective"

    # Data type tags: copy as-is, but normalise separators for readability
    data_tags = data_types.replace(",", ";") if data_types else ""

    # Integration level based on number of data types
    if data_types:
        n_types = len([t for t in data_types.split(",") if t.strip()])
        if n_types <= 1:
            fusion = "single source"
        else:
            fusion = "multi-layer fusion"
    else:
        fusion = ""

    row = {
        "Paper_ID": pid,
        "Title": title,
        "Year": year,
        "Journal": journal,
        "Region": "",
        "Crop_Type": crop,
        "Field_Size_Scale": "",
        "Goal_Objective": goal,
        "Primary_Management_Focus": pmf,
        "Application": "",
        "Used_Methods": methods,
        "Degree_of_Zone_Optimization": "",
        "Temporal_Dimension": "",
        "Used_Data_Description": "",
        "Data_Type_Tags": data_tags,
        "Integration_Fusion_Level": fusion,
        "Evaluation_Approach": "",
        "Evaluation_Metrics": "",
        "Validation_Data_Independence": "",
        "Study_Type": "",
        "Notes": "",
    }
    rows.append(row)

# Write the template with prefilled columns
with output_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Prefilled table written to: {output_path}")
