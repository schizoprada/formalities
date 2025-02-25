# ~/formalities/src/formalities/core/types/operators/modal/base.py
from __future__ import annotations
from dataclasses import dataclass
from formalities.core.types.operators.base import Operator
from formalities.core.types.propositions.base import Proposition

class ModalOperator(Operator[Proposition]):
    """Base class for modal operators"""

    def apply(self, *operands: Proposition) -> bool:
        """
        Apply this modal operator to propositions.
        Note:
            Actual evaluation must be done in context of a modal framework,
            with possible world semantics.
        """
        self.validatearity(*operands)
        raise NotImplementedError("Modal operators must be evaluated within a modal framework")


class Necessity(ModalOperator):
    """
    Necessity operator (□).
    □P means "P is necessarily true" or "P is true in all accessible worlds"
    """
    @property
    def symbol(self) -> str:
        return "□"

    @property
    def arity(self) -> int:
        return 1


class Possibility(ModalOperator):
    """
    Possibility operator (◇).
    ◇P means "P is possibly true" or "P is true in at least one accessible world"
    """
    @property
    def symbol(self) -> str:
        return "◇"

    @property
    def arity(self) -> int:
        return 1


class Always(ModalOperator):
    """
    Always operator (G).
    GP means "P is true at all future points"
    """
    @property
    def symbol(self) -> str:
        return "G"

    @property
    def arity(self) -> int:
        return 1

class Eventually(ModalOperator):
    """
    Eventually operator (F).
    FP means "P is true at some future point"
    """
    @property
    def symbol(self) -> str:
        return "F"

    @property
    def arity(self) -> int:
        return 1

class Until(ModalOperator):
    """
    Until operator (U).
    P U Q means "P remains true until Q becomes true"
    """
    @property
    def symbol(self) -> str:
        return "U"

    @property
    def arity(self) -> int:
        return 2  # Takes two arguments: P and Q
