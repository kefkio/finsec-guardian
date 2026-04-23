"""
WebIntel Analysis Engine Base Classes

Provides abstractions for all analyzer implementations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class FindingSeverity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class WebFindingData:
    """Normalized finding output from analyzers."""
    title: str
    description: str
    severity: FindingSeverity
    category: str
    analyzer_name: str
    confidence_score: int  # 0-100
    evidence: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Optional[str] = None  # For deduplication


@dataclass
class AnalyzerResult:
    """Result container for analyzer execution."""
    available: bool = True
    error: Optional[str] = None
    findings: List[WebFindingData] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    
    def __post_init__(self):
        if not self.available and not self.error:
            self.error = "Analyzer not available"


class BaseWebAnalyzer:
    """
    Base class for all WebIntel analyzers.
    
    Each analyzer is responsible for detecting specific types of financial deception.
    """
    
    analyzer_name: str = "BaseAnalyzer"
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def is_available(self) -> bool:
        """
        Check if analyzer dependencies are available.
        
        Returns:
            bool: True if analyzer can run, False otherwise
        """
        return True
    
    def analyze(self, target: str, target_type: str, **kwargs) -> AnalyzerResult:
        """
        Run analysis on the target.
        
        Args:
            target: URL, domain, or IP to analyze
            target_type: Type of target ('url', 'domain', 'ip')
            **kwargs: Additional analyzer-specific parameters
        
        Returns:
            AnalyzerResult: Standardized result container
        """
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def normalize_finding(
        self,
        title: str,
        description: str,
        severity: FindingSeverity,
        category: str,
        confidence: int,
        evidence: Optional[Dict] = None,
    ) -> WebFindingData:
        """Create normalized finding."""
        return WebFindingData(
            title=title,
            description=description,
            severity=severity,
            category=category,
            analyzer_name=self.analyzer_name,
            confidence_score=confidence,
            evidence=evidence or {},
        )
