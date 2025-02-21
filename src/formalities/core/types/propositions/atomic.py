# ~/formalities/src/formalities/core/types/propositions/atomic.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.atomic import Atomic, AtomicRegistry
from formalities.core.types.propositions.base import Proposition

@dataclass(frozen=True, eq=False)
class AtomicProposition(Proposition, Atomic):
    """
    Represents an atomic (indivisible) proposition

    An atomic proposition is the simplest form of proposition that cannot be broken down into simpler logical components.
    It represents a single, specific claim that is either True or False.

    Verbal Examples:
        - '2 is a prime number'
        - 'it is raining'
    Formal Examples:
        >>> p = AtomicProposition("P")  # Create proposition P with no fixed truth value
        >>> p.evaluate({"P": True})      # Evaluate P as True in given context
        True
        >>> q = AtomicProposition("Q", truth_value=False)  # Create Q with fixed False value
        >>> q.evaluate()                 # Q is always False
        False
    """

    symbol: str
    _truthvalue: t.Optional[bool] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'symbol', self.symbol.strip())
        if not self.symbol:
            raise ValueError(f"Proposition symbol cannot be empty")
        AtomicRegistry.register(self)


    def evaluate(self, context: t.Optional[t.Dict[str, bool]]=None) -> bool:
        """
        Evaluate the truth value of this proposition.

        Args:
            context: optional mapping of proposition symbols to truth values
        Returns:
            the truth value of this proposition
        Raises:
            ValueError if no truth value is available (neither fixed nor in context)
        """
        # fixed truth value takes precedence
        if self._truthvalue is not None:
            return self._truthvalue

        if context is not None:
            if self.symbol in context:
                return context[self.symbol]

        raise ValueError(
            f"""
            No truth value available for proposition: {self.symbol}.
            Provide either a fixed _truthvalue or evaluation context
            """
        )

    def __str__(self) -> str:
        """Return the string representation (symbol) of this proposition."""
        return self.symbol

    def __eq__(self, other: t.Any) -> bool:
        """
        Compare this proposition with another for equality.
        Propositions are equal if they have the same symbol and truth value.
        """
        if not isinstance(other, AtomicProposition):
            return False
        return (
            self.symbol == other.symbol and
            self._truthvalue == other._truthvalue
        )

    def __hash__(self) -> int:
        """Generate a hash based on this proposition's symbol and truth value"""
        return hash((self.symbol, self._truthvalue))

    @property
    def logictype(self) -> LogicType:
        """The logical type of this element (is always PROPOSITION)"""
        return LogicType.PROPOSITION
