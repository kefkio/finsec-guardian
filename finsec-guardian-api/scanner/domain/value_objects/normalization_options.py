from __future__ import annotations

from dataclasses import dataclass, fields

from scanner.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class NormalizationOptions:
    """
    Immutable configuration controlling source-code normalization.

    A NormalizationOptions instance defines the strategy used by a
    normalizer to produce a deterministic canonical representation of
    source code prior to fingerprint generation.

    Because this is a Value Object, instances are immutable and may be
    safely shared or cached throughout the application.
    """

    normalize_unicode: bool = True
    normalize_line_endings: bool = True
    normalize_tabs: bool = True
    normalize_whitespace: bool = True
    collapse_blank_lines: bool = True
    remove_comments: bool = True

    def __post_init__(self) -> None:
        """
        Validate that every configuration option is a boolean.

        Dataclass type annotations are not enforced at runtime, so this
        guards against invalid configuration originating from external
        configuration sources.
        """
        for field in fields(self):
            value = getattr(self, field.name)

            if not isinstance(value, bool):
                raise DomainValidationError(
                    f"{field.name} must be a bool, "
                    f"got {type(value).__name__}."
                )

    # ==========================================================
    # Presets
    # ==========================================================

    @classmethod
    def fingerprinting(cls) -> "NormalizationOptions":
        """
        Return the recommended configuration for fingerprint generation.

        This preset performs maximal normalization while preserving the
        semantic meaning of the source code.
        """
        return cls()

    @classmethod
    def preserve_formatting(cls) -> "NormalizationOptions":
        """
        Return a configuration that preserves formatting.

        Useful for displaying normalized code or producing human-readable
        diffs where comments and whitespace should remain unchanged.
        """
        return cls(
            normalize_unicode=True,
            normalize_line_endings=True,
            normalize_tabs=False,
            normalize_whitespace=False,
            collapse_blank_lines=False,
            remove_comments=False,
        )

    @classmethod
    def raw(cls) -> "NormalizationOptions":
        """
        Return a configuration that performs no normalization.

        Primarily intended for testing and debugging.
        """
        return cls(
            normalize_unicode=False,
            normalize_line_endings=False,
            normalize_tabs=False,
            normalize_whitespace=False,
            collapse_blank_lines=False,
            remove_comments=False,
        )

    # ==========================================================
    # Introspection
    # ==========================================================

    @property
    def active_options(self) -> tuple[str, ...]:
        """
        Return the names of all enabled normalization options.
        """
        return tuple(
            field.name
            for field in fields(self)
            if getattr(self, field.name)
        )

    def describe(self) -> str:
        """
        Return a human-readable description of this configuration.
        """
        active = self.active_options

        return (
            f"NormalizationOptions("
            f"{', '.join(active) if active else 'none'}"
            f")"
        )