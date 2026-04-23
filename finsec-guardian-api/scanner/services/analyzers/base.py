"""Base types shared by all analyzers."""

from dataclasses import dataclass, field


@dataclass
class AnalyzerResult:
    """Standardised return value for every analyzer.

    ``raw_output`` contains the tool-specific data (e.g. Slither detector
    list, Mythril issue list, or heuristic finding list).  The normalizer
    is responsible for converting these into the unified finding format.
    """

    success: bool
    raw_output: dict = field(default_factory=dict)
    error: str | None = None
    stderr: str = ""
    tool: str = ""
