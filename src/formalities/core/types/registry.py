# ~/formalities/src/formalities/core/types/registry.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from collections import defaultdict

T = t.TypeVar('T')

class Registry(ABC, t.Generic[T]):
    """Base class for all registries in the framework.

    Handles registration, retrieval, and management of instances.
    Type-safe through generics.
    """

    _instances: dict[str, T] = {}

    @classmethod
    @abstractmethod
    def _validateinstance(cls, instance: T) -> None:
        """Validate an instance before registration.

        Subclasses should implement specific validation logic.

        Raises:
            ValueError: If instance is invalid
            TypeError: If instance is of wrong type
        """
        pass

    @classmethod
    @abstractmethod
    def _getkey(cls, instance: T) -> str:
        """Generate a unique key for the instance.

        Subclasses should implement specific key generation logic.
        """
        pass

    @classmethod
    def register(cls, instance: T) -> T:
        """Register an instance.

        Returns existing instance if an equivalent one exists.

        Args:
            instance: Instance to register

        Returns:
            Registered instance (either existing or new)

        Raises:
            ValueError: If instance fails validation
        """
        cls._validateinstance(instance)
        key = cls._getkey(instance)

        if key in cls._instances:
            return cls._instances[key]

        cls._instances[key] = instance
        return instance

    @classmethod
    def get(cls, key: str) -> t.Optional[T]:
        """Retrieve an instance by its key."""
        return cls._instances.get(key)

    @classmethod
    def clear(cls) -> None:
        """Clear all instances from the registry."""
        cls._instances.clear()

    @classmethod
    def all(cls) -> t.ValuesView[T]:
        """Get all registered instances."""
        return cls._instances.values()

    @classmethod
    def count(cls) -> int:
        """Get count of registered instances."""
        return len(cls._instances)
