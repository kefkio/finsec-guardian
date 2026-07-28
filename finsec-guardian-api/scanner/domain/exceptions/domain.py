"""
Domain exceptions for the Scanner bounded context.

Domain exceptions represent violations of business rules and
invalid domain operations. They should be raised only from the
domain layer and handled by the application layer.
"""


class DomainError(Exception):
    """
    Base exception for all domain errors.
    """

    pass


class DomainValidationError(DomainError):
    """
    Raised when an entity or value object violates
    one or more domain validation rules.
    """

    pass


class InvalidStateTransitionError(DomainError):
    """
    Raised when an entity attempts an illegal
    state transition.
    """

    pass


class EntityNotFoundError(DomainError):
    """
    Raised when a required domain entity
    cannot be located.
    """

    pass


class DuplicateEntityError(DomainError):
    """
    Raised when attempting to create an entity
    that already exists.
    """

    pass


class BusinessRuleViolationError(DomainError):
    """
    Raised when a business rule is violated.
    """

    pass