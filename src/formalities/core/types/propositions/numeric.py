# ~/formalities/src/formalities/core/types/propositions/numeric.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.atomic import Atomic, AtomicRegistry
from formalities.core.types.propositions.base import Proposition
from formalities.core.types.propositions.atomic import AtomicProposition

@dataclass(frozen=True, eq=True)
class NumericProposition(AtomicProposition):
    """
    Represents a proposition that encapsulates a numeric value.

    This allows numeric computations to be represented in our logical framework.
    The truth value is determined by the numeric values existence (non-None).

    Examples:
        >>> n = NumericProposition("count", 3)  # Represents "count = 3"
        >>> n.value
        3
        >>> n.evaluate()  # Has a value, therefore True
        True
        >>> n = NumericProposition("empty")  # No value assigned
        >>> n.evaluate()  # No value, therefore False
        False
    """
    value: t.Optional[(int | float)] = None

    def __post_init__(self) -> None:
        return super().__post_init__() # register in atomic registry

    def evaluate(self, context: t.Optional[t.Dict[str, bool]]) -> bool:
        return self.value is not None

    def __eq__(self, other: t.Any) -> bool:
        return all((isinstance(other, NumericProposition), (self.symbol == getattr(other, 'symbol')), (self.value == getattr(other, 'value'))))

    def __hash__(self) -> int:
        return hash((self.symbol, self.value))

    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.symbol}={self.value}"
        return self.symbol

    def __add__(self, other: NumericProposition) -> NumericProposition:
            """Add two numeric propositions"""
            if None in (self.value, other.value):
                raise ValueError("Cannot perform arithmetic on undefined values")
            return NumericProposition(
                f"({self.symbol}+{other.symbol})",
                value=(self.value + other.value)
            )

    def __sub__(self, other: NumericProposition) -> NumericProposition:
        """Subtract two numeric propositions"""
        if None in (self.value, other.value):
            raise ValueError("Cannot perform arithmetic on undefined values")
        return NumericProposition(
            f"({self.symbol}-{other.symbol})",
            value=(self.value - other.value)
        )

    def __mul__(self, other: NumericProposition) -> NumericProposition:
        """Multiply two numeric propositions"""
        if None in (self.value, other.value):
            raise ValueError("Cannot perform arithmetic on undefined values")
        return NumericProposition(
            f"({self.symbol}*{other.symbol})",
            value=(self.value * other.value)
        )

    def __gt__(self, other: NumericProposition) -> bool:
        """Greater than comparison"""
        if None in (self.value, other.value):
            raise ValueError("Cannot compare undefined values")
        return self.value > other.value

    def __lt__(self, other: NumericProposition) -> bool:
        """Less than comparison"""
        if None in (self.value, other.value):
            raise ValueError("Cannot compare undefined values")
        return self.value < other.value

    def __ge__(self, other: NumericProposition) -> bool:
        """Greater than or equal comparison"""
        if None in (self.value, other.value):
            raise ValueError("Cannot compare undefined values")
        return self.value >= other.value

    def __le__(self, other: NumericProposition) -> bool:
        """Less than or equal comparison"""
        if None in (self.value, other.value):
            raise ValueError("Cannot compare undefined values")
        return self.value <= other.value

    @staticmethod
    def FromComputation(symbol: str, computation: t.Callable[[], (int | float)]) -> NumericProposition:
        """
        Create a NumericProposition from a computation function.
        Useful for lazy evaluation of numeric operations.

        Args:
            symbol: name/symbol for this proposition
            computation: function that returns a numeric value

        Returns:
            NumericProposition with computed value
        """
        try:
            return NumericProposition(symbol, value=(computation()))
        except Exception as e:
            raise ValueError(f"Computation failed: {str(e)}")
