# ~/formalities/src/formalities/frameworks/base.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition
)

@dataclass
class ValidationResult:
    """Result of framework validation containing boolean success status and any errors"""
    isvalid: bool
    errors: list[str] = field(default_factory=list)


class Framework(ABC):
    """
    Base class for logical frameworks.
    A framework defines how logical statements ought to be interpreted and validated,
    according to specific philosophical & mathematical principles.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this logical framework."""
        pass

    @abstractmethod
    def validate(self, proposition: Proposition) -> ValidationResult:
        """
        Validate a proposition according to this framework's rules.
        Args:
            proposition: the proposition to validate
        Returns:
            ValidationResult containing success status and any errors
        """
        pass

    @abstractmethod
    def evaluate(self, proposition: Proposition, context: t.Optional[dict[str, bool]]=None) -> bool:
        """
        Evaluate a proposition according to this framework's interpretation.

        Args:
            proposition: The proposition to evaluate
            context: Optional mapping of atomic propositions to truth values

        Returns:
            The truth value according to this framework's rules
        """
        pass

    @abstractmethod
    def iscompatible(self, proposition: Proposition) -> bool:
        """
        Check if a proposition is compatible with this framework.
        Some frameworks may have restrictions on the types of propositions or operators they can handle.
        """
        pass

    def validatecompatibility(self, proposition: Proposition) -> None:
        """
        Validate that a proposition is compatible with this framework.
        Raises:
            ValueError if proposition is not compatible
        """
        if not self.iscompatible(proposition):
            raise ValueError(
                f"""
                Proposition {proposition} is not compatible with {self.name} framework.
                """
            )
