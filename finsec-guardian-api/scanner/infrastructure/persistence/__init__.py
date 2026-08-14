"""Persistence implementations for the scanner app.

Note: avoid importing model classes at package import time because doing
so can trigger Django model import logic before the app registry is
initialized (leading to ``AppRegistryNotReady`` during pytest collection).

Import concrete model modules directly (e.g. ``.models`` or
``.models_v2``) to ensure Django setup occurs first.
"""

# Intentionally do not import model classes here to avoid side-effects at
# package import time. Import consumers should import the specific modules
# they need, for example::
#
#     from scanner.infrastructure.persistence import models_v2
#     from scanner.infrastructure.persistence.models_v2 import ScanRecord
#
__all__ = [
    # package-level re-exports are omitted to prevent eager imports
]
