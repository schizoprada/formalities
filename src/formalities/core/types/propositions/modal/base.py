# ~/formalities/src/formalities/core/types/propositions/modal/base.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.core.types.propositions.base import Proposition
from formalities.core.types.propositions.compound import CompoundProposition
from formalities.core.types.operators.modal.base import ModalOperator
from formalities.core.types.operators.modal.registry import ModalRegistry


@dataclass(frozen=True)
class ModalProposition(CompoundProposition):
    """
    A proposition governed by modal operators.

    Modal propositions extend the classical propositional logic with operators that deal with
    necessity, possibility, and temporal relationships. These are evaluated within the context
    of possible worlds (Kripke semantics) or temporal frames.

    Examples:
        □P : "necessarily P"
        ◇P : "possibly P"
        GP : "always P"
        FP : "eventually P"
        P U Q : "P until Q"
    """
    _operator: ModalOperator
    _components: tuple[Proposition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.operator, ModalOperator):
            raise TypeError(
                f"""
                Modal proposition requires modal operator.
                Got: {type(self.operator).__name__}
                """
            )
        self.operator.validatearity(*self.components)

    def evaluate(self, context: t.Optional[t.Dict[str, bool]] = None, *args, **kwargs) -> bool:
        """
        Evaluate the modal proposition.

        Modal propositions require special evaluation context that includes:
        - Current world/time point
        - Accessibility relation
        - World/time point valuation function

        Args:
            context: Must include modal evaluation context

        Raises:
            NotImplementedError: Direct evaluation not supported
                                (must be handled by modal framework)
        """
        raise NotImplementedError("Modal propositions must be evaluated within a modal framework")


    def __str__(self) -> str:
        """String representation of modal proposition."""
        if self.operator.arity == 1:
            return f"{self.operator.symbol}{self.components[0]}"
        return f"({' '.join(str(c) for c in self.components)})"

    def __eq__(self, other: t.Any) -> bool:
        """Equality comparison."""
        if not isinstance(other, ModalProposition):
            return False
        return (self.operator == other.operator and
                self.components == other.components)

    def __hash__(self) -> int:
        """Hash for modal proposition."""
        return hash((self.operator, self.components))


# Factory Functions for common modal propositions
def necessarily(p: Proposition) -> ModalProposition:
    """Create a necessity proposition"""
    return ModalProposition(ModalRegistry.necessity(), (p,))

def possibly(p: Proposition) -> ModalProposition:
    """Create a possibility proposition"""
    return ModalProposition(ModalRegistry.possibility(), (p,))

def always(p: Proposition) -> ModalProposition:
    """Create an always proposition"""
    return ModalProposition(ModalRegistry.always(), (p,))

def eventually(p: Proposition) -> ModalProposition:
    """Create an eventually proposition"""
    return ModalProposition(ModalRegistry.eventually(), (p,))

def until(p: Proposition, q: Proposition) -> ModalProposition:
    """Create an until proposition"""
    return ModalProposition(ModalRegistry.until(), (p, q))
