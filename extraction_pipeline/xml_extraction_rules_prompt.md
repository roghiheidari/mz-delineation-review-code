# XML extraction rules and prompt (study-level extraction)

This document contains the rules and response format used to extract structured, study-level information from full-text papers during the review workflow.

## Task

You are analyzing research papers for a systematic review titled:

"The Evolution of Data-Driven Management Zone Delineation: A Systematic Review"

Your job is to determine whether each paper is relevant, and if it is, produce a strictly formatted XML summary using short, keyword-style entries (not descriptive sentences).

If the paper is not relevant, output an `exclude: ...` line explaining why.

## Inclusion criteria (all must be true)

1. Field-scale agricultural context
   - Real crop fields (not greenhouse, pots, purely lab, urban, or forestry).
   - Focus on crop production or soil/water/nutrient/crop management.

2. Applying a zoning method that produces discrete management zones
   - Paper delineates sub-areas inside a field (management zones, site-specific management units, homogeneous zones, productivity zones, etc.),
   - using measured/sensed field data (soil, yield, EC, NDVI/RS, UAV, etc.).

3. Direct link to site-specific management decisions
   - Zones are explicitly intended to guide field operations, e.g. variable-rate:
     - variable-rate fertilizer, lime/gypsum, irrigation, seeding, pesticides, or similar,
     - or clear zone-specific agronomic recommendations (different input levels or field practices per zone).
   - Conceptual/tool papers are included only if they clearly target such within-field input decisions in real crop fields.

4. Original field study
   - Includes empirical field data and actual MZ delineation (not only theory, generic simulation, or pure review/meta-analysis).

## Exclusion criteria (any one is sufficient)

Exclude (do NOT generate XML) if any of the following is true:

- No field-scale MZ / no within-field partitioning
  - Only continuous mapping or classification (e.g. LAI, yield, soil properties, land cover) without defining management zones or within-field decision units.

- Wrong scale or context
  - Only regional/landscape/farm-level planning zones with no clear field-scale MZs.
  - Non-agricultural contexts (urban, forest, basins) unless clearly framed as crop-field management zones.

- Experimental setup not comparable
  - Greenhouse/micro-plots/pots/lysimeters without spatial zoning of real fields.

- Pure method/theory without real field MZs
  - Algorithms or optimization methods tested only on synthetic or generic examples, with no clear application to field-scale agricultural MZs.

- Quality / terroir zoning without agronomic input decisions
  - Zoning used mainly for product or quality differentiation (wine quality, coffee beverage typicity, terroir branding, certification lots),
  - and not clearly used to change within-field agronomic inputs (fertilizer, irrigation, seeding, etc.).
  - This includes cases where zones guide only harvest grouping, drying strategies, storage, marketing, or labelling.

## Response format

If excluded, return only one line:

```
exclude: <short reason>
```

Examples:

- `exclude: zoning focuses on coffee beverage quality/terroir, not agronomic inputs or VRT`
- `exclude: only continuous yield mapping, no management zones or site-specific decisions`
- `exclude: regional zoning, no field-scale management zones`

If included, return exactly one XML block:

```xml
<Paper id="NNN">
    <Column>Country</Column><Information>...</Information>
    <Column>FieldSize</Column><Information>...</Information>
    <Column>Data used for MZ</Column><Information>...</Information>
    <Column>Auxilary data</Column><Information>...</Information>
    <Column>Data used for validation</Column><Information>...</Information>
    <Column>Sensors/DataSources names</Column><Information>...</Information>
    <Column>SamplingDensity</Column><Information>...</Information>
    <Column>Resolution</Column><Information>...</Information>
    <Column>Methods</Column><Information>...</Information>
    <Column>Sub-Methods-Internal</Column><Information>...</Information>
    <Column>Zones</Column><Information>...</Information>
    <Column>ManagementFocus</Column><Information>...</Information>
    <Column>Crops</Column><Information>...</Information>
    <Column>Validation Method</Column><Information>...</Information>
    <Column>Notes</Column><Information>...</Information>
</Paper>
```

Use these exact column names (spelling and spaces):

- Country
- FieldSize
- Data used for MZ
- Auxilary data
- Data used for validation
- Sensors/DataSources names
- SamplingDensity
- Resolution
- Methods
- Sub-Methods-Internal
- Zones
- ManagementFocus
- Crops
- Validation Method
- Notes

## Content style (Information values)

- Each `Information` value should be short.
- Prefer keywords or compact phrases (lists separated by `;`).
- Aim for under ~300 characters per `Information`.
- Capture only the most important variables, methods, data sources, zones, and main findings.

## Plain text only

- No HTML (no `<sup>`, `<sub>`, `<b>`, etc.).
- Write `R2` instead of `R²`.
- Use `p < 0.05` (or `p &lt; 0.05` if needed inside XML).

## XML validity rules

- Always follow the pattern:
  - `<Column>ColumnName</Column><Information>...</Information>`
- Every `<Column>` must have a matching `</Column>`.
- Every `<Information>` must have a matching `</Information>`.
- No extra `</Column>` or `</Information>` tags.
- No text before `<Paper>` or after `</Paper>`.
- If you need a `<` inside text, write it as `&lt;`.

## Model query convention

The user will ask, e.g.:

"Generate XML result for paper XXX.pdf based on rules.docx"

The model must respond with either:

- A single `<Paper>...</Paper>` XML block (for included papers), or
- A single line `exclude: <reason>` (for excluded papers).

No extra explanations, comments, or markdown.

## No citation brackets

In `Information` values, do not include reference-style citations such as `[1]`, `[2–4]`, `[6, 18–21]`, etc.

Write the content (keywords or short phrases) without these bracketed reference numbers.
