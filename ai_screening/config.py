from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelinePaths:
    output_root: Path


@dataclass(frozen=True)
class ScreeningConfig:
    fulltext_criteria: str | None = None


@dataclass(frozen=True)
class PipelineConfig:
    """Minimal configuration for the helper scripts in this repository.

    This is intentionally small and easy to edit for reviewers.
    """

    paths: PipelinePaths = PipelinePaths(output_root=Path("temp_vector_pipeline"))
    screening: ScreeningConfig = ScreeningConfig()
    ollama_model: str = "llama3"
