"""
Normalization framework.

Provides deterministic language-specific source code
normalizers used during fingerprint generation.
"""

from .base_normalizer import BaseNormalizer

__all__ = [
    "BaseNormalizer",
]