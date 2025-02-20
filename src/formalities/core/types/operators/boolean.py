# ~/formalities/src/formalities/core/types/operators/boolean.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.core.types.propositions.base import Proposition
from formalities.core.types.operators.base import Operator

class UnaryOperator(Operator[Proposition]):
    """Base class for operators that take one operand."""

    @property
    def arity(self) -> int:
        return 1

class BinaryOperator(Operator[Proposition]):
    """Base class for operators that take two operands."""

    @property
    def arity(self) -> int:
        return 2

class NaryOperator(Operator[Proposition]):
    """Base class for operators that take N operands."""
    def __init__(self, arity: int = 2):
        if arity < 2:
            raise ValueError("N-ary operators must have arity >= 2")
        self._arity = arity

    @property
    def arity(self) -> int:
        return self._arity


class NOT(UnaryOperator):
    """Logical negation operator."""

    @property
    def symbol(self) -> str:
        return "¬"

    def apply(self, *operands: Proposition) -> bool:
        #self.validatearity(*operands) // this is already taken care of in the abstract apply method
        return not operands[0].evaluate()

class AND(BinaryOperator):
    """Logical conjunction operator."""

    @property
    def symbol(self) -> str:
        return "∧"

    def apply(self, *operands: Proposition) -> bool:
        return operands[0].evaluate() and operands[1].evaluate()

class OR(BinaryOperator):
    """Logical disjunction operator."""

    @property
    def symbol(self) -> str:
        return "∨"

    def apply(self, *operands: Proposition) -> bool:
        return operands[0].evaluate() or operands[1].evaluate()

class IMPLIES(BinaryOperator):
    """Logical implication operator."""

    @property
    def symbol(self) -> str:
        return "→"

    def apply(self, *operands: Proposition) -> bool:
        p, q = operands[0].evaluate(), operands[1].evaluate()
        return (not p) or q

class XOR(BinaryOperator):
    """Exclusive disjunction operator."""
    @property
    def symbol(self) -> str:
        return "⊕"

    def apply(self, *operands: Proposition) -> bool:
        p, q = operands[0].evaluate(), operands[1].evaluate()
        return p != q

class NAND(BinaryOperator):
    """Not-and operator."""
    @property
    def symbol(self) -> str:
        return "↑"

    def apply(self, *operands: Proposition) -> bool:
        return not (operands[0].evaluate() and operands[1].evaluate())

class NOR(BinaryOperator):
    """Not-or operator."""
    @property
    def symbol(self) -> str:
        return "↓"

    def apply(self, *operands: Proposition) -> bool:
        return not (operands[0].evaluate() or operands[1].evaluate())

class IFF(BinaryOperator):
    """If and only if (biconditional) operator."""
    @property
    def symbol(self) -> str:
        return "↔"

    def apply(self, *operands: Proposition) -> bool:
        p, q = operands[0].evaluate(), operands[1].evaluate()
        return p == q

# N-ary Operators
class NANDN(NaryOperator):
    """N-ary NAND operator."""
    @property
    def symbol(self) -> str:
        return f"↑{self.arity}"

    def apply(self, *operands: Proposition) -> bool:
        return not all(op.evaluate() for op in operands)

class NORN(NaryOperator):
    """N-ary NOR operator."""
    @property
    def symbol(self) -> str:
        return f"↓{self.arity}"

    def apply(self, *operands: Proposition) -> bool:
        return not any(op.evaluate() for op in operands)

class ANDN(NaryOperator):
    """N-ary AND operator."""
    @property
    def symbol(self) -> str:
        return f"∧{self.arity}"

    def apply(self, *operands: Proposition) -> bool:
        return all(op.evaluate() for op in operands)

class ORN(NaryOperator):
    """N-ary OR operator."""
    @property
    def symbol(self) -> str:
        return f"∨{self.arity}"

    def apply(self, *operands: Proposition) -> bool:
        return any(op.evaluate() for op in operands)

# Aliases
XNOR = IFF  # XNOR is equivalent to IFF
BICOND = IFF  # Biconditional is equivalent to IFF
