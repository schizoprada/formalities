# ~/formalities/src/formalities/core/types/propositions/base.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.registry import Registry
from formalities.core.types.atomic import Atomic, AtomicRegistry

class Proposition(ABC):
    """
    Abstract base class for all propositions.

    A proposition is a statement that is either true or false. <- hint (bool return at evaluation)
    All proposition types must inherit from this base class.
    """

    @abstractmethod
    def evaluate(self, *args, **kwargs) -> bool:
        """Derive an ultimate boolean value from the given proposition."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Return a string representation of the proposition."""

    @abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        """Check equality with another proposition."""
        pass

    def __call__(self, *args, **kwargs):
        """Short-hand for evaluation calling"""
        return self.evaluate(*args, **kwargs)

    @property
    def logictype(self) -> LogicType:
        return LogicType.PROPOSITION
