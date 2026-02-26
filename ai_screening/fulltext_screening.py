from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import csv
import json
import subprocess

try:
    from .config import PipelineConfig
except ImportError:  # pragma: no cover
    from config import PipelineConfig


@dataclass
class ScreeningResult:
    paper_id: str
    decision: str  # INCLUDE / EXCLUDE / UNCERTAIN / ERROR
    confidence: str  # high / medium / low / unknown
    reason: str
    model: str


def _build_prompt(title: str, abstract: str | None, full_text: str, criteria_text: str) -> str:
    """Construct a prompt for the LLM that applies full-text inclusion/exclusion criteria.

    The prompt is kept model-agnostic so that any Ollama model can be plugged in.
    """
    header = (
        "You are assisting with a systematic review on management zone delineation in precision agriculture. "
        "Read the following information about one paper (title, optional abstract, and full text) and decide whether "
        "the paper should be INCLUDED or EXCLUDED at full-text screening. Apply the inclusion/exclusion criteria exactly."\
    )

    parts: List[str] = [header, "\n\nFULL-TEXT SCREENING CRITERIA:\n", criteria_text.strip(), "\n\nPAPER:\n"]

    parts.append(f"Title: {title.strip()}\n")
    if abstract:
        parts.append(f"Abstract: {abstract.strip()}\n")
    parts.append("Full text (may be truncated in this view):\n")
    parts.append(full_text.strip())

    parts.append(
        "\n\nTASK:\n"
        "1. Decide: INCLUDE, EXCLUDE, or UNCERTAIN.\n"
        "2. Provide a confidence level: high, medium, or low.\n"
        "3. Briefly explain the main reason, referring to methods, data, or scope.\n\n"
        "Respond in the following JSON format ONLY (no extra text):\n"
        '{"decision": "INCLUDE|EXCLUDE|UNCERTAIN", "confidence": "high|medium|low", "reason": "..."}'
    )

    return "".join(parts)


def _call_ollama(model: str, prompt: str) -> Dict[str, str]:
    """Call a local Ollama model and parse a JSON response.

    This implementation uses the `ollama` CLI, which must be installed and
    available on the system PATH. The model is expected to return a single
    JSON object with fields: `decision`, `confidence`, and `reason`.
    """
    # We pass the prompt via stdin to avoid shell-quoting issues.
    try:
        proc = subprocess.run(
            ["ollama", "run", model],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Ollama CLI (`ollama`) not found. Please install Ollama and ensure it "
            "is available on your PATH before running full-text screening."
        ) from exc

    if proc.returncode != 0:
        raise RuntimeError(
            f"Ollama call failed with exit code {proc.returncode}: {proc.stderr.decode('utf-8', errors='ignore')}"
        )

    raw = proc.stdout.decode("utf-8", errors="ignore").strip()

    # Some models may emit extra text; try to locate the JSON object.
    # We look for the first '{' and the last '}' and parse that slice.
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(
            f"Ollama output did not contain a JSON object as expected. Output was:\n{raw}"
        )

    json_str = raw[start : end + 1]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse JSON from Ollama output. Slice was:\n{json_str}"
        ) from exc

    # Normalise keys and provide defaults.
    return {
        "decision": str(data.get("decision", "UNCERTAIN")),
        "confidence": str(data.get("confidence", "unknown")),
        "reason": str(data.get("reason", "")),
    }


def run_fulltext_screening(cfg: PipelineConfig) -> None:
    """Run AI-assisted full-text screening over all extracted full-text files.

    For each paper in full_text/, this function:
    - Builds an LLM prompt with title/abstract (if available) and full text.
    - Calls an Ollama model to get INCLUDE/EXCLUDE/UNCERTAIN, confidence, and reason.
    - Writes results to FULLTEXT_AI_SCREENING.csv in the analysis directory.

    All final decisions should still be made by human reviewers, using this file as a
    starting point for efficient review.
    """
    full_text_dir = cfg.paths.output_root / "full_text"
    if not full_text_dir.exists():
        raise FileNotFoundError(f"Full-text directory not found: {full_text_dir}")

    analysis_dir = cfg.paths.output_root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    out_csv = analysis_dir / "FULLTEXT_AI_SCREENING.csv"

    # Optional: path to a metadata file (e.g., Included_Papers_Tracking) could be added later.
    # For now, we only know paper_id from the full-text filename.

    # Simple text block with your full-text inclusion/exclusion criteria.
    # You can refine or externalize this later.
    criteria_text = cfg.screening.fulltext_criteria if hasattr(cfg, "screening") else (
        "Include peer-reviewed Q1 journal articles (2000--2025) that present original "
        "methods for delineating or creating management zones in agricultural fields, "
        "using data-driven approaches (e.g., clustering, geostatistics, machine learning) "
        "and reporting sufficient methodological detail. Exclude papers that do not focus "
        "on management zone delineation, lack methodological detail, are not primarily "
        "about precision agriculture, or are reviews, conceptual pieces, or commentaries."
    )

    model_name = getattr(cfg, "ollama_model", "llama3")  # you can add this to config.yaml

    results: List[ScreeningResult] = []

    for txt_path in sorted(full_text_dir.glob("*.txt")):
        paper_id = txt_path.stem  # e.g., 001, 002, ...
        text = txt_path.read_text(encoding="utf-8", errors="ignore")

        # To keep prompts within a reasonable context window and reduce the risk of
        # truncated or malformed JSON responses, we only send a prefix of the full
        # text to the model. This still provides substantial information for
        # screening while improving robustness.
        text_prefix = text[:6000]

        # In this first version we do not inject title/abstract metadata; that can be added later
        # by joining with your tracking Excel file.
        title = f"Paper {paper_id} (title unavailable in this pipeline step)"
        abstract = None

        prompt = _build_prompt(title=title, abstract=abstract, full_text=text_prefix, criteria_text=criteria_text)

        try:
            resp = _call_ollama(model=model_name, prompt=prompt)
            decision = str(resp.get("decision", "ERROR")).upper()
            confidence = str(resp.get("confidence", "unknown")).lower()
            reason = str(resp.get("reason", ""))
        except Exception as exc:  # pragma: no cover - defensive logging
            decision = "ERROR"
            confidence = "unknown"
            reason = f"Ollama call failed: {exc}"

        results.append(
            ScreeningResult(
                paper_id=paper_id,
                decision=decision,
                confidence=confidence,
                reason=reason,
                model=model_name,
            )
        )

    # Write CSV log for human review
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["paper_id", "decision", "confidence", "reason", "model"])
        for r in results:
            writer.writerow([r.paper_id, r.decision, r.confidence, r.reason, r.model])

    print(f"Full-text AI screening results written to: {out_csv}")


if __name__ == "__main__":
    run_fulltext_screening(PipelineConfig())
