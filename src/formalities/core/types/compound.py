# ~/formalities/src/formalities/core/types/compound.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.operators.base import Operator

T = t.TypeVar('T')

class Compound(ABC, t.Generic[T]):
    """
    Base class for all compound (non-atomic) elements in formal logic.

    A compound element is composed of other elements combined through some operator.
    This pattern appears throughout formal logic - in propositions, predicates,
    terms, and other constructs.
    """

    @property
    @abstractmethod
    def operator(self) -> Operator[T]:
        """The operator combining this compound's components."""
        pass

    @property
    @abstractmethod
    def components(self) -> tuple[T, ...]:
        """The components being combined in this compound."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """String representation of this compound element."""
        pass

    @abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        """Equality comparison with another compound element."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Hash value for the compound element."""
        pass

    @property
    @abstractmethod
    def logictype(self) -> LogicType:
        """The logical type of this compound element."""
        pass
