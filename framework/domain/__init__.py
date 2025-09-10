"""Domain layer for the Gary-Zero framework.

This module implements domain-driven design patterns including:
- Domain entities and value objects
- Domain services
- Domain events
- Repository patterns

This layer contains the core business logic and is independent of
external concerns like persistence or APIs.
"""

from .entities import DomainEntity
from .events import DomainEvent, EventBus
from .services import DomainService
from .value_objects import ValueObject

__all__ = [
    "DomainEntity",
    "DomainEvent", 
    "EventBus",
    "DomainService",
    "ValueObject",
]