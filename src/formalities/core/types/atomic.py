# ~/formalities/src/formalities/core/types/atomic.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from formalities.core.types.registry import Registry
from formalities.core.types.logic import LogicType

class Atomic(ABC):
    """
    Base class for all atomic elements in formal logic.

    Atomic elements are the fundamental building blocks that cannot be broken down further.
    e.g. atomic propositions, predicates, terms, and symbols.
    """

    @abstractmethod
    def __str__(self) -> str:
        """String representation of the atomic element."""
        pass

    @abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        """Equality comparison with another atomic element."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Hash value for the atomic element.

        Required for using atomic elements in sets/dicts and for instance tracking.
        """
        pass

    @property
    @abstractmethod
    def logictype(self) -> LogicType:
        """The logical type of this atomic element."""
        pass

class AtomicRegistry(Registry[Atomic]):
    """Registry for atomic elements."""

    @classmethod
    def _validateinstance(cls, instance: Atomic) -> None:
        if not isinstance(instance, Atomic):
            raise TypeError(f"Instance must be Atomic. Got: {type(instance)}")

    @classmethod
    def _getkey(cls, instance: Atomic) -> str:
        return str(instance)
